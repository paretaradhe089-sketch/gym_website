# from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
# from models.database import get_db
# from datetime import datetime
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from fpdf import FPDF
# import io
# import config
# import razorpay

# main_bp = Blueprint('main', __name__)
# razorpay_client = razorpay.Client(auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET))

# def add_months(source_date, months):
#     new_month = source_date.month - 1 + months
#     new_year = source_date.year + new_month // 12
#     new_month = new_month % 12 + 1
#     return datetime(new_year, new_month, source_date.day)

# @main_bp.route('/')
# def index():
#     db = get_db()
#     active_users = db.users.count_documents({'status': 'Active'})
#     offer = db.offers.find_one({'is_active': True})
#     return render_template('index.html', active_users=active_users, offer=offer, upi_id=config.UPI_ID)

# @main_bp.route('/validate_coupon', methods=['POST'])
# def validate_coupon():
#     data = request.json
#     code = data.get('code', '').upper()
#     amount = int(data.get('amount', 1200))
#     db = get_db()
#     coupon = db.coupons.find_one({'code': code, 'is_active': True})
    
#     if not coupon:
#         return jsonify({'valid': False, 'message': 'Invalid Coupon Code.'})
#     if datetime.strptime(coupon['expiry_date'], '%Y-%m-%d') < datetime.now():
#         return jsonify({'valid': False, 'message': 'Coupon expired.'})
#     if amount < coupon.get('min_amount', 0):
#         return jsonify({'valid': False, 'message': f'Min amount ₹{coupon["min_amount"]} required.'})
        
#     if coupon['type'] == 'percentage':
#         discount = (amount * coupon['value']) / 100
#         if discount > coupon.get('max_discount', 0): discount = coupon['max_discount']
#     else:
#         discount = coupon['value']
        
#     return jsonify({'valid': True, 'discount': discount, 'final_amount': amount - discount, 'message': f'₹{discount} Discount Applied!'})

# @main_bp.route('/create_order', methods=['POST'])
# def create_order():
#     data = request.json
#     amount = int(data.get('final_amount', data.get('amount', 1200))) * 100
#     db = get_db()
    
#     if db.users.find_one({'phone': data.get('phone')}):
#         return jsonify({'error': 'Phone number already registered!'})
        
#     join_date = datetime.strptime(data.get('join_date'), '%Y-%m-%d') if data.get('join_date') else datetime.now()
#     user_data = {
#         'name': data.get('name'), 'phone': data.get('phone'), 'email': data.get('email'),
#         'gender': data.get('gender'), 'batch': data.get('batch'), 'address': data.get('address'),
#         'comment': data.get('comment'), 'plan': data.get('plan'), 
#         'amount': int(data.get('amount', 1200)), 'discount': int(data.get('discount', 0)),
#         'final_amount': int(data.get('final_amount', data.get('amount', 1200))),
#         'coupon_code': data.get('coupon_code', ''),
#         'payment_method': 'Online', 'status': 'Pending',
#         'join_date': join_date,
#         'expiry_date': add_months(join_date, {'Monthly': 1, 'Quarterly': 3, '6 months': 6, 'Yearly': 12}.get(data.get('plan'), 1))
#     }
#     result = db.users.insert_one(user_data)
#     user_id = str(result.inserted_id)
    
#     order = razorpay_client.order.create({
#         'amount': amount, 'currency': 'INR', 'receipt': f'spz_rcpt_{user_id[-8:]}',
#         'notes': {'user_id': user_id, 'name': data.get('name')}
#     })
#     return jsonify({'order_id': order['id'], 'user_id': user_id, 'amount': amount})

# @main_bp.route('/register_cash', methods=['POST'])
# def register_cash():
#     db = get_db()
#     name = request.form.get('name', '').strip()
#     phone = request.form.get('phone', '').strip()
#     if not name or not phone:
#         flash('⚠️ Naam aur Phone zaroori hai!', 'error')
#         return redirect(url_for('main.index'))
#     if db.users.find_one({'phone': phone}):
#         flash('⚠️ Ye phone number already registered hai!', 'error')
#         return redirect(url_for('main.index'))
        
