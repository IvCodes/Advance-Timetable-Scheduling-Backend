from pymongo import MongoClient

MONGODB_URI: str = "mongodb+srv://wkmswanthra:wkmswanthra@test-bed.dtgmi5a.mongodb.net/?retryWrites=true&w=majority&appName=test-bed"


client = MongoClient(MONGODB_URI)
db = client["time_table_whiz"]

