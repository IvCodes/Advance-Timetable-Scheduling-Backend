from pymongo import MongoClient

MONGODB_URI:  str = "mongodb+srv://ivCodes:doNF7RbKedWTtB5S@timetablewiz-cluster.6pnyt.mongodb.net/?retryWrites=true&w=majority&appName=TimeTableWiz-Cluster"

client = MongoClient(MONGODB_URI)
db = client["TimeTable_Wiz"]


# Test the connection
def test_connection():
    try:
        # The ismaster command is cheap and does not require auth
        client.admin.command('ismaster')
        print("MongoDB connection successful!")
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return False
