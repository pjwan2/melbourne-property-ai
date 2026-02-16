from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from celery.result import AsyncResult
from app.tasks.ingestion import mock_scraping_task

app = FastAPI(
    title="Real Estate Analyzer API",
    description="Senior Data Engineering & AI Backend API",
    version="1.0.0"
)

# Pydantic model for request validation
class IngestionRequest(BaseModel):
    suburb: str

@app.get("/health")
def health_check():
    """
    Health check endpoint to verify system status.
    """
    return {"status": "active", "service": "real-estate-analyzer"}

@app.post("/api/v1/ingest")
def trigger_ingestion(request: IngestionRequest):
    """
    Triggers the background scraping pipeline for a specific suburb.
    Returns the Task ID for status tracking.
    """
    task = mock_scraping_task.delay(request.suburb)
    return {
        "message": "Ingestion task queued successfully",
        "task_id": task.id,
        "status": "pending"
    }

@app.get("/api/v1/tasks/{task_id}")
def get_task_status(task_id: str):
    """
    Retrieves the status of a background task.
    """
    task_result = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result
    }