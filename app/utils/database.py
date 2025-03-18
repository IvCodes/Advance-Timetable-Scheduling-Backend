from pymongo import MongoClient
import logging
from passlib.context import CryptContext

MONGODB_URI:  str = "mongodb+srv://ivCodes:doNF7RbKedWTtB5S@timetablewiz-cluster.6pnyt.mongodb.net/?retryWrites=true&w=majority&appName=TimeTableWiz-Cluster"
# MONGODB_URI:  str = "mongodb+srv://easaragtech:TUpUMeBKMUC9GjkG@timetablewiz.mfha3.mongodb.net/?retryWrites=true&w=majority&appName=TimetableWiz"

client = MongoClient(MONGODB_URI)
db = client["time_table_whiz"]

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

  
# Test the connection
def test_connection():
    try:
        client.admin.command('ismaster')
        logging.info(f"MongoDB connection successful! Connected to database: {db.name}")
        return True
    except Exception as e:
        logging.error(f"MongoDB connection failed: {e}")
        return False
        
def initialize_database():
    """
    Initialize the database with required collections if they don't exist
    """
    try:
        logging.info("Initializing database collections...")
        logging.info(f"Database: {db.name}")
        
        # Print existing collections
        existing_collections = db.list_collection_names()
        logging.info(f"Existing collections: {existing_collections}")
        
        # Reset Users collection to ensure proper initialization
        if "Users" in existing_collections:
            # Don't drop the collection as it might have important user data
            # Instead, check each user and update accordingly
            pass
            
        required_collections = [
            "days_of_operation", 
            "periods_of_operation", 
            "faculties", 
            "modules", 
            "Activities", 
            "Users",
            "Spaces",
            "Years",
            "Timetable"
        ]
        
        for collection in required_collections:
            # Check if the collection exists (case-insensitive)
            exists = False
            for existing in existing_collections:
                if collection.lower() == existing.lower():
                    exists = True
                    logging.info(f"Collection {collection} already exists as {existing}")
                    break
                    
            if not exists:
                logging.info(f"Creating collection: {collection}")
                try:
                    db.create_collection(collection)
                    
                    # Add some default data for essential collections
                    if collection == "days_of_operation":
                        db[collection].insert_many([
                            {"name": "Monday", "code": "MON", "order": 1, "long_name": "Monday"},
                            {"name": "Tuesday", "code": "TUE", "order": 2, "long_name": "Tuesday"},
                            {"name": "Wednesday", "code": "WED", "order": 3, "long_name": "Wednesday"},
                            {"name": "Thursday", "code": "THU", "order": 4, "long_name": "Thursday"},
                            {"name": "Friday", "code": "FRI", "order": 5, "long_name": "Friday"}
                        ])
                    elif collection == "periods_of_operation":
                        db[collection].insert_many([
                            {"name": "Period 1", "start_time": "09:00", "end_time": "10:00", "order": 1, "long_name": "Period 1 (9:00-10:00)", "is_interval": False},
                            {"name": "Period 2", "start_time": "10:00", "end_time": "11:00", "order": 2, "long_name": "Period 2 (10:00-11:00)", "is_interval": False},
                            {"name": "Period 3", "start_time": "11:00", "end_time": "12:00", "order": 3, "long_name": "Period 3 (11:00-12:00)", "is_interval": False},
                            {"name": "Period 4", "start_time": "13:00", "end_time": "14:00", "order": 4, "long_name": "Period 4 (13:00-14:00)", "is_interval": False},
                            {"name": "Period 5", "start_time": "14:00", "end_time": "15:00", "order": 5, "long_name": "Period 5 (14:00-15:00)", "is_interval": False},
                            {"name": "Period 6", "start_time": "15:00", "end_time": "16:00", "order": 6, "long_name": "Period 6 (15:00-16:00)", "is_interval": False}
                        ])
                    elif collection == "Users":
                        try:
                            # Add a default admin user if no admin exists
                            if db[collection].count_documents({"role": "admin"}) == 0:
                                # Create hashed password
                                hashed_password = pwd_context.hash("sysadmin2023")
                                # Add a default admin user
                                db[collection].insert_one({
                                    "id": "AD0000002",  # Match the ID being used for login
                                    "username": "admin",
                                    "email": "admin@timetablewhiz.com",
                                    "role": "admin",
                                    "hashed_password": hashed_password,
                                    "first_name": "System",
                                    "last_name": "Administrator"
                                })
                                logging.info("Default admin user created")
                            
                            # Add a default faculty if none exists
                            if db[collection].count_documents({"role": "faculty"}) == 0:
                                # Add a default teacher
                                hashed_password = pwd_context.hash("faculty123")
                                db[collection].insert_one({
                                    "id": "FAC0000001",
                                    "username": "faculty",
                                    "email": "faculty@timetablewhiz.com",
                                    "role": "faculty",
                                    "hashed_password": hashed_password,
                                    "first_name": "Default",
                                    "last_name": "Teacher"
                                })
                                logging.info("Default faculty user created")
                        except Exception as e:
                            logging.error(f"Error adding default users: {str(e)}")
                except Exception as e:
                    logging.error(f"Error creating collection {collection}: {str(e)}")
        
        logging.info("Database initialization complete")
    except Exception as e:
        logging.error(f"Database initialization failed: {str(e)}")

