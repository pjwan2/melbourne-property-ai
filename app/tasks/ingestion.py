# app/tasks/ingestion.py
import logging
from app.core.celery_app import celery_app
from app.services.scraper_service import RealEstateScraper
from app.services.property_service import PropertyService

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.ingestion.mock_scraping_task")
def mock_scraping_task(self, suburb: str):
    task_id = self.request.id
    logger.info(f"Task {task_id}: 🚀 Starting Real Scraper for {suburb}")

    try:
        # Step 1: Scrape Data
        scraper = RealEstateScraper()
        data = scraper.scrape_suburb(suburb)
        
        logger.info(f"Task {task_id}: Scraped {len(data)} items. Now saving to DB...")

        # Step 2: Save to DB
        property_service = PropertyService()
        saved_count = property_service.save_properties(data)
        
        logger.info(f"Task {task_id}: Job Done! Saved {saved_count} new properties to AWS.")
        
        return {
            "status": "completed",
            "suburb": suburb,
            "properties_found": len(data),
            "properties_saved": saved_count,
            "data_preview": data[:3] 
        }

    except Exception as e:
        logger.error(f"Task {task_id}: Failed: {str(e)}")
        raise e