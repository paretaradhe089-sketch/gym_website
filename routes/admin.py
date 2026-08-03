
# from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, Response
# from models.database import get_db
# from config import ADMIN_PASSWORD, MAIL_EMAIL, WEB3FORMS_KEY
# from datetime import datetime, timedelta
# from functools import wraps
# from bson import ObjectId
# import csv
# import io
# import requests
# import pytz
# from apscheduler.schedulers.background import BackgroundScheduler

# admin_bp = Blueprint('admin', __name__)

# def admin_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'admin_logged_in' not in session:
#             return redirect(url_for('admin.admin_login'))
#         return f(*args, **kwargs)
#     return decorated_function

# # === EMAIL FUNCTION (FormSubmit API - No Key Needed) ===
# # === EMAIL FUNCTION (Resend API) ===
# def send_admin_email(subject, body):
#     if not WEB3FORMS_KEY or WEB3FORMS_KEY == 'default-key':
#         print("--- DEBUG: Web3Forms Key missing ---")
#         return False
        
#     url = "https://api.resend.com/emails"
#     headers = {
#         "Authorization": f"Bearer {RESEND_API_KEY}",
#         "Content-Type": "application/json"
#     }
#     payload = {
#         "from": "Spartan Fitness Zone <onboarding@resend.dev>",
#         "to": [MAIL_EMAIL],
#         "subject": subject,
#         "html": body
#     }
    
#     try:
#         print("--- DEBUG: Sending Expiry email via Resend... ---")
#         response = requests.post(url, json=payload, headers=headers, timeout=10)
#         if response.status_code == 200:
#             print("--- DEBUG: Expiry Email sent successfully! ---")
#             return True
#         else:
#             print(f"--- DEBUG: API Error: {response.text} ---")
#             return False
#     except Exception as e:
#         print(f"--- DEBUG: Request Error: {e} ---")
#         return False

# # === APSCHEDULER FUNCTION (Runs Daily at 9 AM) ===
# def check_expired_users():
#     db = get_db()
#     today = datetime.now()
#     today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    
#     users = db.users.find({"status": "Active"})
#     for user in users:
#         expiry = user.get('expiry_date')
#         if not expiry: continue
            
#         if isinstance(expiry, str):
#             try: expiry = datetime.strptime(expiry, '%d-%m-%Y')
#             except: continue
                
#         if expiry <= today:
#             existing_notif = db.notifications.find_one({
#                 'phone': user['phone'], 
#                 'status': 'pending'
#             })
            
#             if not existing_notif:
#                 db.notifications.insert_one({
#                     'name': user.get('name', ''),
#                     'phone': user.get('phone', ''),
#                     'shift': user.get('batch', 'N/A'),
#                     'type': 'EXPIRED',
#                     'expiry_date': expiry,
#                     'status': 'pending',
#                     'created_at': datetime.now()
#                 })
                
#                 subject = "⚠️ Membership Expired!"
#                 body = f"""
#                 <h3>User Membership Expired!</h3>
#                 <p>Ek user ka gym membership expire ho gaya hai. Please contact karke renew karwayein.</p>
#                 <table style="border: 1px solid #ddd; padding: 10px;">
#                     <tr><td><b>Name:</b></td><td>{user.get('name', '')}</td></tr>
#                     <tr><td><b>Phone:</b></td><td>{user.get('phone', '')}</td></tr>
#                     <tr><td><b>Shift:</b></td><td>{user.get('batch', 'N/A')}</td></tr>
#                     <tr><td><b>Expiry Date:</b></td><td>{expiry.strftime('%d %b %Y')}</td></tr>
#                 </table>
#                 """
#                 send_admin_email(subject, body)
#                 print(f"⚠️ EXPIRED Email sent to admin for {user['name']}")

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
    
#     # Also run check manually when admin opens dashboard (fallback for Render sleep)
#     check_expired_users()
    
