# app/core/database.py
import os
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()

# 2. Get the DATABASE_URL from .env
DATABASE_URL = os.getenv("DATABASE_URL")

# 3. Ensure DATABASE_URL is set
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the .env file")

# 4. Create the engine
# echo=True means it will print SQL statements to the console (good for debugging)
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    """Dependency for FastAPI to get a database session."""
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    """Create all tables defined in SQLModel metadata."""
    SQLModel.metadata.create_all(engine)