#     join_date = datetime.strptime(request.form.get('join_date'), '%Y-%m-%d') if request.form.get('join_date') else datetime.now()
#     plan = request.form.get('plan', 'Monthly')
#     amount = {'Monthly': 1200, 'Quarterly': 3000, '6 months': 5000, 'Yearly': 8000}.get(plan, 1200)
    
#     user_data = {
#         'name': name, 'phone': phone, 'email': request.form.get('email'), 'gender': request.form.get('gender'),
#         'batch': request.form.get('batch'), 'address': request.form.get('address'), 'comment': request.form.get('comment'), 
#         'plan': plan, 'amount': amount, 'discount': 0, 'final_amount': amount, 'coupon_code': '',
#         'payment_method': 'Cash', 'status': 'Active',
#         'join_date': join_date, 'expiry_date': add_months(join_date, {'Monthly': 1, 'Quarterly': 3, '6 months': 6, 'Yearly': 12}.get(plan, 1))
#     }
#     db.users.insert_one(user_data)
#     flash('✅ Registration Successful! See you at the gym.', 'success')
#     return redirect(url_for('main.index'))

# @main_bp.route('/verify_payment', methods=['POST'])
# def verify_payment():
#     db = get_db()
#     from bson import ObjectId
#     data = request.json
    
#     try:
#         params_dict = {
#             'razorpay_order_id': data.get('razorpay_order_id'),
#             'razorpay_payment_id': data.get('razorpay_payment_id'),
#             'razorpay_signature': data.get('razorpay_signature')
#         }
#         razorpay_client.utility.verify_payment_signature(params_dict)
        
#         payment = razorpay_client.payment.fetch(data.get('razorpay_payment_id'))
#         if payment['status'] == 'captured' or payment['method'] == 'upi':
#             user_id = data.get('user_id')
#             db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'status': 'Active'}})
#             user = db.users.find_one({'_id': ObjectId(user_id)})
            
#             transaction = {
#                 'user_id': user_id, 'name': user.get('name'), 'phone': user.get('phone'),
#                 'email': user.get('email'), 'plan': user.get('plan'), 
#                 'original_amount': user.get('amount', 0), 'discount': user.get('discount', 0),
#                 'amount_paid': user.get('final_amount', 0), 'coupon_used': user.get('coupon_code', ''),
#                 'order_id': data.get('razorpay_order_id'), 'payment_id': data.get('razorpay_payment_id'), 
#                 'transaction_id': data.get('razorpay_payment_id'),
#                 'payment_method': payment['method'], 'status': 'SUCCESS',
#                 'date': datetime.now().strftime('%d %b %Y'), 'time': datetime.now().strftime('%I:%M %p'),
#                 'receipt': f"SFZ{str(user_id)[-6:]}"
#             }
#             db.payments.insert_one(transaction)
#             return jsonify({'status': 'success', 'user_id': user_id})
#         else:
#             return jsonify({'status': 'failed'})
#     except Exception as e:
#         return jsonify({'status': 'failed', 'error': str(e)})

# @main_bp.route('/payment_success/<user_id>')
# def payment_success(user_id):
#     db = get_db()
#     from bson import ObjectId
#     user = db.users.find_one({'_id': ObjectId(user_id)})
#     if not user: return redirect(url_for('main.index'))
#     wa_text = f"Hi Admin! I am {user['name']}. I paid ₹{user['final_amount']} for the {user['plan']} plan. Reg ID: {str(user['_id'])[-8:]}."
#     wa_link = f"https://wa.me/{config.ADMIN_WHATSAPP}?text={wa_text.replace(' ', '%20')}"
#     return render_template('payment_success.html', user=user, wa_link=wa_link, reg_id=user_id)

