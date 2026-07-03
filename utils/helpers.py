# utils/helpers.py
# Ye file chote-chote helper functions rakhti hai jo kahin bhi use ho sakte hain

from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    """
    Decorator: Sirf logged-in users ko page access karne deta hai.
    Agar user login nahi hai to login page par redirect kar deta hai.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('⚠️ Please pehle login karein!', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def calculate_bmi(weight, height):
    """
    BMI calculate karta hai.
    weight: kg mein
    height: cm mein (convert ho jayega meters mein)
    """
    if height <= 0 or weight <= 0:
        return None
    
    height_in_meters = height / 100  # cm ko meters mein convert kiya
    bmi = weight / (height_in_meters ** 2)
    return round(bmi, 2)

def get_bmi_category(bmi):
    """BMI ke hisaab se category return karta hai"""
    if bmi < 18.5:
        return "Underweight", "⚠️ Aapka weight kam hai. Proper diet lein."
    elif 18.5 <= bmi < 25:
        return "Normal", "✅ Perfect! Aap fit hain."
    elif 25 <= bmi < 30:
        return "Overweight", "⚠️ Thoda weight kam karna padega."
    else:
        return "Obese", "🚨 Turant gym join karein aur diet control karein!"

def validate_email(email):
    """Email valid hai ya nahi check karta hai"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Phone number valid hai ya nahi check karta hai (10 digits)"""
    if not phone:
        return True  # Phone optional ho sakta hai
    return phone.isdigit() and len(phone) == 10