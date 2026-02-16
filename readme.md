# 🏡 Melbourne Real Estate AI Analyzer

An advanced data engineering pipeline that scrapes, analyzes, and valuates real estate properties in Melbourne to identify undervalued assets (Tier 1 Houses vs. Tier 2 Units).

## 🚀 Key Features

* **Stealth Scraping**: Uses `Playwright` in Cyborg Mode to bypass anti-bot detection on major real estate platforms.
* **Data Enrichment**: Automatically fetches hidden attributes like **Land Size** and **Internal Area** to calculate price-per-sqm.
* **Asset Classification**: Regex-based heuristic algorithm to distinguish between *Full Block Houses* (Tier 1) and *Subdivisions/Townhouses* (Tier 2).
* **AI Agent**: Integrated Vision AI module to assess property condition (Renovated vs. Derelict) from images.
* **Visualization**: Interactive Streamlit dashboard for real-time market monitoring.

## 🛠️Tech Stack

* **Core**: Python 3.10+
* **Scraper**: Playwright, BeautifulSoup4
* **Database**: PostgreSQL (AWS RDS), SQLModel (ORM)
* **Frontend**: Streamlit
* **AI**: OpenAI GPT-4o (Vision)

## ⚠️ Disclaimer

This project is for **educational and research purposes only**. The scraped data is not included in this repository. Please respect the Terms of Service of the target websites.