# @main_bp.route('/download_receipt/<user_id>')
# def download_receipt(user_id):
#     db = get_db()
#     from bson import ObjectId
#     user = db.users.find_one({'_id': ObjectId(user_id)})
#     if not user: return redirect(url_for('main.index'))
#     payment = db.payments.find_one({'user_id': user_id})

#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_fill_color(17, 17, 17)
#     pdf.rect(0, 0, 210, 297, 'F')
    
#     pdf.set_text_color(255, 215, 0); pdf.set_font("Arial", 'B', 28); pdf.cell(0, 15, "SFZ", 0, 1, 'C')
#     pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 14); pdf.cell(0, 10, "Spartan Fitness Zone", 0, 1, 'C')
#     pdf.set_text_color(150, 150, 150); pdf.set_font("Arial", '', 10)
#     pdf.cell(0, 5, "E9 - First Floor, Sharma Colony, Nandpuri, Jaipur | Ph: 8440088703", 0, 1, 'C')
#     pdf.ln(10); pdf.set_text_color(255, 215, 0); pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, "PAYMENT RECEIPT", 0, 1, 'C'); pdf.ln(5)
    
#     pdf.set_font("Arial", '', 12)
#     data = [
#         ("Member Name", user.get('name', '')), ("Registration ID", str(user['_id'])[-8:]),
#         ("Membership Plan", user.get('plan', '')), ("Original Amount", f"Rs. {user.get('amount', 0)}"),
#         ("Discount Applied", f"Rs. {user.get('discount', 0)} ({user.get('coupon_code', 'N/A')})"),
#         ("Amount Paid", f"Rs. {user.get('final_amount', 0)}"),
#         ("Payment Method", payment.get('payment_method', 'N/A').upper() if payment else 'CASH'),
#         ("Transaction ID", payment.get('transaction_id', 'N/A') if payment else 'N/A'),
#         ("Order ID", payment.get('order_id', 'N/A') if payment else 'N/A'),
#         ("Payment ID", payment.get('payment_id', 'N/A') if payment else 'N/A'),
#         ("Payment Date", payment.get('date', datetime.now().strftime('%d %b %Y')) if payment else datetime.now().strftime('%d %b %Y')),
#         ("Payment Time", payment.get('time', datetime.now().strftime('%I:%M %p')) if payment else datetime.now().strftime('%I:%M %p')),
#         ("Payment Status", "SUCCESS" if payment else "PENDING"),
#         ("Expiry Date", user.get('expiry_date').strftime('%d %b %Y') if user.get('expiry_date') else 'N/A')
#     ]
#     for label, value in data:
#         pdf.set_text_color(150, 150, 150); pdf.cell(60, 10, label, 0, 0)
#         pdf.set_text_color(255, 255, 255); pdf.cell(0, 10, ": " + str(value), 0, 1)
        
#     pdf.ln(15); pdf.set_text_color(255, 215, 0); pdf.set_font("Arial", 'B', 12)
#     pdf.cell(0, 10, "Thank You for choosing Spartan Fitness Zone!", 0, 1, 'C')
    
#     buffer = io.BytesIO(); buffer.write(pdf.output()); buffer.seek(0)
#     return send_file(buffer, as_attachment=True, download_name=f"SFZ_Receipt_{user['name']}.pdf", mimetype='application/pdf')

