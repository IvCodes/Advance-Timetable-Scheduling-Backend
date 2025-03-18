from .database import db

def get_faculties():
    faculties = list(db["faculties"].find())
    return faculties

def get_days():
    days = list(db["days_of_operation"].find())
    return days

def get_years():
    years = list(db["Years"].find())
    return years

def get_periods():
    periods = list(db["periods_of_operation"].find())
    return periods

def get_spaces():
    spaces = list(db["Spaces"].find())
    return spaces

def get_activities():
    activities = list(db["Activities"].find())
    return activities

def get_modules():
    modules = list(db["modules"].find())
    return modules

def get_teachers():
    teachers = list(db["Users"].find({
        "role": "faculty"
    }))
    return teachers

def get_students():
    students = list(db["Users"].find({
        "role": "student"
    }))
    return students