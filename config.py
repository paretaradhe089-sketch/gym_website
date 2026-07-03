# config.py
import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-spartan-key-2024')
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/spartanDB')
ADMIN_PASSWORD = "gym@57675656"