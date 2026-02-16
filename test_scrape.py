import logging
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure Python can find the app module
sys.path.append(os.getcwd())

from app.services.scraper_service import RealEstateScraper
from app.services.property_service import PropertyService

def manual_test():
    suburb = "Boronia"
    # IMPORTANT: Domain requires the postcode
    postcode = "3155" 
    
    print(f"\n🕷️ TEST START: Target -> {suburb} ({postcode})")

    # Step 1: Scrape
    try:
        print("   -> Launching Scraper...")
        scraper = RealEstateScraper()
        # Pass the postcode here
        data = scraper.scrape_suburb(suburb, state="vic", postcode=postcode)
        
        print(f"   -> Scraper finished. Found {len(data)} items.")
    except Exception as e:
        print(f"❌ SCRAPER ERROR: {e}")
        return

    if not data:
        print("⚠️ No data found. Stopping.")
        return

    # Step 2: Save to AWS
    try:
        print("   -> Saving to AWS Database...")
        service = PropertyService()
        count = service.save_properties(data)
        print(f"🎉 FINAL SUCCESS! Saved {count} properties to AWS!")
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")

if __name__ == "__main__":
    manual_test()