#     active_users = db.users.count_documents({'status': 'Active'})
#     pending_users = db.users.count_documents({'status': 'Pending'})
#     total_users = db.users.count_documents({})
#     today = datetime.now().strftime('%d %b %Y')
#     today_regs = db.users.count_documents({'join_date': {'$gte': datetime.now().replace(hour=0, minute=0, second=0)}})
#     today_revenue = sum(p.get('amount_paid', 0) for p in db.payments.find({'date': today}))
    
#     # Monthly Revenue Calculation
#     monthly_rev_data = {}
#     for p in db.payments.find({'status': 'SUCCESS'}):
#         try:
#             dt = datetime.strptime(p['date'], '%d %b %Y')
#             key = dt.strftime('%Y-%m')
#             monthly_rev_data[key] = monthly_rev_data.get(key, 0) + p.get('amount_paid', 0)
#         except:
#             pass
#     sorted_monthly_rev = sorted(monthly_rev_data.items(), reverse=True)[:6] # Last 6 months
    
#     pending_payments = db.users.count_documents({'payment_method': 'Online', 'status': 'Pending'})
#     completed_payments = db.payments.count_documents({'status': 'SUCCESS'})
    
#     users = list(db.users.find().sort('join_date', -1).limit(10))
#     payments = list(db.payments.find().sort('date', -1).limit(5))
#     feedbacks = list(db.feedback.find().sort('created_at', -1))
#     coupons = list(db.coupons.find())
    
#     # Fetch Pending Notifications
#     notifications = list(db.notifications.find({'status': 'pending'}).sort('created_at', -1))

#     return render_template('admin_dashboard.html', active_users=active_users, pending_users=pending_users, total_users=total_users,
#                            today_regs=today_regs, today_revenue=today_revenue,
#                            pending_payments=pending_payments, completed_payments=completed_payments,
#                            users=users, feedbacks=feedbacks, payments=payments, coupons=coupons,
#                            notifications=notifications, monthly_rev=sorted_monthly_rev)

# # NOTIFICATION ACTIONS
# @admin_bp.route('/admin/dismiss_notif/<notif_id>')
# @admin_required
# def dismiss_notif(notif_id):
#     db = get_db()
#     db.notifications.update_one({'_id': ObjectId(notif_id)}, {'$set': {'status': 'dismissed'}})
#     flash('✅ Notification dismissed.', 'success')
#     return redirect(url_for('admin.dashboard') + '#alerts')

# @admin_bp.route('/admin/payment_received_notif/<notif_id>')
# @admin_required
# def payment_received_notif(notif_id):
#     db = get_db()
#     notif = db.notifications.find_one({'_id': ObjectId(notif_id)})
#     if notif:
#         user = db.users.find_one({'phone': notif['phone']})
#         if user:
#             # Extend Expiry by 1 Month
#             current_expiry = user.get('expiry_date', datetime.now())
#             if isinstance(current_expiry, str):
#                 current_expiry = datetime.now()
#             new_expiry = current_expiry.replace(month=current_expiry.month % 12 + 1, year=current_expiry.year + (1 if current_expiry.month == 12 else 0))
#             db.users.update_one({'_id': user['_id']}, {'$set': {'expiry_date': new_expiry, 'status': 'Active'}})
            
#             # Dismiss Notification
#             db.notifications.update_one({'_id': ObjectId(notif_id)}, {'$set': {'status': 'resolved'}})
#             flash('✅ Membership renewed for 1 month!', 'success')
#     return redirect(url_for('admin.dashboard') + '#alerts')

# @admin_bp.route('/admin/add_coupon', methods=['POST'])
# @admin_required
# def add_coupon():
#     db = get_db()
#     code = request.form.get('code', '').upper()
#     if db.coupons.find_one({'code': code}):
#         flash('⚠️ Coupon code already exists!', 'error')
#         return redirect(url_for('admin.dashboard') + '#coupons')
#     db.coupons.insert_one({
#         'code': code, 'type': request.form.get('type'), 'value': int(request.form.get('value', 0)),
#         'max_discount': int(request.form.get('max_discount', 0)), 'min_amount': int(request.form.get('min_amount', 0)),
#         'expiry_date': request.form.get('expiry_date'), 'max_uses': int(request.form.get('max_uses', 100)),
#         'current_uses': 0, 'is_active': True, 'description': request.form.get('description', '')
#     })
#     flash('✅ Coupon added successfully!', 'success')
#     return redirect(url_for('admin.dashboard') + '#coupons')

