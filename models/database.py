from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import config

_client = None

def get_db():
    global _client
    if _client is None:
        _client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=10000, maxPoolSize=10)
    return _client['spartanDB']

def init_db():
    try:
        db = get_db()
        db.command("ping")
        print("✅ MongoDB Connected & Ready!")
        db.users.create_index("phone", unique=True)
    except ConnectionFailure as e:
        print(f"❌ MONGODB CONNECTION FAILED! Check MONGO_URI.")
    except Exception as e:
<<<<<<< HEAD
        print(f"❌ Error: {e}")
=======
        print(f"❌ Error: {e}")
>>>>>>> dfea781 (Added Hero Banner, Fixed Razorpay and Group Image)
