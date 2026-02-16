import streamlit as st
import pandas as pd
from sqlmodel import Session, select
from app.core.database import engine
from app.models.property import Property
import re

# --- 复用你的核心清洗逻辑 ---
def parse_price(price_str):
    if not price_str: return None
    clean_str = price_str.lower().strip().replace(',', '')
    if any(x in clean_str for x in ['contact', 'auction', 'enquir', 'review']): return None
    if ('sqm' in clean_str or 'm2' in clean_str) and '$' not in clean_str: return None
    numbers = re.findall(r'\d+\.?\d*', clean_str)
    if not numbers: return None
    try:
        if 'm' in clean_str and ('$' in clean_str or 'mill' in clean_str):
            val = int(float(numbers[0]) * 1_000_000)
        else:
            ints = [float(n) for n in numbers]
            ints = [i for i in ints if i > 200_000 and i < 20_000_000]
            if not ints: return None
            val = int(sum(ints[:2]) / 2) if len(ints) >= 2 else int(ints[0])
        return val if val < 10_000_000 else None
    except: return None

def get_asset_tier(addr, suburb, beds):
    addr = addr.upper()
    suburb = suburb.upper()
    beds = beds if beds else 0
    is_strata = False
    
    # 包含修正后的 "10B" 逻辑
    if re.match(r'^[A-Z0-9]+[/]', addr) or re.match(r'^\d+[A-Z]\s', addr): 
        is_strata = True
    elif any(x in addr for x in ['UNIT', 'APT', 'LOT', 'VILLA', 'SUITE']):
        is_strata = True
    
    if is_strata and (suburb in ['ST-KILDA', 'PORT-MELBOURNE', 'FRANKSTON'] or beds == 1):
        return "Tier 4: Apartment"
    if is_strata and beds == 2: return "Tier 3: Villa Unit"
    if is_strata and beds >= 3: return "Tier 2: Townhouse"
    if not is_strata: return "Tier 1: House"
    return "Unknown"

# --- Streamlit 页面 ---
st.set_page_config(page_title="Melbourne Property AI", layout="wide")

st.title("🏡 Melbourne Coastal Market AI Analyzer")
st.markdown("### Real-time Undervalued Asset Detection")

# 1. 加载数据
with Session(engine) as session:
    props = session.exec(select(Property)).all()
    
    data = []
    for p in props:
        # Strict Suburb Matching
        if p.suburb.replace('-', ' ').upper() not in p.address.upper():
            if "PATTERSON" not in p.suburb.upper(): continue

        price = parse_price(p.price_text)
        if price:
            tier = get_asset_tier(p.address, p.suburb, p.bedrooms)
            data.append({
                "Suburb": p.suburb.upper(),
                "Address": p.address,
                "Price": price,
                "Tier": tier,
                "Beds": p.bedrooms,
                "Link": f"https://www.domain.com.au/{p.address.replace(' ', '-').lower()}" # 伪链接
            })

df = pd.DataFrame(data)

if not df.empty:
    # 2. 侧边栏过滤器
    st.sidebar.header("Filters")
    selected_suburbs = st.sidebar.multiselect(
        "Select Suburbs", 
        options=sorted(df["Suburb"].unique()),
        default=["ASPENDALE", "ASPENDALE-GARDENS", "PATTERSON-LAKES"]
    )
    
    selected_tiers = st.sidebar.multiselect(
        "Asset Class",
        options=sorted(df["Tier"].unique()),
        default=["Tier 1: House", "Tier 2: Townhouse"]
    )

    # 3. 数据过滤
    filtered_df = df[
        (df["Suburb"].isin(selected_suburbs)) & 
        (df["Tier"].isin(selected_tiers))
    ]

    # 4. 核心指标 (KPIs)
    if not filtered_df.empty:
        avg_price = filtered_df["Price"].median()
        st.metric("Median Price (Selected)", f"${avg_price:,.0f}")
        
        # 5. 图表
        st.subheader("💰 Price Distribution by Suburb")
        st.bar_chart(filtered_df, x="Suburb", y="Price", color="Tier")

        # 6. 捡漏列表 (The Bargain List)
        st.subheader("🔥 Top Deals (Lowest Price First)")
        
        # 显示详细表格
        display_cols = ["Price", "Suburb", "Address", "Beds", "Tier"]
        st.dataframe(
            filtered_df.sort_values("Price")[display_cols].style.format({"Price": "${:,.0f}"}),
            use_container_width=True
        )
    else:
        st.info("No data matches your filters.")
else:
    st.error("No valid data found in database.")