# @admin_bp.route('/admin/transactions')
# @admin_required
# def transactions():
#     db = get_db()
#     q = request.args.get('q', '')
#     query = {}
#     if q:
#         query = {
#             '$or': [
#                 {'name': {'$regex': q, '$options': 'i'}},
#                 {'receipt': {'$regex': q, '$options': 'i'}},
#                 {'transaction_id': {'$regex': q, '$options': 'i'}}
#             ]
#         }
#     payments = list(db.payments.find(query).sort('date', -1))
#     return render_template('admin_transactions.html', payments=payments, q=q)

# @admin_bp.route('/admin/export_csv')
# @admin_required
# def export_csv():
#     db = get_db()
#     payments = list(db.payments.find().sort('date', -1))
#     output = io.StringIO()
#     writer = csv.writer(output)
#     writer.writerow(['Member Name', 'Phone', 'Email', 'Plan', 'Amount', 'Transaction ID', 'Order ID', 'Method', 'Status', 'Date'])
#     for p in payments:
#         writer.writerow([p.get('name', ''), p.get('phone', ''), p.get('email', ''), p.get('plan', ''), p.get('amount_paid', 0), p.get('transaction_id', ''), p.get('order_id', ''), p.get('payment_method', ''), p.get('status', ''), p.get('date', '')])
#     output.seek(0)
#     return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=SFZ_Transactions.csv"})

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
#             'amount': u.get('final_amount', u.get('amount', 0)), 'payment_method': u.get('payment_method', 'Cash'),
#             'status': u.get('status', ''), 'join_date': u.get('join_date').strftime('%d %b %y') if u.get('join_date') else 'N/A'
#         })
#     return jsonify(result)

# @admin_bp.route('/admin/edit/<user_id>', methods=['POST'])
# @admin_required
# def edit_user(user_id):
#     db = get_db()
#     db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'name': request.form.get('name'), 'phone': request.form.get('phone'), 'address': request.form.get('address'), 'status': request.form.get('status')}})
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

# # ==========================================
# # SCHEDULER START FUNCTION (To be called in app.py)
# # ==========================================
# def start_scheduler(app):
#     scheduler = BackgroundScheduler()
#     # 9:00 AM IST = 3:30 AM UTC
#     scheduler.add_job(func=check_expired_users, trigger="cron", hour=3, minute=30, timezone='UTC')
#     scheduler.start()
#     app.logger.info("APScheduler started successfully.")
















from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, Response
from models.database import get_db
from config import ADMIN_PASSWORD, MAIL_EMAIL, RESEND_API_KEY
from datetime import datetime, timedelta
from functools import wraps
from bson import ObjectId
import csv
import io
import requests
import pytz
from apscheduler.schedulers.background import BackgroundScheduler

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# === EMAIL FUNCTION (Resend API) ===
def send_admin_email(subject, body):
    if not RESEND_API_KEY:
        print("--- DEBUG: Resend API Key missing ---")
        return False
        
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": "Spartan Fitness Zone <onboarding@resend.dev>",
        "to": [MAIL_EMAIL],
        "subject": subject,
        "html": body
    }
    
    try:
        print("--- DEBUG: Sending Expiry email via Resend... ---")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            print("--- DEBUG: Expiry Email sent successfully! ---")
            return True
        else:
            print(f"--- DEBUG: API Error: {response.text} ---")
            return False
    except Exception as e:
        print(f"--- DEBUG: Request Error: {e} ---")
        return False

