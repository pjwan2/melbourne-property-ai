from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class Property(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    suburb: str
    address: str
    price_text: Optional[str] = None
    price_value: Optional[int] = None
    

    listing_url: str = Field(index=True) # 
    land_size: Optional[int] = None      # 
    internal_area: Optional[int] = None  # 
    # --------------------

    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    parking_spaces: Optional[int] = None
    property_type: Optional[str] = None
    
    scraped_at: datetime = Field(default_factory=datetime.utcnow)