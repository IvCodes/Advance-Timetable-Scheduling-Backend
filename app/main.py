from fastapi import FastAPI,Response 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
import logging
import os
import sys
import asyncio
import threading
import queue
import json 
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from logging.handlers import RotatingFileHandler
from app.utils.database import test_connection
from app.routers import space_routes 
from app.routers import year_routes, info_router, module_routes, user_router, faculty_routes, timetable_routes, activity_routes
from app.routers import timetable_sliit, dashboard_routes, faculty_unavailability_routes, notification_routes
from app.routers.chatbot.router import router as chatbot_router
from app.etl import etl_router

log_queue = queue.Queue()

class QueueHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        log_queue.put(log_entry)



# Get the directory of the application
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Create logs directory if it doesn't exist 
os.makedirs(LOG_DIR, exist_ok=True)


# Configure logging
queue_handler = QueueHandler()
queue_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        queue_handler,  # Add queue handler for SSE
    ]
)

# Get logger for this file
logger = logging.getLogger(__name__)

app = FastAPI(
    title="University Scheduler API",
    description="""
    Backend API for University Scheduler System.
    Manage spaces, faculty, modules, and student information efficiently.
    """,
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Users",
            "description": "Operations with users, authentication and authorization"
        },
        {
            "name": "Info",
            "description": "University information management"
        },
        {
            "name": "Faculty",
            "description": "Faculty management operations"
        },
        {
            "name": "Module",
            "description": "Course module management"
        },
        {
            "name": "Year",
            "description": "Academic year and student group management"
        },
        {
            "name": "Space",
            "description": "Physical space and room management"
        },
        {
            "name": "Activity",
            "description": "Teaching and learning activities management"
        }
    ]
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
    expose_headers=["*"],
)

# Test database connection on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting TimeTableWhiz API")
    if test_connection():
        from app.utils.database import initialize_database, update_existing_collections, ensure_admin_exists, ensure_activities_exist
        initialize_database()
        update_existing_collections()
        ensure_admin_exists()  # Make sure admin user exists
        ensure_activities_exist()  # Make sure default activities exist
    else:
        logger.error("Database connection failed. Application may not function correctly!")

@app.get("/test-logs")
async def test_logs():
    logger = logging.getLogger(__name__)
    logger.info("Test log 1")
    logger.info("Test log 2")
    logger.info("Test log 3")
    return {"message": "Logs generated"}

app.include_router(user_router.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(info_router.router, prefix="/api/v1/info", tags=["Info"])
app.include_router(faculty_routes.router, prefix="/api/v1/faculty", tags=["Faculty"])
app.include_router(module_routes.router, prefix="/api/v1/module", tags=["Module"])
app.include_router(year_routes.router, prefix="/api/v1/year", tags=["Year"])
app.include_router(space_routes.router, prefix="/api/v1/space", tags=["Space"])
app.include_router(timetable_routes.router, prefix="/api/v1/timetable", tags=["Timetable"])
app.include_router(activity_routes.router, prefix="/api/v1/activity", tags=["Activity"])
app.include_router(chatbot_router, prefix="/api/v1/chatbot", tags=["Chatbot"])
app.include_router(etl_router, prefix="/api/v1/etl", tags=["etl"])
app.include_router(timetable_sliit.router, prefix="/api/v1/timetable/sliit", tags=["Timetable SLIIT"]) # Include the new router
app.include_router(dashboard_routes.router, prefix="/api/v1/dashboard", tags=["Dashboard"]) # Include dashboard routes
app.include_router(faculty_unavailability_routes.router, prefix="/api/v1/faculty-availability", tags=["Faculty Availability"])
app.include_router(notification_routes.router, prefix="/api/v1", tags=["Notifications"])

@app.get("/")
async def root():
    return {"message": "Welcome to the TimeTableWhiz"} 

# SSE generator function
async def event_generator():
    while True:
        if not log_queue.empty():
            log_entry = log_queue.get()
            yield f"data: {json.dumps({'message': log_entry})}\n\n"
        await asyncio.sleep(0.1)

@app.get("/api/v1/timetable/progress-stream")
async def stream_progress(response: Response):
    response.headers["Content-Type"] = "text/event-stream"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)