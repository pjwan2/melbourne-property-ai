# init_db.py
import logging
from sqlmodel import Session, text
from app.core.database import create_db_and_tables, engine
# IMPORTANT: Import the model so SQLModel knows what table to create
from app.models.property import Property

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init():
    logger.info("Connecting to AWS RDS...")

    try:
        # 1. Test the connection
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        logger.info("Connection Successful! (AWS is reachable)")
        
        # 2. Create the tables
        logger.info("Creating tables...")
        create_db_and_tables()
        logger.info("🎉 Success! The 'property' table is created in the cloud!")
        
    except Exception as e:
        logger.error(f" Connection Failed: {e}")
        logger.error("Hint: Check your VPN, AWS Security Group, or password.")

if __name__ == "__main__":
    init()