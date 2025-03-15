from datetime import datetime
from app.utils.database import db
import json

constraints_collection = db["constraints"]

constraints = []
with open('constraints.json', 'r') as file:
    constraints = json.load(file)


default_settings = {}
default_applicability = {
    "teachers": None,
    "students": None,
    "activities": None,
    "spaces": None,
    "all_teachers": False,
    "all_students": False,
    "all_activities": False
}
for constraint in constraints:
    constraint.update({
        "description": "",
        "settings": default_settings,
        "applicability": default_applicability,
        "weight": 100,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    })

result = constraints_collection.insert_many(constraints)

print(f"Inserted {len(result.inserted_ids)} constraints into the database.")
