import time
from flask import render_template, current_app
from app.extensions import mail
from flask_mail import Message

def send_email_retry(subject, recipients, html_body, retries=3, delay=5):
    for attempt in range(retries):
        try:
            msg = Message(subject, recipients=recipients, html=html_body)
            mail.send(msg)
            current_app.logger.info(f"Email sent successfully to {recipients}")
            return True
        except Exception as e:
            current_app.logger.error(f"Attempt {attempt+1} failed for {recipients}: {str(e)}")
            if attempt < retries - 1:
                time.sleep(delay)
    return False

def send_member_expiry_email(member):
    if not member.email:
        return False
    html = render_template('email_member.html', name=member.name)
    return send_email_retry(
        subject="Your Gym Membership Has Expired",
        recipients=[member.email],
        html_body=html
    )

def send_owner_batch_email(expired_members):
    owner_email = current_app.config.get('OWNER_EMAIL')
    if not owner_email:
        current_app.logger.error("OWNER_EMAIL not configured in env.")
        return False
    html = render_template('email_owner.html', members=expired_members)
    return send_email_retry(
        subject="Membership Expiry Alert - Action Required",
        recipients=[owner_email],
        html_body=html
    )