# check_data.py
import logging
import sys
import os
from sqlmodel import Session, select
from app.core.database import engine
from app.models.property import Property

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure Python finds the app module
sys.path.append(os.getcwd())

def show_me_the_money():
    print("\n🔮 Querying AWS Database for saved properties...\n")
    
    try:
        with Session(engine) as session:
            # Get the top 10 most recently added properties
            statement = select(Property).order_by(Property.id.desc()).limit(10)
            results = session.exec(statement).all()
            
            if not results:
                print("📭 The database is empty.")
                return

            print(f"✅ Found {len(results)} properties. Here are the latest ones:\n")
            print(f"{'ID':<5} | {'Suburb':<10} | {'Price':<20} | {'Address'}")
            print("-" * 80)
            
            for prop in results:
                # Handle None values gracefully
                p_text = prop.price_text if prop.price_text else "N/A"
                addr = prop.address if prop.address else "Unknown"
                
                print(f"{prop.id:<5} | {prop.suburb:<10} | {p_text[:20]:<20} | {addr}")

            print("\n🎉 It works! Your data is safe in the cloud.")

    except Exception as e:
        print(f"❌ Error reading database: {e}")

if __name__ == "__main__":
    show_me_the_money()