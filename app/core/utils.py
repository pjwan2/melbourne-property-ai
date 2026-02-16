import re

def parse_price(price_str):
    """
    Convert "$750,000 - $820,000" or "Over $1M" into a clean integer.
    """
    if not price_str or "Auction" in price_str:
        return None
    
    # Extract all numbers
    numbers = re.findall(r'\d+', price_str.replace(',', ''))
    
    if not numbers:
        return None
        
    # If it's a range, take the average; if it's one number, take it.
    ints = [int(n) for n in numbers]
    if len(ints) >= 2:
        return sum(ints[:2]) // 2
    return ints[0]