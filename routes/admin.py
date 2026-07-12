# from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, Response
# from models.database import get_db
# from config import ADMIN_PASSWORD
# from datetime import datetime, timedelta
# from functools import wraps
# from bson import ObjectId
# import csv
# import io

# admin_bp = Blueprint('admin', __name__)

# # ─── Middleware ──────────────────────────────────────────────────

# def admin_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'admin_logged_in' not in session:
#             return redirect(url_for('admin.admin_login'))
#         return f(*args, **kwargs)
#     return decorated_function

# # ─── Auth Routes ────────────────────────────────────────────────

# @admin_bp.route('/admin/login', methods=['GET', 'POST'])
# def admin_login():
#     if request.method == 'POST':
#         if request.form.get('password') == ADMIN_PASSWORD:
#             session['admin_logged_in'] = True
#             return redirect(url_for('admin.dashboard'))
#         flash('❌ Galat Password!', 'error')
#     return render_template('admin_login.html')

# @admin_bp.route('/admin/logout')
# def admin_logout():
#     session.clear()
#     return redirect(url_for('main.index'))

# # ─── Dashboard & Notifications ─────────────────────────────────

# def check_expiry_notifications(db):
#     today = datetime.now()
#     three_days_later = today + timedelta(days=3)

#     for user in db.users.find({'status': 'Active'}):
#         expiry = user.get('expiry_date')
#         if expiry and today <= expiry <= three_days_later:
#             if not db.notifications.find_one({
#                 'user_phone': user['phone'], 'type': 'Expiry', 'is_read': False
#             }):
#                 db.notifications.insert_one({
#                     'type': 'Expiry',
#                     'message': f"⚠️ {user['name']} ka plan {expiry.strftime('%d %b')} ko expire ho raha hai!",
#                     'user_phone': user['phone'],
#                     'created_at': datetime.now(),
#                     'is_read': False
#                 })

# @admin_bp.route('/admin/dashboard')
# @admin_required
# def dashboard():
#     db = get_db()

#     check_expiry_notifications(db)

#     active_users = db.users.count_documents({'status': 'Active'})
#     pending_users = db.users.count_documents({'status': 'Pending'})
#     total_users = db.users.count_documents({})

#     current_month = datetime.now().month
#     current_year = datetime.now().year

#     total_payment = sum(
#         u.get('amount', 0)
#         for u in db.users.find({
#             'join_date': {'$gte': datetime(current_year, current_month, 1)},
#             'payment_method': 'Cash'
#         })
#     )

#     users = list(db.users.find().sort('join_date', -1))
#     notifications = list(db.notifications.find({'is_read': False}).sort('created_at', -1))
#     feedbacks = list(db.feedback.find().sort('created_at', -1))

#     return render_template(
#         'admin_dashboard.html',
#         active_users=active_users,
#         pending_users=pending_users,
#         total_users=total_users,
#         total_payment=total_payment,
#         users=users,
#         notifications=notifications,
#         feedbacks=feedbacks
#     )

# # ─── Transactions & Export ─────────────────────────────────────

# @admin_bp.route('/admin/transactions')
# @admin_required
# def transactions():
#     db = get_db()
#     payments = list(db.payments.find().sort('date', -1))
#     return render_template('admin_transactions.html', payments=payments)

# @admin_bp.route('/admin/export_csv')
# @admin_required
# def export_csv():
#     db = get_db()
#     payments = list(db.payments.find().sort('date', -1))

#     output = io.StringIO()
#     writer = csv.writer(output)

#     writer.writerow([
#         'Member Name', 'Phone', 'Email', 'Plan', 'Amount',
#         'Transaction ID', 'Order ID', 'Method', 'Status', 'Date'
#     ])

#     for p in payments:
#         writer.writerow([
#             p.get('name', ''),
#             p.get('phone', ''),
#             p.get('email', ''),
#             p.get('plan', ''),
#             p.get('amount', 0),
#             p.get('transaction_id', ''),
#             p.get('order_id', ''),
#             p.get('payment_method', ''),
#             p.get('status', ''),
#             p.get('date', '')
#         ])

#     output.seek(0)

#     return Response(
#         output,
#         mimetype="text/csv",
#         headers={"Content-Disposition": "attachment; filename=SFZ_Transactions.csv"}
#     )

# # ─── API & Actions ─────────────────────────────────────────────

# @admin_bp.route('/admin/search_api')
# @admin_required
# def search_api():
#     db = get_db()
#     q = request.args.get('q', '')

#     if q:
#         users = list(db.users.find({'phone': {'$regex': q, '$options': 'i'}}))
#     else:
#         users = list(db.users.find().sort('join_date', -1))

#     result = []
#     for u in users:
#         result.append({
#             'id': str(u['_id']),
#             'name': u.get('name', ''),
#             'phone': u.get('phone', ''),
#             'gender': u.get('gender', ''),
#             'batch': u.get('batch', ''),
#             'plan': u.get('plan', ''),
#             'amount': u.get('amount', 0),
#             'payment_method': u.get('payment_method', 'Cash'),
#             'status': u.get('status', ''),
#             'join_date': u.get('join_date').strftime('%d %b %y') if u.get('join_date') else 'N/A',
#             'expiry': u.get('expiry_date').strftime('%d %b %y') if u.get('expiry_date') else 'N/A' # HTML ke liye zaroori hai
#         })

#     return jsonify(result)

