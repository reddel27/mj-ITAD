from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db
from models import Dispensary, Product
import googlemaps
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="MJ-ITAD API", description="Marijuana dispensary price comparison API")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))

@app.get("/")
async def root():
    return {"message": "MJ-ITAD API is running"}

@app.get("/dispensaries")
async def get_dispensaries(lat: float, lng: float, radius: int = 5000, db: Session = Depends(get_db)):
    """
    Get dispensaries near a location
    """
    try:
        places_result = gmaps.places_nearby(
            location=(lat, lng),
            radius=radius,
            keyword="marijuana dispensary"
        )
        places = places_result.get("results", [])
    except Exception as exc:
        # Fallback to mock data if the key or API call fails
        print(f"Google Maps API error: {exc}")
        places = [
            {
                "name": "Green Valley Dispensary",
                "vicinity": "123 Main St, San Francisco, CA",
                "geometry": {"location": {"lat": 37.7749, "lng": -122.4194}}
            },
            {
                "name": "Herbal Remedies",
                "vicinity": "456 Oak Ave, San Francisco, CA",
                "geometry": {"location": {"lat": 37.7849, "lng": -122.4294}}
            }
        ]

    dispensaries = []
    for place in places:
        name = place.get('name')
        if not name:
            continue

        existing = db.query(Dispensary).filter(Dispensary.name == name).first()
        if not existing:
            dispensary = Dispensary(
                name=name,
                address=place.get('vicinity'),
                latitude=place['geometry']['location']['lat'],
                longitude=place['geometry']['location']['lng']
            )
            db.add(dispensary)
            db.commit()
            db.refresh(dispensary)
        else:
            dispensary = existing

        dispensaries.append({
            "id": dispensary.id,
            "name": dispensary.name,
            "address": dispensary.address,
            "latitude": dispensary.latitude,
            "longitude": dispensary.longitude
        })

    return {"dispensaries": dispensaries}

def ensure_sample_products(dispensary: Dispensary, db: Session):
    products = db.query(Product).filter(Product.dispensary_id == dispensary.id).all()
    if products:
        return products

    sample_products = [
        {
            "name": "Indica Breeze",
            "category": "Flower",
            "strain": "Blue Dream",
            "price": 35.0,
            "unit": "g",
            "description": "Smooth indica with notes of berries and pine.",
            "in_stock": 1,
            "thc_content": 22.5,
            "cbd_content": 0.3,
        },
        {
            "name": "CBD Gummies",
            "category": "Edible",
            "strain": "Hybrid",
            "price": 25.0,
            "unit": "pack",
            "description": "10-count gummy pack for gentle relaxation.",
            "in_stock": 1,
            "thc_content": 0.0,
            "cbd_content": 10.0,
        },
        {
            "name": "Live Resin Cartridge",
            "category": "Concentrate",
            "strain": "Sour Diesel",
            "price": 45.0,
            "unit": "each",
            "description": "High-potency vape cartridge for fast effects.",
            "in_stock": 1,
            "thc_content": 78.0,
            "cbd_content": 0.2,
        },
    ]

    created = []
    for item in sample_products:
        product = Product(
            dispensary_id=dispensary.id,
            name=item["name"],
            category=item["category"],
            strain=item["strain"],
            price=item["price"],
            unit=item["unit"],
            description=item["description"],
            in_stock=item["in_stock"],
            thc_content=item["thc_content"],
            cbd_content=item["cbd_content"],
        )
        db.add(product)
        created.append(product)

    db.commit()
    return created

@app.get("/products/{dispensary_id}")
async def get_products(dispensary_id: int, db: Session = Depends(get_db)):
    """
    Get products from a specific dispensary
    """
    dispensary = db.query(Dispensary).filter(Dispensary.id == dispensary_id).first()
    if not dispensary:
        return {"products": []}

    products = ensure_sample_products(dispensary, db)
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