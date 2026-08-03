from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import current_app
import logging

scheduler = BackgroundScheduler()

def scheduled_job():
    from app.services.membership_service import process_expired_members
    with current_app.app_context():
        current_app.logger.info("Running daily expiry notification job...")
        result = process_expired_members()
        current_app.logger.info(f"Job result: {result}")

def start_scheduler(app):
    if app.debug and app.config.get('WERKZEUG_RUN_MAIN') != 'true':
        return

    trigger = CronTrigger(hour=3, minute=30, timezone='UTC')
    
    scheduler.add_job(
        func=scheduled_job,
        trigger=trigger,
        id='daily_expiry_job',
        replace_existing=True
    )
    
    if not scheduler.running:
        scheduler.start()
        app.logger.info("APScheduler started successfully.")