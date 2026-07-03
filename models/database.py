# models/database.py
from pymongo import MongoClient
import config

def get_db():
    client = MongoClient(config.MONGO_URI)
    return client['spartanDB']

def init_db():
    db = get_db()
    db.users.create_index("phone", unique=True)
    print("✅ MongoDB Connected & Ready!")