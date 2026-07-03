# app.py
from flask import Flask
from config import SECRET_KEY
from models.database import init_db
from routes.main import main_bp
from routes.admin import admin_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

init_db()

app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    print("🏋️ Spartan Fitness Zone Starting on http://localhost:5000")
    app.run(debug=True, port=5000)