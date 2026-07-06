# from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
# from models.database import get_db
# from config import ADMIN_PASSWORD
# from datetime import datetime
# from functools import wraps
# from bson import ObjectId

# admin_bp = Blueprint('admin', __name__)

# def admin_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'admin_logged_in' not in session:
#             return redirect(url_for('admin.admin_login'))
#         return f(*args, **kwargs)
#     return decorated_function

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

# @admin_bp.route('/admin/dashboard')
# @admin_required
# def dashboard():
#     db = get_db()
#     active_users = db.users.count_documents({'status': 'Active'})
#     pending_users = db.users.count_documents({'status': 'Pending'})
#     total_users = db.users.count_documents({})
#     current_month = datetime.now().month
#     current_year = datetime.now().year
#     total_payment = sum(u.get('amount', 0) for u in db.users.find({'join_date': {'$gte': datetime(current_year, current_month, 1)}, 'payment_method': 'Cash'}))
    
#     users = list(db.users.find().sort('join_date', -1))
#     feedbacks = list(db.feedback.find().sort('created_at', -1))

#     # Notifications variable nahi bhej rahe
#     return render_template('admin_dashboard.html', active_users=active_users, pending_users=pending_users, total_payment=total_payment, total_users=total_users, users=users, feedbacks=feedbacks)

# @admin_bp.route('/admin/search_api')
# @admin_required
# def search_api():
#     db = get_db()
#     q = request.args.get('q', '')
#     users = list(db.users.find({'phone': {'$regex': q, '$options': 'i'}})) if q else list(db.users.find().sort('join_date', -1))
#     result = []
#     for u in users:
#         result.append({
#             'id': str(u['_id']), 'name': u.get('name', ''), 'phone': u.get('phone', ''),
#             'gender': u.get('gender', ''), 'batch': u.get('batch', ''), 'plan': u.get('plan', ''),
#             'amount': u.get('amount', 0), 'payment_method': u.get('payment_method', ''),
#             'status': u.get('status', ''),
#             'join_date': u.get('join_date').strftime('%d %b %y') if u.get('join_date') else 'N/A',
#             'expiry': u.get('expiry_date').strftime('%d %b %y') if u.get('expiry_date') else 'N/A'
#         })
#     return jsonify(result)

# @admin_bp.route('/admin/edit/<user_id>', methods=['POST'])
# @admin_required
# def edit_user(user_id):
#     db = get_db()
#     db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {
#         'name': request.form.get('name'), 'phone': request.form.get('phone'),
#         'address': request.form.get('address'), 'status': request.form.get('status')
#     }})
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







from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, Response
from models.database import get_db
from config import ADMIN_PASSWORD
from datetime import datetime
from functools import wraps
from bson import ObjectId
import csv

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
    active_users = db.users.count_documents({'status': 'Active'})
    pending_users = db.users.count_documents({'status': 'Pending'})
    total_users = db.users.count_documents({})
    current_month = datetime.now().month
    current_year = datetime.now().year
    total_payment = sum(u.get('amount', 0) for u in db.users.find({'join_date': {'$gte': datetime(current_year, current_month, 1)}, 'payment_method': 'Cash'}))
    
    users = list(db.users.find().sort('join_date', -1))
    feedbacks = list(db.feedback.find().sort('created_at', -1))

    return render_template('admin_dashboard.html', active_users=active_users, pending_users=pending_users, total_payment=total_payment, total_users=total_users, users=users, feedbacks=feedbacks)

# NEW ROUTE: Payment Transactions
@admin_bp.route('/admin/transactions')
@admin_required
def transactions():
    db = get_db()
    payments = list(db.payments.find().sort('date', -1))
    return render_template('admin_transactions.html', payments=payments)

# NEW ROUTE: Export CSV
@admin_bp.route('/admin/export_csv')
@admin_required
def export_csv():
    db = get_db()
    payments = list(db.payments.find().sort('date', -1))
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Member Name', 'Phone', 'Email', 'Plan', 'Amount', 'Transaction ID', 'Order ID', 'Method', 'Status', 'Date'])
    
    for p in payments:
        writer.writerow([
            p.get('name', ''), p.get('phone', ''), p.get('email', ''), p.get('plan', ''),
            p.get('amount', 0), p.get('transaction_id', ''), p.get('order_id', ''),
            p.get('payment_method', ''), p.get('status', ''), p.get('date').strftime('%d %b %Y')
        ])
        
    output.seek(0)
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=SFZ_Transactions.csv"})

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
            'amount': u.get('amount', 0), 'payment_method': u.get('payment_method', ''),
            'status': u.get('status', ''),
            'join_date': u.get('join_date').strftime('%d %b %y') if u.get('join_date') else 'N/A',
            'expiry': u.get('expiry_date').strftime('%d %b %y') if u.get('expiry_date') else 'N/A'
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

# Need to import io for CSV
import io
