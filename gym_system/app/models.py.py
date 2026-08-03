from datetime import datetime
from app.extensions import db

class Member(db.Document):
    name = db.StringField(max_length=100, required=True)
    phone = db.StringField(max_length=20, required=True)
    email = db.StringField(max_length=120)
    shift = db.StringField(max_length=50, required=True)
    membership_plan = db.StringField(max_length=50, required=True)
    joining_date = db.DateTimeField(required=True)
    expiry_date = db.DateTimeField(required=True)
    amount_paid = db.FloatField(default=0.0)
    
    notification_sent = db.BooleanField(default=False)
    notification_sent_at = db.DateTimeField()
    is_active = db.BooleanField(default=True)

    meta = {
        'indexes': [
            'expiry_date',
            'notification_sent'
        ]
    }

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "shift": self.shift,
            "plan": self.membership_plan,
            "joining_date": self.joining_date.strftime('%Y-%m-%d'),
            "expiry_date": self.expiry_date.strftime('%Y-%m-%d'),
            "amount": self.amount_paid,
            "is_active": self.is_active
        }