import sys
import os
import re
from statistics import median
from sqlmodel import Session, select
from app.core.database import engine
from app.models.property import Property

# Fix path to ensure app module is found
sys.path.append(os.getcwd())

def parse_price_midpoint(price_str):
    """
    Parses price string and returns the midpoint value.
    Example: "$900k-990k" -> 945000
    """
    if not price_str: return None
    # Normalize string: lowercase, remove special chars
    clean_str = price_str.lower().replace(',', '').replace('$', '').replace(' ', '')
    
    # Exclude non-sale items (Auctions, Contact Agent, etc.)
    if any(x in clean_str for x in ['contact', 'auction', 'enquir']): return None
    
    # Extract all numbers using regex
    numbers = re.findall(r'\d+\.?\d*', clean_str)
    try:
        val = float(numbers[0])
        if 'm' in clean_str and val < 100:  # 
            return int(val * 1_000_000)
        
        ints = [float(n) for n in numbers]
        # Filter out years (2025) or postcodes (3195) based on reasonable price range
        ints = [i for i in ints if i > 300_000 and i < 10_000_000] 
        
        if not ints: return None
        
        # Calculate average if a range is provided
        if len(ints) >= 2:
            return int(sum(ints[:2]) / 2) 
        
        return int(ints[0])
    except:
        return None

def generate_report():
    print("\n💎 MELBOURNE LAND VALUE REPORT (PRICE PER SQM)\n")
    print(f"{'SUBURB':<20} | {'ADDRESS':<35} | {'PRICE':<10} | {'LAND':<8} | {'$/SQM':<8} | {'RATING'}")
    print("-" * 110)
    
    with Session(engine) as session:
        # Query only properties with valid land size > 0
        props = session.exec(select(Property).where(Property.land_size > 0)).all()
        
        # Target Suburbs for Analysis
        target_suburbs = ["BERWICK", "ASPENDALE", "ASPENDALE-GARDENS", "PATTERSON-LAKES", "FRANKSTON", "BORONIA"]
        
        data = []
        for p in props:
            price = parse_price_midpoint(p.price_text)
            
            # Filter: Ensure price exists and land size is realistic (>100 sqm)
            if price and p.land_size > 100: 
                psm = price / p.land_size # Calculate Price per Square Meter
                data.append({
                    "suburb": p.suburb.upper(),
                    "address": p.address,
                    "price": price,
                    "land": p.land_size,
                    "psm": int(psm),
                    "url": p.listing_url
                })
        
        # Sort by Price per SQM (Low to High) to find best value
        data.sort(key=lambda x: x['psm'])
        
        for item in data:
            if item['suburb'] not in target_suburbs: continue
            
            # Simple Valuation Algorithm
            rating = "FAIR"
            if item['psm'] < 1000: rating = "🔥 STEAL"  # Extremely Cheap
            elif item['psm'] < 1500: rating = "✅ GOOD"   # Good Value
            elif item['psm'] > 3000: rating = "⚠️ PRICEY" # Expensive
            
            # Formatting Output
            price_display = f"${item['price']/1000:,.0f}k"
            land_display = f"{item['land']}m²"
            psm_display = f"${item['psm']:,}"
            
            print(f"{item['suburb']:<20} | {item['address'][:35]:<35} | {price_display:<10} | {land_display:<8} | {psm_display:<8} | {rating}")

    print("\n💡 LEGEND: 'STEAL' < $1,000/sqm | 'GOOD' < $1,500/sqm")

if __name__ == "__main__":
    generate_report()