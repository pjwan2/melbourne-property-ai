import logging
import time
import random
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class RealEstateScraper:
    """
    Service responsible for interacting with Domain.com.au.
    Updated with robust selectors.
    """
    
    def __init__(self):
        self.base_url = "https://www.domain.com.au"

    def scrape_suburb(self, suburb: str, state: str = "vic", postcode: str = "3155") -> list:
        logger.info(f"🕸️ Domain Scraper: Launching browser for {suburb}, {state}, {postcode}...")
        
        results = []

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
            )
            
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            search_query = f"{suburb}-{state}-{postcode}".lower().replace(" ", "-")
            target_url = f"{self.base_url}/sale/{search_query}/"
            
            logger.info(f"➡️ Navigating to: {target_url}")
            
            try:
                page.goto(target_url, timeout=60000)
                time.sleep(random.uniform(3, 5))

                # Wait for the results list specifically
                try:
                    page.wait_for_selector('ul[data-testid="results"]', timeout=15000)
                except:
                    logger.warning("⚠️ Main list not found. Trying to parse anyway...")

                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

                html_content = page.content()
                results = self._parse_domain_html(html_content, suburb)
                
            except Exception as e:
                logger.error(f"❌ Scraping failed: {e}")
                page.screenshot(path=f"error_{suburb}_domain.png")
            finally:
                browser.close()
                
        return results

    def _parse_domain_html(self, html: str, suburb: str) -> list:
        """
        Robust parser for Domain.com.au
        """
        soup = BeautifulSoup(html, "lxml")
        data = []

        # Strategy 1: Find the main results list container first
        results_container = soup.find('ul', attrs={"data-testid": "results"})
        
        if results_container:
            # Get all list items inside the results
            cards = results_container.find_all('li')
        else:
            # Fallback: Find any list items that look like cards
            logger.warning("⚠️ 'results' container not found, using fallback selector.")
            cards = soup.select('li.css-1q2v64e') # Common Domain class, might change
            if not cards:
                cards = soup.select('li') # Get ALL list items (messy but works)

        logger.info(f"🔍 Found {len(cards)} list items to check.")

        for card in cards:
            try:
                # Skip cards that are just separators or ads (usually empty text)
                if not card.text.strip():
                    continue

                # --- 1. Address Extraction (Robust) ---
                # Look for h2 (usually address) or any span with the suburb name
                address_tag = card.find('h2')
                if not address_tag:
                    address_tag = card.find('span', attrs={"itemprop": "streetAddress"})
                
                # If still no address, try finding the link text
                if not address_tag:
                    link = card.find('a', href=True)
                    if link and suburb.lower() in link.text.lower():
                        address_tag = link
                
                if not address_tag:
                    continue # Valid cards MUST have an address

                address = address_tag.text.strip()

                # --- 2. Price Extraction ---
                price_text = "Contact Agent"
                # Price is usually in a paragraph or specific testid
                price_tag = card.find('p', attrs={"data-testid": "listing-card-price"})
                if price_tag:
                    price_text = price_tag.text.strip()

                # --- 3. Image ---
                image_url = None
                img = card.find('img')
                if img:
                    image_url = img.get('src')

                # --- 4. Features ---
                bedrooms = self._extract_feature_text(card, "Beds")
                bathrooms = self._extract_feature_text(card, "Baths")
                parking = self._extract_feature_text(card, "Parking")

                item = {
                    "suburb": suburb,           
                    "address": address,         
                    "price_text": price_text,   
                    "image_url": image_url,
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms,
                    "parking_spaces": parking,
                    "property_type": "House", # Simplified
                    "source_url": "domain.com.au"
                }
                
                # Check if it's a real property (address usually has numbers)
                if len(address) > 5:
                    data.append(item)

            except Exception as e:
                # Ignore parse errors for individual cards
                continue
                
        logger.info(f"✅ Successfully parsed {len(data)} properties from Domain.")
        return data

    def _extract_feature_text(self, card, feature_keyword):
        """
        Finds text like '3 Beds' and returns 3.
        """
        try:
            # Search all spans for the keyword (e.g., "Beds")
            all_text = card.get_text(" ")
            # Regex to find "3 Beds" or "3Beds"
            match = re.search(r'(\d+)\s*' + feature_keyword, all_text, re.IGNORECASE)
            if match:
                return int(match.group(1))
            
            # Fallback: specific spans (Domain often uses icons with text)
            spans = card.find_all('span')
            for span in spans:
                if feature_keyword in span.text:
                    match = re.search(r'\d+', span.text)
                    if match: return int(match.group())
        except:
            return None
        return None