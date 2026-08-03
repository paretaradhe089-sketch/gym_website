import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from app.config import Config
from app.extensions import db, mail

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Extensions
    db.init_app(app)
    mail.init_app(app)

    # Logging Setup
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    # Register Blueprints
    from app.routes.admin_routes import admin_bp
    app.register_blueprint(admin_bp)

    # Start Scheduler
    from app.services.scheduler_service import start_scheduler
    start_scheduler(app)

    return app