# @main_bp.route('/services')
# def services():
#     services_list = [
#         {'icon': '🏋️', 'title': 'Strength Training', 'desc': 'Build raw power and muscle mass.', 'img': 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800&q=80', 'benefits': ['Increased Muscle Mass', 'Better Bone Density', 'Enhanced Metabolism', 'Improved Posture']},
#         {'icon': '🔥', 'title': 'Weight Loss', 'desc': 'High-intensity routines to shred fat.', 'img': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&q=80', 'benefits': ['Rapid Fat Burn', 'Increased Stamina', 'Core Strengthening', 'Boosted Confidence']},
#         {'icon': '💪', 'title': 'Muscle Building', 'desc': 'Hypertrophy focused training protocols.', 'img': 'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=800&q=80', 'benefits': ['Targeted Muscle Growth', 'Strength Optimization', 'Supplement Guidance', 'Recovery Techniques']},
#         {'icon': '🏃', 'title': 'Cardio Training', 'desc': 'Improve heart health and endurance.', 'img': 'https://images.unsplash.com/photo-1538805060514-97d9cc17730c?w=800&q=80', 'benefits': ['Heart Health', 'Lung Capacity', 'Endurance Boost', 'Stress Relief']},
#         {'icon': '🤼', 'title': 'CrossFit', 'desc': 'High-intensity functional movements.', 'img': 'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=800&q=80', 'benefits': ['Full Body Workout', 'Agility & Speed', 'Community Support', 'Functional Strength']},
#         {'icon': '🧘', 'title': 'Yoga', 'desc': 'Improve flexibility, balance, and mental peace.', 'img': 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=800&q=80', 'benefits': ['Flexibility', 'Mental Peace', 'Injury Prevention', 'Better Breathing']},
#         {'icon': '🏃‍♂️', 'title': 'Functional Training', 'desc': 'Exercises that mimic daily activities.', 'img': 'https://images.unsplash.com/photo-1599058917212-d750089bc07e?w=800&q=80', 'benefits': ['Real-world Strength', 'Balance Improvement', 'Core Stability', 'Mobility']},
#         # Personal Training ki image update kar di gayi hai (aapki di gayi image)
#         {'icon': '👨‍🏫', 'title': 'Personal Training', 'desc': 'One-on-one coaching for targeted results.', 'img': 'https://z-cdn-media.chatglm.cn/files/67013b80-0819-4b84-b2f5-6c33af6d97c9.jpeg?auth_key=1883864928-480f72f92c4e49a4af6a728c8b3a86d9-0-a41eb0623c9cb12304a5c27a5aff36a7', 'benefits': ['Customized Plan', 'Dedicated Attention', 'Faster Results', 'Form Correction']}
#     ]
#     return render_template('services.html', services=services_list)

# @main_bp.route('/contact', methods=['GET', 'POST'])
# def contact():
#     db = get_db()
#     if request.method == 'POST':
#         name = request.form.get('name', '').strip()
#         message = request.form.get('message', '').strip()
#         if not name or not message:
#             flash('⚠️ Naam aur Message zaroori hai!', 'error')
#             return redirect(url_for('main.contact'))
#         db.feedback.insert_one({'name': name, 'email': request.form.get('email'), 'message': message, 'created_at': datetime.now()})
#         flash('✅ Feedback bhej diya! Thank you.', 'success')
#         return redirect(url_for('main.contact'))
#     return render_template('contact.html')












from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from models.database import get_db
from datetime import datetime
from fpdf import FPDF
import io
import config
import razorpay

main_bp = Blueprint('main', __name__)
razorpay_client = razorpay.Client(auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET))

def add_months(source_date, months):
    new_month = source_date.month - 1 + months
    new_year = source_date.year + new_month // 12
    new_month = new_month % 12 + 1
    return datetime(new_year, new_month, source_date.day)

@main_bp.route('/')
def index():
    db = get_db()
    active_users = db.users.count_documents({'status': 'Active'})
    offer = db.offers.find_one({'is_active': True})
    return render_template('index.html', active_users=active_users, offer=offer, upi_id=config.UPI_ID)

@main_bp.route('/validate_coupon', methods=['POST'])
def validate_coupon():
    data = request.json
    code = data.get('code', '').upper()
    amount = int(data.get('amount', 1200))
    db = get_db()
    coupon = db.coupons.find_one({'code': code, 'is_active': True})
    
    if not coupon:
        return jsonify({'valid': False, 'message': 'Invalid Coupon Code.'})
    if datetime.strptime(coupon['expiry_date'], '%Y-%m-%d') < datetime.now():
        return jsonify({'valid': False, 'message': 'Coupon expired.'})
    if amount < coupon.get('min_amount', 0):
        return jsonify({'valid': False, 'message': f'Min amount ₹{coupon["min_amount"]} required.'})
        
    if coupon['type'] == 'percentage':
        discount = (amount * coupon['value']) / 100
        if discount > coupon.get('max_discount', 0): discount = coupon['max_discount']
    else:
        discount = coupon['value']
        
    return jsonify({'valid': True, 'discount': discount, 'final_amount': amount - discount, 'message': f'₹{discount} Discount Applied!'})

