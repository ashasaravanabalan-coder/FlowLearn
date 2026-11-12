"""MongoDB connection and collections."""
import os
from pymongo import MongoClient, DESCENDING

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"), serverSelectionTimeoutMS=5000)
db = client[os.getenv("MONGO_DB", "flowlearn")]
users = db["users"]
sessions = db["sessions"]


def init_indexes():
    users.create_index("username", unique=True)
    sessions.create_index([("user_id", 1), ("created_at", DESCENDING)])
