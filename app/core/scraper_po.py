import os
import sys
import time
import random
import logging
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

sys.path.append(os.getcwd())
from app.services.property_service import PropertyService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 🎯 The Golden List: 使用 Slug 确保 URL 100% 正确
TARGET_DATA = [
    {"slug": "patterson-lakes-vic-3197", "name": "Patterson Lakes"},
    {"slug": "carrum-vic-3197", "name": "Carrum"},
    {"slug": "aspendale-gardens-vic-3195", "name": "Aspendale Gardens"},
    {"slug": "aspendale-vic-3195", "name": "Aspendale"},
    {"slug": "edithvale-vic-3196", "name": "Edithvale"},
    {"slug": "chelsea-vic-3196", "name": "Chelsea"},
    {"slug": "bonbeach-vic-3196", "name": "Bonbeach"},
    {"slug": "mordialloc-vic-3195", "name": "Mordialloc"},
    {"slug": "parkdale-vic-3195", "name": "Parkdale"},
    {"slug": "mentone-vic-3194", "name": "Mentone"},
    {"slug": "frankston-vic-3199", "name": "Frankston"},
    {"slug": "frankston-south-vic-3199", "name": "Frankston South"},
    {"slug": "seaford-vic-3198", "name": "Seaford"},
    {"slug": "mornington-vic-3931", "name": "Mornington"},
    {"slug": "mount-martha-vic-3934", "name": "Mount Martha"},
    {"slug": "boronia-vic-3155", "name": "Boronia"},
    {"slug": "wantirna-vic-3152", "name": "Wantirna"},
    {"slug": "wantirna-south-vic-3152", "name": "Wantirna South"},
    {"slug": "ringwood-vic-3134", "name": "Ringwood"},
    {"slug": "rowville-vic-3178", "name": "Rowville"},
    {"slug": "cranbourne-vic-3977", "name": "Cranbourne"},
    {"slug": "pakenham-vic-3810", "name": "Pakenham"},
    {"slug": "berwick-vic-3806", "name": "Berwick"}
]

class RealEstateScraper:
    def __init__(self):
        self.service = PropertyService()
        self.user_data_dir = os.path.join(os.getcwd(), "browser_session")

    def parse_page(self, html, suburb):
        soup = BeautifulSoup(html, "lxml")
        listings = []
        
        # 1. 查找卡片
        potential_prices = soup.find_all(lambda tag: tag.name in ['div', 'span', 'p'] and 
                                       (tag.get('data-testid') == 'listing-card-price' or 
                                        ('$' in tag.get_text() and len(tag.get_text()) < 30)))
        
        cards = []
        for price_tag in potential_prices:
            card = price_tag.find_parent('li') or \
                   price_tag.find_parent('div', attrs={"data-testid": re.compile(r"listing-card")})
            if card: cards.append(card)
        
        cards = list(set(cards)) # 去重

        logger.info(f"   🧩 Parser found {len(cards)} potential cards.")

        for card in cards:
            try:
                # --- ✅ 修复点 1: 正确提取 URL ---
                url = None
                # 先向下找
                link_tag = card.find("a", href=True)
                # 如果没找到，再向上找 (处理包裹情况)
                if not link_tag:
                    link_tag = card.find_parent("a", href=True)
                
                if link_tag:
                    url = link_tag['href']
                    if not url.startswith("http"):
                        url = "https://www.domain.com.au" + url
                
               

                # --- ✅ 修复点 2: 正确提取 Land Size ---
                land_size = 0
                features = card.find_all(attrs={"data-testid": "property-features-text-container"})
                for f in features:
                    txt = f.get_text(strip=True)
                    if 'm²' in txt or 'sqm' in txt:
                        match = re.search(r'([\d,]+)', txt)
                        if match:
                            land_size = int(match.group(1).replace(',', ''))

                # --- 3. 提取地址 ---
                addr_tag = card.find(attrs={"data-testid": "address"}) or card.find('h2')
                if not addr_tag: continue
                address = addr_tag.get_text(strip=True)

                # --- 4. 提取价格 ---
                price_tag = card.find(attrs={"data-testid": "listing-card-price"})
                price = price_tag.get_text(strip=True) if price_tag else "Contact Agent"
                if not price_tag:
                    pt = card.find(string=re.compile(r'\$'))
                    if pt: price = pt.strip()

                # --- 5. 提取卧室 ---
                beds = 0
                if features:
                    text = features[0].get_text(strip=True)
                    match = re.search(r'(\d+)', text)
                    if match: beds = int(match.group(1))

                listings.append({
                    "suburb": suburb,
                    "address": address,
                    "price_text": price,
                    "bedrooms": beds,
                    "property_type": "House",
                    "listing_url": url,       # 现在 url 已经被定义了
                    "land_size": land_size    # land_size 也被定义了
                })

            except Exception as e:
                # logger.error(f"Error parsing card: {e}")
                continue
        
        return listings

    def run(self):
        logger.info(f"🚀 Starting Scraper for {len(TARGET_DATA)} suburbs...")
        
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.pages[0]

            for item in TARGET_DATA:
                slug = item['slug']
                name = item['name']
                url = f"https://www.domain.com.au/sale/{slug}/"
                
                logger.info(f"🔎 Crawling {name.upper()}...")
                
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    
                    try:
                        logger.info("   ⏳ Waiting for listings to render...")
                        page.wait_for_selector('[data-testid="listing-card-price"]', timeout=15000)
                    except:
                        logger.warning("   ⚠️ Wait timeout. Page might be empty.")

                    page.mouse.wheel(0, 3000)
                    time.sleep(2)
                    
                    listings = self.parse_page(page.content(), name)
                    
                    if listings:
                        saved = self.service.save_properties(listings)
                        logger.info(f"📊 {name.upper()}: Extracted {len(listings)}, Saved {saved}")
                    else:
                        with open(f"debug_failed_{name}.html", "w", encoding="utf-8") as f:
                            f.write(page.content())
                        logger.warning(f"⚠️ Zero listings found for {name}.")

                except Exception as e:
                    logger.error(f"❌ Error: {e}")
                
                time.sleep(random.uniform(15, 30))

            context.close()

if __name__ == "__main__":
    scraper = RealEstateScraper()
    scraper.run()