from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from app.utils.database import test_connection
from app.routers import space_routes
from app.routers import year_routes, info_router, module_routes, user_router, faculty_routes, timetable_routes, activity_routes

# Get the directory of the application
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Create logs directory if it doesn't exist 
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        RotatingFileHandler(
            os.path.join(LOG_DIR, "app.log"), 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,  # Keep 5 backup files
            encoding='utf-8'
        )
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

app.include_router(user_router.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(info_router.router, prefix="/api/v1/info", tags=["Info"])
app.include_router(faculty_routes.router, prefix="/api/v1/faculty", tags=["Faculty"])
app.include_router(module_routes.router, prefix="/api/v1/module", tags=["Module"])
app.include_router(year_routes.router, prefix="/api/v1/year", tags=["Year"])
app.include_router(space_routes.router, prefix="/api/v1/space", tags=["Space"])
app.include_router(timetable_routes.router, prefix="/api/v1/timetable", tags=["Timetable"])
app.include_router(activity_routes.router, prefix="/api/v1/activity", tags=["Activity"])

@app.get("/")
async def root():
    return {"message": "Welcome to the TimeTableWhiz"} 

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)