def update_existing_collections():
    """
    Update existing collections with missing fields
    """
    try:
        # Update days collection with long_name if missing
        days_collection = "days_of_operation"
        if days_collection in db.list_collection_names():
            days = list(db[days_collection].find())
            for day in days:
                if "long_name" not in day:
                    db[days_collection].update_one(
                        {"_id": day["_id"]},
                        {"$set": {"long_name": day["name"]}}
                    )
                    logging.info(f"Updated day {day['name']} with long_name")
                    
        # Update periods collection with long_name and is_interval if missing
        periods_collection = "periods_of_operation"
        if periods_collection in db.list_collection_names():
            periods = list(db[periods_collection].find())
            for period in periods:
                updates = {}
                if "long_name" not in period:
                    if "start_time" in period and "end_time" in period:
                        long_name = f"{period['name']} ({period['start_time']}-{period['end_time']})"
                    else:
                        long_name = period["name"]
                    updates["long_name"] = long_name
                    
                if "is_interval" not in period:
                    updates["is_interval"] = False
                    
                if updates:
                    db[periods_collection].update_one(
                        {"_id": period["_id"]},
                        {"$set": updates}
                    )
                    logging.info(f"Updated period {period['name']} with {updates}")
                    
        logging.info("Collection updates complete")
    except Exception as e:
        logging.error(f"Error updating collections: {str(e)}")

def ensure_admin_exists():
    """
    Ensure that the admin user exists with the correct credentials
    Used to fix issues with logging in after database changes
    """
    try:
        logging.info("Checking for admin user...")
        
        # Look for admin with ID AD0000002
        admin = db["Users"].find_one({"id": "AD0000002"})
        
        if not admin:
            # Create admin if it doesn't exist
            hashed_password = pwd_context.hash("sysadmin2023")
            db["Users"].insert_one({
                "id": "AD0000002",  # Match the ID being used for login
                "username": "admin",
                "email": "admin@timetablewhiz.com",
                "role": "admin",
                "hashed_password": hashed_password,
                "first_name": "System",
                "last_name": "Administrator"
            })
            logging.info("Created new admin user with ID: AD0000002")
        else:
            # Update admin password if necessary
            if not pwd_context.verify("sysadmin2023", admin.get("hashed_password", "")):
                hashed_password = pwd_context.hash("sysadmin2023")
                db["Users"].update_one(
                    {"id": "AD0000002"},
                    {"$set": {"hashed_password": hashed_password}}
                )
                logging.info("Updated admin password for ID: AD0000002")
            else:
                logging.info("Admin user exists with correct password")
    except Exception as e:
        logging.error(f"Error ensuring admin exists: {str(e)}")

def ensure_activities_exist():
    """
    Ensure that some default activities exist in the database
    """
    try:
        logging.info("Checking for activities...")
        
        # Check if Activities collection exists and has data
        if "Activities" in db.list_collection_names() and db["Activities"].count_documents({}) > 0:
            logging.info(f"Found {db['Activities'].count_documents({})} existing activities")
            return
            
        logging.info("Creating default activities...")
        
        # Create some default activities
        default_activities = [
            {
                "code": "ACT001",
                "name": "Introduction to Programming Lecture",
                "subject": "CSC101",
                "activity_type": "lecture",
                "duration": 2,
                "teacher_ids": ["FAC0000001"],
                "subgroup_ids": ["SEM101"],
                "required_equipment": ["projector", "whiteboard"],
                "special_requirements": "Requires computer lab"
            },
            {
                "code": "ACT002",
                "name": "Data Structures Tutorial",
                "subject": "CSC102",
                "activity_type": "tutorial",
                "duration": 1,
                "teacher_ids": ["FAC0000001"],
                "subgroup_ids": ["SEM101"],
                "required_equipment": ["whiteboard"],
                "special_requirements": None
            },
            {
                "code": "ACT003",
                "name": "Database Systems Lab",
                "subject": "CSC103",
                "activity_type": "lab",
                "duration": 3,
                "teacher_ids": ["FAC0000001"],
                "subgroup_ids": ["SEM102"],
                "required_equipment": ["computers", "database_software"],
                "special_requirements": "Database server access required"
            }
        ]
        
        # Insert activities
        db["Activities"].insert_many(default_activities)
        logging.info(f"Added {len(default_activities)} default activities")
        
    except Exception as e:
        logging.error(f"Error ensuring activities exist: {str(e)}")