@main_bp.route('/create_order', methods=['POST'])
def create_order():
    data = request.json
    amount = int(data.get('final_amount', data.get('amount', 1200))) * 100
    db = get_db()
    
    if db.users.find_one({'phone': data.get('phone')}):
        return jsonify({'error': 'Phone number already registered!'})
        
    join_date = datetime.strptime(data.get('join_date'), '%Y-%m-%d') if data.get('join_date') else datetime.now()
    user_data = {
        'name': data.get('name'), 'phone': data.get('phone'), 'email': data.get('email'),
        'gender': data.get('gender'), 'batch': data.get('batch'), 'address': data.get('address'),
        'comment': data.get('comment'), 'plan': data.get('plan'), 
        'amount': int(data.get('amount', 1200)), 'discount': int(data.get('discount', 0)),
        'final_amount': int(data.get('final_amount', data.get('amount', 1200))),
        'coupon_code': data.get('coupon_code', ''),
        'payment_method': 'Online', 'status': 'Pending',
        'join_date': join_date,
        'expiry_date': add_months(join_date, {'Monthly': 1, 'Quarterly': 3, '6 months': 6, 'Yearly': 12}.get(data.get('plan'), 1))
    }
    result = db.users.insert_one(user_data)
    user_id = str(result.inserted_id)
    
    order = razorpay_client.order.create({
        'amount': amount, 'currency': 'INR', 'receipt': f'spz_rcpt_{user_id[-8:]}',
        'notes': {'user_id': user_id, 'name': data.get('name')}
    })
    return jsonify({'order_id': order['id'], 'user_id': user_id, 'amount': amount})

@main_bp.route('/register_cash', methods=['POST'])
def register_cash():
    db = get_db()
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    if not name or not phone:
        flash('⚠️ Naam aur Phone zaroori hai!', 'error')
        return redirect(url_for('main.index'))
    if db.users.find_one({'phone': phone}):
        flash('⚠️ Ye phone number already registered hai!', 'error')
        return redirect(url_for('main.index'))
        
    join_date = datetime.strptime(request.form.get('join_date'), '%Y-%m-%d') if request.form.get('join_date') else datetime.now()
    plan = request.form.get('plan', 'Monthly')
    amount = {'Monthly': 1200, 'Quarterly': 3000, '6 months': 5000, 'Yearly': 8000}.get(plan, 1200)
    
    user_data = {
        'name': name, 'phone': phone, 'email': request.form.get('email'), 'gender': request.form.get('gender'),
        'batch': request.form.get('batch'), 'address': request.form.get('address'), 'comment': request.form.get('comment'), 
        'plan': plan, 'amount': amount, 'discount': 0, 'final_amount': amount, 'coupon_code': '',
        'payment_method': 'Cash', 'status': 'Active',
        'join_date': join_date, 'expiry_date': add_months(join_date, {'Monthly': 1, 'Quarterly': 3, '6 months': 6, 'Yearly': 12}.get(plan, 1))
    }
    db.users.insert_one(user_data)
    flash('✅ Registration Successful! See you at the gym.', 'success')
    return redirect(url_for('main.index'))

