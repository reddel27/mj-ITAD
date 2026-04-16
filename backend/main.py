from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db
from models import Dispensary, Product
import googlemaps
import os
import logging
from sqlalchemy import and_
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
from scraper import scrape_products_from_url

load_dotenv()
logger = logging.getLogger(__name__)
ENABLE_MOCK_DISPENSARIES = os.getenv("ENABLE_MOCK_DISPENSARIES", "false").lower() in {"1", "true", "yes"}

app = FastAPI(title="MJ-ITAD API", description="Marijuana dispensary price comparison API")


class DispensaryResponse(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class DispensaryListResponse(BaseModel):
    dispensaries: List[DispensaryResponse]


class ProductResponse(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    price: float
    unit: Optional[str] = None
    in_stock: int


class ProductListResponse(BaseModel):
    products: List[ProductResponse]


class MenuIngestRequest(BaseModel):
    dispensary_id: int
    menu_url: str


class MenuIngestResponse(BaseModel):
    ingested_count: int
    skipped_count: int


allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
    ).split(",")
    if origin.strip()
]

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps_client = None


def get_gmaps_client():
    global gmaps_client
    if gmaps_client is not None:
        return gmaps_client

    if not GOOGLE_MAPS_API_KEY:
        raise HTTPException(status_code=503, detail="Google Maps API key is not configured")

    try:
        gmaps_client = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    except Exception as exc:
        logger.exception("Failed to initialize Google Maps client: %s", exc)
        raise HTTPException(status_code=503, detail="Google Maps client initialization failed")

    return gmaps_client


def get_mock_places():
    return [
        {
            "name": "Green Valley Dispensary",
            "vicinity": "123 Main St, San Francisco, CA",
            "geometry": {"location": {"lat": 37.7749, "lng": -122.4194}},
        },
        {
            "name": "Herbal Remedies",
            "vicinity": "456 Oak Ave, San Francisco, CA",
            "geometry": {"location": {"lat": 37.7849, "lng": -122.4294}},
        },
    ]

@app.get("/")
async def root():
    return {"message": "MJ-ITAD API is running"}

@app.get("/dispensaries", response_model=DispensaryListResponse)
async def get_dispensaries(lat: float, lng: float, radius: int = 5000, db: Session = Depends(get_db)):
    """
    Get dispensaries near a location
    """
    try:
        gmaps = get_gmaps_client()
        places_result = gmaps.places_nearby(
            location=(lat, lng),
            radius=radius,
            keyword="marijuana dispensary"
        )
        places = places_result.get("results", [])
    except HTTPException as exc:
        if ENABLE_MOCK_DISPENSARIES:
            logger.warning("Google Maps unavailable, using mock dispensaries: %s", exc.detail)
            places = get_mock_places()
        else:
            raise
    except Exception as exc:
        logger.exception("Google Maps API error: %s", exc)
        if ENABLE_MOCK_DISPENSARIES:
            logger.warning("Using mock dispensaries due to upstream API error")
            places = get_mock_places()
        else:
            raise HTTPException(status_code=502, detail="Failed to fetch dispensaries from Google Maps")

    dispensaries = []
    for place in places:
        name = place.get('name')
        if not name:
            continue

        place_id = place.get('place_id')
        address = place.get('vicinity')
        latitude = place['geometry']['location']['lat']
        longitude = place['geometry']['location']['lng']

        existing = None
        if place_id:
            existing = db.query(Dispensary).filter(Dispensary.place_id == place_id).first()

        if not existing:
            existing = db.query(Dispensary).filter(
                and_(
                    Dispensary.name == name,
                    Dispensary.address == address,
                )
            ).first()

        if not existing:
            dispensary = Dispensary(
                place_id=place_id,
                name=name,
                address=address,
                latitude=latitude,
                longitude=longitude
            )
            db.add(dispensary)
            db.commit()
            db.refresh(dispensary)
        else:
            # Backfill missing place_id and location details for older rows.
            if place_id and not existing.place_id:
                existing.place_id = place_id
            existing.address = address or existing.address
            existing.latitude = latitude
            existing.longitude = longitude
            db.commit()
            db.refresh(existing)
            dispensary = existing

        dispensaries.append({
            "id": dispensary.id,
            "name": dispensary.name,
            "address": dispensary.address,
            "latitude": dispensary.latitude,
            "longitude": dispensary.longitude
        })

    return {"dispensaries": dispensaries}

@app.get("/products/{dispensary_id}", response_model=ProductListResponse)
async def get_products(dispensary_id: int, db: Session = Depends(get_db)):
    """
    Get products from a specific dispensary
    """
    dispensary = db.query(Dispensary).filter(Dispensary.id == dispensary_id).first()
    if not dispensary:
        return {"products": []}

    products = db.query(Product).filter(Product.dispensary_id == dispensary.id).all()
    return {"products": [
        {
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "price": product.price,
            "unit": product.unit,
            "in_stock": product.in_stock
        } for product in products
    ]}


@app.post("/ingest/menu", response_model=MenuIngestResponse)
async def ingest_menu(payload: MenuIngestRequest, db: Session = Depends(get_db)):
    """
    Scrape and ingest menu products from a dispensary page URL.
    """
    dispensary = db.query(Dispensary).filter(Dispensary.id == payload.dispensary_id).first()
    if not dispensary:
        raise HTTPException(status_code=404, detail="Dispensary not found")

    scraped_products = scrape_products_from_url(payload.menu_url)
    if not scraped_products:
        return {"ingested_count": 0, "skipped_count": 0}

    ingested_count = 0
    skipped_count = 0
    for item in scraped_products:
        existing = db.query(Product).filter(
            Product.dispensary_id == payload.dispensary_id,
            Product.name == item["name"],
            Product.price == item["price"],
            Product.unit == item.get("unit"),
        ).first()

        if existing:
            skipped_count += 1
            continue

        product = Product(
            dispensary_id=payload.dispensary_id,
            name=item["name"],
            category=item.get("category"),
            strain=item.get("strain"),
            price=item["price"],
            unit=item.get("unit") or "each",
            description=item.get("description"),
            in_stock=1,
            thc_content=item.get("thc_content"),
            cbd_content=item.get("cbd_content"),
        )
        db.add(product)
        ingested_count += 1

    db.commit()
    return {"ingested_count": ingested_count, "skipped_count": skipped_count}