# === APSCHEDULER FUNCTION (Runs Daily at 9 AM) ===
def check_expired_users():
    db = get_db()
    today = datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    
    users = db.users.find({"status": "Active"})
    for user in users:
        expiry = user.get('expiry_date')
        if not expiry: continue
            
        if isinstance(expiry, str):
            try: expiry = datetime.strptime(expiry, '%d-%m-%Y')
            except: continue
                
        if expiry <= today:
            existing_notif = db.notifications.find_one({
                'phone': user['phone'], 
                'status': 'pending'
            })
            
            if not existing_notif:
                db.notifications.insert_one({
                    'name': user.get('name', ''),
                    'phone': user.get('phone', ''),
                    'shift': user.get('batch', 'N/A'),
                    'type': 'EXPIRED',
                    'expiry_date': expiry,
                    'status': 'pending',
                    'created_at': datetime.now()
                })
                
                subject = "⚠️ Membership Expired!"
                body = f"""
                <h3>User Membership Expired!</h3>
                <p>Ek user ka gym membership expire ho gaya hai. Please contact karke renew karwayein.</p>
                <table style="border: 1px solid #ddd; padding: 10px;">
                    <tr><td><b>Name:</b></td><td>{user.get('name', '')}</td></tr>
                    <tr><td><b>Phone:</b></td><td>{user.get('phone', '')}</td></tr>
                    <tr><td><b>Shift:</b></td><td>{user.get('batch', 'N/A')}</td></tr>
                    <tr><td><b>Expiry Date:</b></td><td>{expiry.strftime('%d %b %Y')}</td></tr>
                </table>
                """
                send_admin_email(subject, body)
                print(f"⚠️ EXPIRED Email sent to admin for {user['name']}")

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
    
    # Also run check manually when admin opens dashboard (fallback for Render sleep)
    check_expired_users()
    
    active_users = db.users.count_documents({'status': 'Active'})
    pending_users = db.users.count_documents({'status': 'Pending'})
    total_users = db.users.count_documents({})
    today = datetime.now().strftime('%d %b %Y')
    today_regs = db.users.count_documents({'join_date': {'$gte': datetime.now().replace(hour=0, minute=0, second=0)}})
    today_revenue = sum(p.get('amount_paid', 0) for p in db.payments.find({'date': today}))
    
    # Monthly Revenue Calculation
    monthly_rev_data = {}
    for p in db.payments.find({'status': 'SUCCESS'}):
        try:
            dt = datetime.strptime(p['date'], '%d %b %Y')
            key = dt.strftime('%Y-%m')
            monthly_rev_data[key] = monthly_rev_data.get(key, 0) + p.get('amount_paid', 0)
        except:
            pass
    sorted_monthly_rev = sorted(monthly_rev_data.items(), reverse=True)[:6] # Last 6 months
    
    pending_payments = db.users.count_documents({'payment_method': 'Online', 'status': 'Pending'})
    completed_payments = db.payments.count_documents({'status': 'SUCCESS'})
    
    users = list(db.users.find().sort('join_date', -1).limit(10))
    payments = list(db.payments.find().sort('date', -1).limit(5))
    feedbacks = list(db.feedback.find().sort('created_at', -1))
    coupons = list(db.coupons.find())
    
    # Fetch Pending Notifications
    notifications = list(db.notifications.find({'status': 'pending'}).sort('created_at', -1))

    return render_template('admin_dashboard.html', active_users=active_users, pending_users=pending_users, total_users=total_users,
                           today_regs=today_regs, today_revenue=today_revenue,
                           pending_payments=pending_payments, completed_payments=completed_payments,
                           users=users, feedbacks=feedbacks, payments=payments, coupons=coupons,
                           notifications=notifications, monthly_rev=sorted_monthly_rev)

# NOTIFICATION ACTIONS
@admin_bp.route('/admin/dismiss_notif/<notif_id>')
@admin_required
def dismiss_notif(notif_id):
    db = get_db()
    db.notifications.update_one({'_id': ObjectId(notif_id)}, {'$set': {'status': 'dismissed'}})
    flash('✅ Notification dismissed.', 'success')
    return redirect(url_for('admin.dashboard') + '#alerts')

