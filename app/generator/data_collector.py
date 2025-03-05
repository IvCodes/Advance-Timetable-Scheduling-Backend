from app.utils.database import db

def get_collections():
    """Get all collection names in the database"""
    return db.list_collection_names()

def get_faculties():
    collections = get_collections()
    if "faculties" in collections:
        faculties = list(db["faculties"].find())
    else:
        faculties = list(db["Faculties"].find()) if "Faculties" in collections else []
    return faculties

def get_days():
    collections = get_collections()
    if "days_of_operation" in collections:
        days = list(db["days_of_operation"].find())
    else:
        days = list(db["Days"].find()) if "Days" in collections else []
    return days

def get_years():
    collections = get_collections()
    if "Years" in collections:
        years = list(db["Years"].find())
    else:
        years = list(db["years"].find()) if "years" in collections else []
    return years

def get_periods():
    collections = get_collections()
    if "periods_of_operation" in collections:
        periods = list(db["periods_of_operation"].find())
    else:
        periods = list(db["Periods"].find()) if "Periods" in collections else []
    return periods

def get_spaces():
    collections = get_collections()
    if "Spaces" in collections:
        spaces = list(db["Spaces"].find())
    else:
        spaces = list(db["spaces"].find()) if "spaces" in collections else []
    return spaces

def get_activities():
    collections = get_collections()
    if "Activities" in collections:
        activities = list(db["Activities"].find())
    else:
        activities = list(db["activities"].find()) if "activities" in collections else []
    return activities

def get_modules():
    collections = get_collections()
    if "modules" in collections:
        modules = list(db["modules"].find())
    else:
        modules = list(db["Modules"].find()) if "Modules" in collections else []
    return modules

def get_teachers():
    collections = get_collections()
    if "Users" in collections:
        teachers = list(db["Users"].find({
            "role": "faculty"
        }))
    else:
        teachers = []
    return teachers

def get_students():
    collections = get_collections()
    if "Users" in collections:
        students = list(db["Users"].find({
            "role": "student"
        }))
    else:
        students = []
    return students

def get_timetables():
    collections = get_collections()
    if "Timetable" in collections:
        timetable = list(db["Timetable"].find())
    else:
        timetable = list(db["timetables"].find()) if "timetables" in collections else []
    return timetable