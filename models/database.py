from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import config
from datetime import datetime

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
        
        # Default Coupons Add karna (Agar nahi hain toh) - Expiry 2033 ki hai
        if db.coupons.count_documents({}) == 0:
            db.coupons.insert_many([
                {'code': 'WELCOME10', 'type': 'percentage', 'value': 10, 'max_discount': 500, 'min_amount': 1000, 'expiry_date': '2033-12-31', 'max_uses': 100, 'current_uses': 0, 'is_active': True, 'description': '10% Off on plans above 1000'},
                {'code': 'GYM500', 'type': 'flat', 'value': 500, 'max_discount': 500, 'min_amount': 5000, 'expiry_date': '2033-12-31', 'max_uses': 50, 'current_uses': 0, 'is_active': True, 'description': 'Flat 500 Off on Yearly Plan'},
                {'code': 'NEWUSER', 'type': 'percentage', 'value': 15, 'max_discount': 1000, 'min_amount': 1200, 'expiry_date': '2030-12-31', 'max_uses': 100, 'current_uses': 0, 'is_active': True, 'description': '15% Off for new users'}
            ])
            print("✅ Default Coupons Added!")
            
        # Default Offer Banner
        if db.offers.count_documents({}) == 0:
            db.offers.insert_one({'text': '🔥 Monsoon Offer! Get ₹500 OFF on Yearly Plans. Use Code: GYM500', 'is_active': True})
            
    except ConnectionFailure as e:
        print(f"❌ MONGODB CONNECTION FAILED! Check MONGO_URI.")
    except Exception as e:
        print(f"❌ Error: {e}")
