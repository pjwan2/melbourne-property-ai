from sqlmodel import Session, select
from app.core.database import engine
from app.models.property import Property
import logging

logger = logging.getLogger(__name__)

class PropertyService:
    def save_properties(self, listings: list[dict]) -> int:

        saved_count = 0
        

        with Session(engine) as session:
            for item in listings:
                try:
                   
                    statement = select(Property).where(
                        (Property.address == item["address"]) & 
                        (Property.suburb == item["suburb"])
                    )
                    existing_prop = session.exec(statement).first()

                    if existing_prop:
                   
                        existing_prop.price_text = item["price_text"]
                   
                        if item.get("listing_url"):
                            existing_prop.listing_url = item["listing_url"]
                        if item.get("land_size", 0) > 0:
                            existing_prop.land_size = item["land_size"]
                            
                        session.add(existing_prop)
                    else:
                     
                        new_prop = Property(
                            suburb=item["suburb"],
                            address=item["address"],
                            price_text=item["price_text"],
                            price_value=None, 
                            bedrooms=item["bedrooms"],
                            property_type=item["property_type"],
                            listing_url=item.get("listing_url"), 
                            land_size=item.get("land_size", 0),
                            internal_area=0
                        )
                        session.add(new_prop)
                    
     
                    session.commit()
                    saved_count += 1

                except Exception as e:
               
                    logger.error(f"❌ Error saving {item.get('address')}: {e}")
                    session.rollback()
                    continue #

        return saved_count