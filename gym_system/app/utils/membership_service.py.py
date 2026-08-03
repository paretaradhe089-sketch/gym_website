from datetime import datetime
from app.models import Member
from app.utils.date_utils import get_today_ist, calculate_expiry
from app.services.email_service import send_member_expiry_email, send_owner_batch_email

def process_expired_members():
    today = get_today_ist()
    today_end = datetime.combine(today, datetime.max.time())
    
    expired_members = Member.objects(
        expiry_date__lte=today_end,
        notification_sent=False,
        is_active=True
    )

    if not expired_members:
        return {"status": "success", "message": "No expired members to process today."}

    successfully_notified = []
    
    for member in expired_members:
        email_sent = False
        if member.email:
            email_sent = send_member_expiry_email(member)
        else:
            email_sent = True 
            
        if email_sent:
            member.notification_sent = True
            member.notification_sent_at = datetime.utcnow()
            member.is_active = False
            member.save()
            successfully_notified.append(member)
        else:
            current_app.logger.warning(f"Failed to send email to {member.name} ({member.phone}). Will retry tomorrow.")
            
    if successfully_notified:
        send_owner_batch_email(successfully_notified)
        
    return {
        "status": "success", 
        "processed": len(successfully_notified),
        "failed": len(expired_members) - len(successfully_notified)
    }

def renew_member(member_id):
    try:
        member = Member.objects.get(id=member_id)
    except:
        return False
        
    today = get_today_ist()
    
    member.joining_date = today
    member.expiry_date = calculate_expiry(today)
    member.notification_sent = False
    member.notification_sent_at = None
    member.is_active = True
    
    member.save()
    return True