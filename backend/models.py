from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Dispensary(Base):
    __tablename__ = 'dispensaries'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    phone = Column(String)
    website = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    products = relationship("Product", back_populates="dispensary")

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    dispensary_id = Column(Integer, ForeignKey('dispensaries.id'), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String)  # flower, edible, concentrate, etc.
    strain = Column(String)
    price = Column(Float, nullable=False)
    unit = Column(String, default='g')  # g, oz, each, etc.
    description = Column(String)
    in_stock = Column(Integer, default=1)  # 1 for in stock, 0 for out
    thc_content = Column(Float)
    cbd_content = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dispensary = relationship("Dispensary", back_populates="products")