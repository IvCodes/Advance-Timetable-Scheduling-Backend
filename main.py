from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from database import test_connection
from routers import user_router, info_router, faculty_routes, module_routes, year_routes, space_routes

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
    test_connection()

app.include_router(user_router.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(info_router.router, prefix="/api/v1/info", tags=["Info"])
app.include_router(faculty_routes.router, prefix="/api/v1/faculty", tags=["Faculty"])
app.include_router(module_routes.router, prefix="/api/v1/module", tags=["Module"])
app.include_router(year_routes.router, prefix="/api/v1/year", tags=["Year"])
app.include_router(space_routes.router, prefix="/api/v1/space", tags=["Space"])

@app.get("/")
async def root():
    return {"message": "Welcome to the TimeTableWhiz"} 

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)