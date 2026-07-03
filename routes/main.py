# routes/main.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.database import get_db
from datetime import datetime

main_bp = Blueprint('main', __name__)

def add_months(source_date, months):
    new_month = source_date.month - 1 + months
    new_year = source_date.year + new_month // 12
    new_month = new_month % 12 + 1
    return datetime(new_year, new_month, source_date.day)

@main_bp.route('/')
def index():
    db = get_db()
    active_users = db.users.count_documents({'status': 'Active'})
    return render_template('index.html', active_users=active_users)

@main_bp.route('/register', methods=['POST'])
def register_user():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        plan = request.form.get('plan', 'Monthly')
        payment_method = request.form.get('payment_method', 'Cash')
        
        if not name or not phone:
            flash('⚠️ Naam aur Phone zaroori hai!', 'error')
            return redirect(url_for('main.index'))
        
        db = get_db()
        if db.users.find_one({'phone': phone}):
            flash('⚠️ Ye phone number already registered hai!', 'error')
            return redirect(url_for('main.index'))
        
        join_date = datetime.now()
        months_map = {'Monthly': 1, 'Quarterly': 3, '6 months': 6, 'Yearly': 12}
        amount_map = {'Monthly': 1200, 'Quarterly': 3000, '6 months': 5000, 'Yearly': 8000}
        
        user_data = {
            'name': name,
            'phone': phone,
            'address': address,
            'plan': plan,
            'payment_method': payment_method,
            'amount': amount_map.get(plan, 1200),
            'status': 'Active' if payment_method == 'Cash' else 'Pending',
            'join_date': join_date,
            'expiry_date': add_months(join_date, months_map.get(plan, 1))
        }
        
        db.users.insert_one(user_data)
        
        db.notifications.insert_one({
            'type': 'New User',
            'message': f'🆕 Naya User: {name} ({phone}) - Plan: {plan}',
            'user_phone': phone,
            'created_at': datetime.now(),
            'is_read': False
        })
        
        flash('✅ Registration Successful! Admin aapse contact karenge.', 'success')
        return redirect(url_for('main.index'))

@main_bp.route('/services')
def services():
    services_list = [
        {'icon': '🏋️', 'title': 'Gym'},
        {'icon': '🔥', 'title': 'HIIT Exercise Classes'},
        {'icon': '💃', 'title': 'Aerobics'},
        {'icon': '🤸', 'title': 'Crossfit'},
        {'icon': '🎵', 'title': 'Zumba'},
        {'icon': '👨‍🏫', 'title': 'Personal training'},
        {'icon': '🧘', 'title': 'Yoga classes'},
        {'icon': '⚽', 'title': 'Adult sports'},
        {'icon': '💪', 'title': 'Weight training'},
        {'icon': '🥗', 'title': 'Nutrition consulting'},
        {'icon': '🚴', 'title': 'Cycling'},
        {'icon': '🏆', 'title': 'Bodybuilding'}
    ]
    return render_template('services.html', services=services_list)

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    db = get_db()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        
        if not name or not message:
            flash('⚠️ Naam aur Message zaroori hai!', 'error')
            return redirect(url_for('main.contact'))
        
        db.feedback.insert_one({
            'name': name, 'email': email, 'message': message, 'created_at': datetime.now()
        })
        flash('✅ Feedback bhej diya! Thank you.', 'success')
        return redirect(url_for('main.contact'))
    return render_template('contact.html')