# @admin_bp.route('/admin/edit/<user_id>', methods=['POST'])
# @admin_required
# def edit_user(user_id):
#     db = get_db()
#     db.users.update_one(
#         {'_id': ObjectId(user_id)},
#         {'$set': {
#             'name': request.form.get('name'),
#             'phone': request.form.get('phone'),
#             'address': request.form.get('address'),
#             'status': request.form.get('status')
#         }}
#     )
#     flash('✅ User updated!', 'success')
#     return redirect(url_for('admin.dashboard'))

# @admin_bp.route('/admin/delete/<user_id>')
# @admin_required
# def delete_user(user_id):
#     db = get_db()
#     db.users.delete_one({'_id': ObjectId(user_id)})
#     flash('🗑️ User deleted!', 'success')
#     return redirect(url_for('admin.dashboard'))

# @admin_bp.route('/admin/delete_feedback/<feedback_id>')
# @admin_required
# def delete_feedback(feedback_id):
#     db = get_db()
#     db.feedback.delete_one({'_id': ObjectId(feedback_id)})
#     flash('🗑️ Feedback deleted!', 'success')
#     return redirect(url_for('admin.dashboard') + '#feedbacks')

# @admin_bp.route('/admin/delete_notification/<notif_id>')
# @admin_required
# def delete_notification(notif_id):
#     db = get_db()
#     db.notifications.delete_one({'_id': ObjectId(notif_id)})
#     return redirect(url_for('admin.dashboard'))











from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, Response
from models.database import get_db
from config import ADMIN_PASSWORD
from datetime import datetime
from functools import wraps
from bson import ObjectId
import csv
import io

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

@admin_bp.route('/admin/dashboard')
@admin_required
def dashboard():
    db = get_db()
    
    # Stats
    active_users = db.users.count_documents({'status': 'Active'})
    pending_users = db.users.count_documents({'status': 'Pending'})
    total_users = db.users.count_documents({})
    
    today = datetime.now().strftime('%d %b %Y')
    today_regs = db.users.count_documents({'join_date': {'$gte': datetime.now().replace(hour=0, minute=0, second=0)}})
    
    # Revenue Calculations
    today_revenue = sum(p.get('amount_paid', 0) for p in db.payments.find({'date': today}))
    monthly_revenue = sum(p.get('amount_paid', 0) for p in db.payments.find({'date': {'$regex': f"^{datetime.now().strftime('%b %Y')}"}}))
    pending_payments = db.users.count_documents({'payment_method': 'Online', 'status': 'Pending'})
    completed_payments = db.payments.count_documents({'status': 'SUCCESS'})
    
    users = list(db.users.find().sort('join_date', -1).limit(10))
    payments = list(db.payments.find().sort('date', -1).limit(5))
    feedbacks = list(db.feedback.find().sort('created_at', -1))
    coupons = list(db.coupons.find())

    return render_template('admin_dashboard.html', 
                           active_users=active_users, pending_users=pending_users, total_users=total_users,
                           today_regs=today_regs, today_revenue=today_revenue, monthly_revenue=monthly_revenue,
                           pending_payments=pending_payments, completed_payments=completed_payments,
                           users=users, feedbacks=feedbacks, payments=payments, coupons=coupons)

@admin_bp.route('/admin/add_coupon', methods=['POST'])
@admin_required
def add_coupon():
    db = get_db()
    code = request.form.get('code', '').upper()
    if db.coupons.find_one({'code': code}):
        flash('⚠️ Coupon code already exists!', 'error')
        return redirect(url_for('admin.dashboard') + '#coupons')
        
    db.coupons.insert_one({
        'code': code,
        'type': request.form.get('type'),
        'value': int(request.form.get('value', 0)),
        'max_discount': int(request.form.get('max_discount', 0)),
        'min_amount': int(request.form.get('min_amount', 0)),
        'expiry_date': request.form.get('expiry_date'),
        'max_uses': int(request.form.get('max_uses', 100)),
        'current_uses': 0,
        'is_active': True,
        'description': request.form.get('description', '')
    })
    flash('✅ Coupon added successfully!', 'success')
    return redirect(url_for('admin.dashboard') + '#coupons')

@admin_bp.route('/admin/transactions')
@admin_required
def transactions():
    db = get_db()
    payments = list(db.payments.find().sort('date', -1))
    return render_template('admin_transactions.html', payments=payments)

@admin_bp.route('/admin/search_api')
@admin_required
def search_api():
    db = get_db()
    q = request.args.get('q', '')
    users = list(db.users.find({'phone': {'$regex': q, '$options': 'i'}})) if q else list(db.users.find().sort('join_date', -1))
    result = []
    for u in users:
        result.append({
            'id': str(u['_id']), 'name': u.get('name', ''), 'phone': u.get('phone', ''),
            'gender': u.get('gender', ''), 'batch': u.get('batch', ''), 'plan': u.get('plan', ''),
            'amount': u.get('final_amount', u.get('amount', 0)), 'payment_method': u.get('payment_method', 'Cash'),
            'status': u.get('status', ''),
            'join_date': u.get('join_date').strftime('%d %b %y') if u.get('join_date') else 'N/A'
        })
    return jsonify(result)

@admin_bp.route('/admin/edit/<user_id>', methods=['POST'])
@admin_required
def edit_user(user_id):
    db = get_db()
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {
        'name': request.form.get('name'), 'phone': request.form.get('phone'),
        'address': request.form.get('address'), 'status': request.form.get('status')
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