@main_bp.route('/verify_payment', methods=['POST'])
def verify_payment():
    db = get_db()
    from bson import ObjectId
    data = request.json
    
    try:
        params_dict = {
            'razorpay_order_id': data.get('razorpay_order_id'),
            'razorpay_payment_id': data.get('razorpay_payment_id'),
            'razorpay_signature': data.get('razorpay_signature')
        }
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        payment = razorpay_client.payment.fetch(data.get('razorpay_payment_id'))
        if payment['status'] == 'captured' or payment['method'] == 'upi':
            user_id = data.get('user_id')
            db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'status': 'Active'}})
            user = db.users.find_one({'_id': ObjectId(user_id)})
            
            transaction = {
                'user_id': user_id, 'name': user.get('name'), 'phone': user.get('phone'),
                'email': user.get('email'), 'plan': user.get('plan'), 
                'original_amount': user.get('amount', 0), 'discount': user.get('discount', 0),
                'amount_paid': user.get('final_amount', 0), 'coupon_used': user.get('coupon_code', ''),
                'order_id': data.get('razorpay_order_id'), 'payment_id': data.get('razorpay_payment_id'), 
                'transaction_id': data.get('razorpay_payment_id'),
                'payment_method': payment['method'], 'status': 'SUCCESS',
                'date': datetime.now().strftime('%d %b %Y'), 'time': datetime.now().strftime('%I:%M %p'),
                'receipt': f"SFZ{str(user_id)[-6:]}"
            }
            db.payments.insert_one(transaction)
            return jsonify({'status': 'success', 'user_id': user_id})
        else:
            return jsonify({'status': 'failed'})
    except Exception as e:
        return jsonify({'status': 'failed', 'error': str(e)})

@main_bp.route('/payment_success/<user_id>')
def payment_success(user_id):
    db = get_db()
    from bson import ObjectId
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if not user: return redirect(url_for('main.index'))
    wa_text = f"Hi Admin! I am {user['name']}. I paid ₹{user['final_amount']} for the {user['plan']} plan. Reg ID: {str(user['_id'])[-8:]}."
    wa_link = f"https://wa.me/{config.ADMIN_WHATSAPP}?text={wa_text.replace(' ', '%20')}"
    return render_template('payment_success.html', user=user, wa_link=wa_link, reg_id=user_id)

@main_bp.route('/download_receipt/<user_id>')
def download_receipt(user_id):
    db = get_db()
    from bson import ObjectId
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if not user: return redirect(url_for('main.index'))
    payment = db.payments.find_one({'user_id': user_id})

    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(17, 17, 17)
    pdf.rect(0, 0, 210, 297, 'F')
    
    pdf.set_text_color(255, 215, 0); pdf.set_font("Arial", 'B', 28); pdf.cell(0, 15, "SFZ", 0, 1, 'C')
    pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 14); pdf.cell(0, 10, "Spartan Fitness Zone", 0, 1, 'C')
    pdf.set_text_color(150, 150, 150); pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, "E9 - First Floor, Sharma Colony, Nandpuri, Jaipur | Ph: 8440088703", 0, 1, 'C')
    pdf.ln(10); pdf.set_text_color(255, 215, 0); pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, "PAYMENT RECEIPT", 0, 1, 'C'); pdf.ln(5)
    
    pdf.set_font("Arial", '', 12)
    data = [
        ("Member Name", user.get('name', '')), ("Registration ID", str(user['_id'])[-8:]),
        ("Membership Plan", user.get('plan', '')), ("Original Amount", f"Rs. {user.get('amount', 0)}"),
        ("Discount Applied", f"Rs. {user.get('discount', 0)} ({user.get('coupon_code', 'N/A')})"),
        ("Amount Paid", f"Rs. {user.get('final_amount', 0)}"),
        ("Payment Method", payment.get('payment_method', 'N/A').upper() if payment else 'CASH'),
        ("Transaction ID", payment.get('transaction_id', 'N/A') if payment else 'N/A'),
        ("Order ID", payment.get('order_id', 'N/A') if payment else 'N/A'),
        ("Payment ID", payment.get('payment_id', 'N/A') if payment else 'N/A'),
        ("Payment Date", payment.get('date', datetime.now().strftime('%d %b %Y')) if payment else datetime.now().strftime('%d %b %Y')),
        ("Payment Time", payment.get('time', datetime.now().strftime('%I:%M %p')) if payment else datetime.now().strftime('%I:%M %p')),
        ("Payment Status", "SUCCESS" if payment else "PENDING"),
        ("Expiry Date", user.get('expiry_date').strftime('%d %b %Y') if user.get('expiry_date') else 'N/A')
    ]
    for label, value in data:
        pdf.set_text_color(150, 150, 150); pdf.cell(60, 10, label, 0, 0)
        pdf.set_text_color(255, 255, 255); pdf.cell(0, 10, ": " + str(value), 0, 1)
        
    pdf.ln(15); pdf.set_text_color(255, 215, 0); pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Thank You for choosing Spartan Fitness Zone!", 0, 1, 'C')
    
    buffer = io.BytesIO(); buffer.write(pdf.output()); buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"SFZ_Receipt_{user['name']}.pdf", mimetype='application/pdf')

