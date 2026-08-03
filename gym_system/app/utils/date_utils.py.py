from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz

IST = pytz.timezone('Asia/Kolkata')

def get_today_ist():
    return datetime.now(IST).date()

def calculate_expiry(joining_date):
    if isinstance(joining_date, str):
        joining_date = datetime.strptime(joining_date, '%Y-%m-%d').date()
    elif isinstance(joining_date, datetime):
        joining_date = joining_date.date()
        
    expiry = joining_date + relativedelta(months=1)
    return expiry