from pymongo import MongoClient
from datetime import datetime
from utils.database import client, db
import json
from passlib.context import CryptContext


collection = db["modules"]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "TimeTableWhiz" 
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def load_data_from_json(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
    return data

def add_hashed_passwords(data):
    for d in data:
        if "hashed_password" in d:
            d["hashed_password"] = hash_password(d["hashed_password"])
    return data

def insert_data_into_mongo(data):
    try:
        result = collection.insert_many(data)
        print(f"Inserted {len(result.inserted_ids)} data successfully.")
    except Exception as e:
        print(f"Error inserting data: {e}")

data_file = "modules.json"  

data = load_data_from_json(data_file)

# data = add_hashed_passwords(data)

insert_data_into_mongo(data)