@main_bp.route('/services')
def services():
    services_list = [
        {'icon': '🏋️', 'title': 'Strength Training', 'desc': 'Build raw power and muscle mass.', 'img': 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800&q=80', 'benefits': ['Increased Muscle Mass', 'Better Bone Density', 'Enhanced Metabolism', 'Improved Posture']},
        {'icon': '🔥', 'title': 'Weight Loss', 'desc': 'High-intensity routines to shred fat.', 'img': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&q=80', 'benefits': ['Rapid Fat Burn', 'Increased Stamina', 'Core Strengthening', 'Boosted Confidence']},
        {'icon': '💪', 'title': 'Muscle Building', 'desc': 'Hypertrophy focused training protocols.', 'img': 'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=800&q=80', 'benefits': ['Targeted Muscle Growth', 'Strength Optimization', 'Supplement Guidance', 'Recovery Techniques']},
        {'icon': '🏃', 'title': 'Cardio Training', 'desc': 'Improve heart health and endurance.', 'img': 'https://images.unsplash.com/photo-1538805060514-97d9cc17730c?w=800&q=80', 'benefits': ['Heart Health', 'Lung Capacity', 'Endurance Boost', 'Stress Relief']},
        {'icon': '🤼', 'title': 'CrossFit', 'desc': 'High-intensity functional movements.', 'img': 'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=800&q=80', 'benefits': ['Full Body Workout', 'Agility & Speed', 'Community Support', 'Functional Strength']},
        {'icon': '🧘', 'title': 'Yoga', 'desc': 'Improve flexibility, balance, and mental peace.', 'img': 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=800&q=80', 'benefits': ['Flexibility', 'Mental Peace', 'Injury Prevention', 'Better Breathing']},
        {'icon': '🏃‍♂️', 'title': 'Functional Training', 'desc': 'Exercises that mimic daily activities.', 'img': 'https://images.unsplash.com/photo-1599058917212-d750089bc07e?w=800&q=80', 'benefits': ['Real-world Strength', 'Balance Improvement', 'Core Stability', 'Mobility']},
        {'icon': '👨‍🏫', 'title': 'Personal Training', 'desc': 'One-on-one coaching for targeted results.', 'img': 'https://z-cdn-media.chatglm.cn/files/67013b80-0819-4b84-b2f5-6c33af6d97c9.jpeg?auth_key=1883864928-480f72f92c4e49a4af6a728c8b3a86d9-0-a41eb0623c9cb12304a5c27a5aff36a7', 'benefits': ['Customized Plan', 'Dedicated Attention', 'Faster Results', 'Form Correction']}
    ]
    return render_template('services.html', services=services_list)

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    db = get_db()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        message = request.form.get('message', '').strip()
        if not name or not message:
            flash('⚠️ Naam aur Message zaroori hai!', 'error')
            return redirect(url_for('main.contact'))
        db.feedback.insert_one({'name': name, 'email': request.form.get('email'), 'message': message, 'created_at': datetime.now()})
        flash('✅ Feedback bhej diya! Thank you.', 'success')
        return redirect(url_for('main.contact'))
    return render_template('contact.html')

