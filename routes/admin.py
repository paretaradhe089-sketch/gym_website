# routes/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.database import get_db
from config import ADMIN_PASSWORD
from datetime import datetime, timedelta
from functools import wraps
from bson import ObjectId

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin.dashboard'))
        flash('❌ Galat Password!', 'error')
    return render_template('admin_login.html')

@admin_bp.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('main.index'))

def check_expiry_notifications(db):
    today = datetime.now()
    three_days_later = today + timedelta(days=3)
    
    active_users = db.users.find({'status': 'Active'})
    for user in active_users:
        expiry = user.get('expiry_date')
        if not expiry: continue
        
        if today <= expiry <= three_days_later:
            existing_notif = db.notifications.find_one({
                'user_phone': user['phone'],
                'type': 'Expiry',
                'is_read': False
            })
            if not existing_notif:
                db.notifications.insert_one({
                    'type': 'Expiry',
                    'message': f"⚠️ {user['name']} ka plan {expiry.strftime('%d %b')} ko expire ho raha hai!",
                    'user_phone': user['phone'],
                    'created_at': datetime.now(),
                    'is_read': False
                })

@admin_bp.route('/admin/dashboard')
@admin_required
def dashboard():
    db = get_db()
    check_expiry_notifications(db)
    
    active_users = db.users.count_documents({'status': 'Active'})
    pending_users = db.users.count_documents({'status': 'Pending'})
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_payments_cursor = db.users.find({
        'join_date': {'$gte': datetime(current_year, current_month, 1)},
        'payment_method': 'Cash'
    })
    total_payment = sum(u.get('amount', 0) for u in monthly_payments_cursor)
    
    search_query = request.args.get('search', '')
    if search_query:
        users = list(db.users.find({'phone': {'$regex': search_query}}).sort('join_date', -1))
    else:
        users = list(db.users.find().sort('join_date', -1))
        
    notifications = list(db.notifications.find({'is_read': False}).sort('created_at', -1))
    feedbacks = list(db.feedback.find().sort('created_at', -1))

    return render_template('admin_dashboard.html', 
                           active_users=active_users, pending_users=pending_users,
                           total_payment=total_payment, users=users, 
                           notifications=notifications, feedbacks=feedbacks,
                           search_query=search_query)

@admin_bp.route('/admin/edit/<user_id>', methods=['POST'])
@admin_required
def edit_user(user_id):
    db = get_db()
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {
        'name': request.form.get('name'),
        'phone': request.form.get('phone'),
        'address': request.form.get('address'),
        'status': request.form.get('status')
    }})
    flash('✅ User updated!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/delete/<user_id>')
@admin_required
def delete_user(user_id):
    db = get_db()
    db.users.delete_one({'_id': ObjectId(user_id)})
    flash('🗑️ User deleted!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/delete_feedback/<feedback_id>')
@admin_required
def delete_feedback(feedback_id):
    db = get_db()
    db.feedback.delete_one({'_id': ObjectId(feedback_id)})
    flash('🗑️ Feedback deleted!', 'success')
    return redirect(url_for('admin.dashboard') + '#feedbacks')

@admin_bp.route('/admin/delete_notification/<notif_id>')
@admin_required
def delete_notification(notif_id):
    db = get_db()
    db.notifications.delete_one({'_id': ObjectId(notif_id)})
    flash('✅ Notification cleared!', 'success')
    return redirect(url_for('admin.dashboard'))