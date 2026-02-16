import sys
import os
import time
import random
import re
import logging
from sqlmodel import Session, select
from playwright.sync_api import sync_playwright

# 路径修复
sys.path.append(os.getcwd())
from app.core.database import engine
from app.models.property import Property

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class DetailEnricher:
    def __init__(self):
        self.user_data_dir = os.path.join(os.getcwd(), "browser_session")

    def extract_areas(self, html):

        land = 0
        internal = 0
        

        
        # Land Size Pattern
        land_patterns = [
            r'Land size:?\s*([\d,]+)\s*(?:sqm|m²|m2)',
            r'([\d,]+)\s*(?:sqm|m²|m2)\s*land',
            r'Land area\s*([\d,]+)\s*(?:sqm|m²|m2)'
        ]
        
        # Internal Area Pattern
        internal_patterns = [
            r'Internal area:?\s*([\d,]+)\s*(?:sqm|m²|m2)',
            r'Floor area:?\s*([\d,]+)\s*(?:sqm|m²|m2)',
            r'([\d,]+)\s*(?:sqm|m²|m2)\s*internal'
        ]

        # 辅助函数
        def search_patterns(patterns, text):
            for pat in patterns:
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    try:
                        return int(match.group(1).replace(',', ''))
                    except: continue
            return 0

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        text_content = soup.get_text(" ", strip=True) 
        
        land = search_patterns(land_patterns, text_content)
        internal = search_patterns(internal_patterns, text_content)
        

        return land, internal

    def run(self):
        with Session(engine) as session:

            statement = select(Property).where(
                (Property.land_size == None) | (Property.land_size == 0)
            )
            properties = session.exec(statement).all()
            
            logger.info(f"🎯 Found {len(properties)} properties needing enrichment.")
            
            if not properties:
                return

     
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=False, 
                    args=["--disable-blink-features=AutomationControlled"]
                )
                page = browser.pages[0]

        
                for i, prop in enumerate(properties):
                    if not prop.listing_url: continue
                    
                    logger.info(f"[{i+1}/{len(properties)}] Visiting: {prop.address}...")
                    
                    try:
                        page.goto(prop.listing_url, wait_until="domcontentloaded", timeout=30000)
                        
         
                        page.mouse.wheel(0, 1000)
                        time.sleep(random.uniform(1.5, 3))
                        
                        html = page.content()
                        land, internal = self.extract_areas(html)
                        
                      
                        if land > 0 or internal > 0:
                            prop.land_size = land
                            prop.internal_area = internal
                            session.add(prop)
                            session.commit() 
                            logger.info(f"   ✅ Updated! Land: {land}m², Internal: {internal}m²")
                        else:
                            logger.warning("   ⚠️ No size data found on page.")
                            
                    except Exception as e:
                        logger.error(f"   ❌ Failed: {e}")
                    
              
                    time.sleep(random.uniform(3, 6))

                browser.close()

if __name__ == "__main__":
    enricher = DetailEnricher()
    enricher.run()