@admin_bp.route('/admin/payment_received_notif/<notif_id>')
@admin_required
def payment_received_notif(notif_id):
    db = get_db()
    notif = db.notifications.find_one({'_id': ObjectId(notif_id)})
    if notif:
        user = db.users.find_one({'phone': notif['phone']})
        if user:
            # Extend Expiry by 1 Month
            current_expiry = user.get('expiry_date', datetime.now())
            if isinstance(current_expiry, str):
                current_expiry = datetime.now()
            new_expiry = current_expiry.replace(month=current_expiry.month % 12 + 1, year=current_expiry.year + (1 if current_expiry.month == 12 else 0))
            db.users.update_one({'_id': user['_id']}, {'$set': {'expiry_date': new_expiry, 'status': 'Active'}})
            
            # Dismiss Notification
            db.notifications.update_one({'_id': ObjectId(notif_id)}, {'$set': {'status': 'resolved'}})
            flash('✅ Membership renewed for 1 month!', 'success')
    return redirect(url_for('admin.dashboard') + '#alerts')

@admin_bp.route('/admin/add_coupon', methods=['POST'])
@admin_required
def add_coupon():
    db = get_db()
    code = request.form.get('code', '').upper()
    if db.coupons.find_one({'code': code}):
        flash('⚠️ Coupon code already exists!', 'error')
        return redirect(url_for('admin.dashboard') + '#coupons')
    db.coupons.insert_one({
        'code': code, 'type': request.form.get('type'), 'value': int(request.form.get('value', 0)),
        'max_discount': int(request.form.get('max_discount', 0)), 'min_amount': int(request.form.get('min_amount', 0)),
        'expiry_date': request.form.get('expiry_date'), 'max_uses': int(request.form.get('max_uses', 100)),
        'current_uses': 0, 'is_active': True, 'description': request.form.get('description', '')
    })
    flash('✅ Coupon added successfully!', 'success')
    return redirect(url_for('admin.dashboard') + '#coupons')

@admin_bp.route('/admin/transactions')
@admin_required
def transactions():
    db = get_db()
    q = request.args.get('q', '')
    query = {}
    if q:
        query = {
            '$or': [
                {'name': {'$regex': q, '$options': 'i'}},
                {'receipt': {'$regex': q, '$options': 'i'}},
                {'transaction_id': {'$regex': q, '$options': 'i'}}
            ]
        }
    payments = list(db.payments.find(query).sort('date', -1))
    return render_template('admin_transactions.html', payments=payments, q=q)

@admin_bp.route('/admin/export_csv')
@admin_required
def export_csv():
    db = get_db()
    payments = list(db.payments.find().sort('date', -1))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Member Name', 'Phone', 'Email', 'Plan', 'Amount', 'Transaction ID', 'Order ID', 'Method', 'Status', 'Date'])
    for p in payments:
        writer.writerow([p.get('name', ''), p.get('phone', ''), p.get('email', ''), p.get('plan', ''), p.get('amount_paid', 0), p.get('transaction_id', ''), p.get('order_id', ''), p.get('payment_method', ''), p.get('status', ''), p.get('date', '')])
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
            'amount': u.get('final_amount', u.get('amount', 0)), 'payment_method': u.get('payment_method', 'Cash'),
            'status': u.get('status', ''), 'join_date': u.get('join_date').strftime('%d %b %y') if u.get('join_date') else 'N/A'
        })
    return jsonify(result)

@admin_bp.route('/admin/edit/<user_id>', methods=['POST'])
@admin_required
def edit_user(user_id):
    db = get_db()
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'name': request.form.get('name'), 'phone': request.form.get('phone'), 'address': request.form.get('address'), 'status': request.form.get('status')}})
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

# ==========================================
# SCHEDULER START FUNCTION (To be called in app.py)
# ==========================================
def start_scheduler(app):
    scheduler = BackgroundScheduler()
    # 9:00 AM IST = 3:30 AM UTC
    scheduler.add_job(func=check_expired_users, trigger="cron", hour=3, minute=30, timezone='UTC')
    scheduler.start()
    app.logger.info("APScheduler started successfully.")