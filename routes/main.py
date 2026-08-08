# from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
# from models.database import get_db
# from datetime import datetime
# from fpdf import FPDF
# import io
# import urllib.request
# import qrcode
# import config
# import razorpay
# import threading 
# import requests  # Web3Forms API ke liye

# main_bp = Blueprint('main', __name__)
# razorpay_client = razorpay.Client(auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET))


# # === EMAIL FUNCTION (Resend API - 100% Working on Render) ===
# def send_admin_email(subject, body):
#     if not config.RESEND_API_KEY:
#         print("--- DEBUG: Resend API Key missing ---")
#         return False
        
#     url = "https://api.resend.com/emails"
#     headers = {
#         "Authorization": f"Bearer {config.RESEND_API_KEY}",
#         "Content-Type": "application/json"
#     }
#     payload = {
#         "from": "Spartan Fitness Zone <onboarding@resend.dev>",
#         "to": [config.MAIL_EMAIL], # Ye aapki Gmail hai jisme email aayegi
#         "subject": subject,
#         "html": body
#     }
    
#     try:
#         print("--- DEBUG: Sending email via Resend API... ---")
#         response = requests.post(url, json=payload, headers=headers, timeout=10)
#         if response.status_code == 200:
#             print("--- DEBUG: Email sent successfully via Resend! ---")
#             return True
#         else:
#             print(f"--- DEBUG: API Error: {response.text} ---")
#             return False
#     except Exception as e:
#         print(f"--- DEBUG: Request Error: {e} ---")
#         return False

# # === BACKGROUND THREAD FUNCTION ===
# def send_email_async(subject, body):
#     """Email ko background mein bhejne ke liye, taaki website slow na ho"""
#     thread = threading.Thread(target=send_admin_email, args=(subject, body))
#     thread.daemon = True
#     thread.start()

# def add_months(source_date, months):
#     new_month = source_date.month - 1 + months
#     new_year = source_date.year + new_month // 12
#     new_month = new_month % 12 + 1
#     return datetime(new_year, new_month, source_date.day)

# def get_upi_app(vpa):
#     if not vpa: return "N/A"
#     if '@ybl' in vpa or '@apl' in vpa: return 'PhonePe'
#     if '@ok' in vpa or '@oksbi' in vpa: return 'Google Pay'
#     if '@paytm' in vpa: return 'Paytm'
#     return 'UPI'

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
    
#     if not coupon: return jsonify({'valid': False, 'message': 'Invalid Coupon Code.'})
#     if datetime.strptime(coupon['expiry_date'], '%Y-%m-%d') < datetime.now(): return jsonify({'valid': False, 'message': 'Coupon expired.'})
#     if amount < coupon.get('min_amount', 0): return jsonify({'valid': False, 'message': f'Min amount ₹{coupon["min_amount"]} required.'})
        
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
    
#     if db.users.find_one({'phone': data.get('phone')}): return jsonify({'error': 'Phone number already registered!'})
        
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
    
#     # BACKGROUND EMAIL ALERT
#     # send_email_async("🆕 New Online Registration Pending!", f"<h3>New User Registered (Online Pending)</h3><p><b>Name:</b> {user_data['name']}<br><b>Phone:</b> {user_data['phone']}<br><b>Plan:</b> {user_data['plan']}</p>")
#     # BACKGROUND EMAIL ALERT
#     send_email_async("🆕 New Online Registration Pending!", f"<h3>New User Registered (Online Pending)</h3><p><b>Name:</b> {user_data['name']}<br><b>Phone:</b> {user_data['phone']}<br><b>Plan:</b> {user_data['plan']}<br><b>Amount:</b> ₹{user_data['final_amount']}</p>")
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
    
#     # BACKGROUND EMAIL ALERT
#     send_email_async("💰 New Cash Registration!", f"<h3>New User Registered (Cash)</h3><p><b>Name:</b> {name}<br><b>Phone:</b> {phone}<br><b>Plan:</b> {plan}<br><b>Amount:</b> ₹{amount}</p>")
    
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
#                 'payment_method': payment['method'], 'upi_app': get_upi_app(payment.get('vpa', '')), 'vpa': payment.get('vpa', 'N/A'),
#                 'status': 'SUCCESS',
#                 'date': datetime.now().strftime('%d %b %Y'), 'time': datetime.now().strftime('%I:%M %p'),
#                 'receipt': f"SFZ{str(user_id)[-6:]}"
#             }
#             db.payments.insert_one(transaction)
            
#             # BACKGROUND EMAIL ALERT
#             #send_email_async("✅ Payment Received!", f"<h3>Online Payment Successful</h3><p><b>Name:</b> {user.get('name')}<br><b>Amount:</b> ₹{user.get('final_amount')}<br><b>Plan:</b> {user.get('plan')}</p>")
#                         # BACKGROUND EMAIL ALERT
#             upi_app_name = get_upi_app(payment.get('vpa', ''))
#             send_email_async("✅ Payment Received!", f"<h3>Online Payment Successful</h3><p><b>Name:</b> {user.get('name')}<br><b>Amount:</b> ₹{user.get('final_amount')}<br><b>Plan:</b> {user.get('plan')}<br><b>Payment App:</b> {upi_app_name}<br><b>Transaction ID:</b> {payment.get('transaction_id', 'N/A')}</p>")
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

#     receipt_no = f"SFZ{str(user['_id'])[-6:]}"
#     invoice_no = f"INV-2024-{str(user['_id'])[-4:]}"

#     qr = qrcode.QRCode(version=1, box_size=4, border=1)
#     qr.add_data(f"Receipt No: {receipt_no}, Name: {user.get('name')}, Amount: Rs. {user.get('final_amount', 0)}")
#     qr.make(fit=True)
#     qr_img = qr.make_image(fill_color="black", back_color="white")
#     img_byte_arr = io.BytesIO()
#     qr_img.save(img_byte_arr, format='PNG')
#     img_byte_arr.seek(0)

#     pdf = FPDF(orientation='P', unit='mm', format='A4')
#     pdf.add_page()
#     pdf.set_auto_page_break(auto=True, margin=15)

#     pdf.set_fill_color(17, 17, 17)
#     pdf.rect(0, 0, 210, 40, 'F')

#     logo_url = "https://z-cdn-media.chatglm.cn/files/66dfb45d-eb25-46d5-87a9-2f527f8758cf.jpeg?auth_key=1883997017-3faf8b3e4e594a43b060a3bc21b1c3e2-0-799070c3fe3307a0f0a85b395b3404df"
#     try:
#         with urllib.request.urlopen(logo_url, timeout=5) as response:
#             logo_data = io.BytesIO(response.read())
#             pdf.image(logo_data, x=10, y=8, w=20)
#     except:
#         pass

#     pdf.set_xy(35, 10)
#     pdf.set_text_color(255, 215, 0)
#     pdf.set_font("Arial", 'B', 16)
#     pdf.cell(0, 8, config.GYM_NAME, 0, 1)

#     pdf.set_xy(35, 18)
#     pdf.set_text_color(255, 255, 255)
#     pdf.set_font("Arial", '', 8)
#     pdf.multi_cell(80, 4, f"{config.GYM_ADDRESS}\nPhone: {config.GYM_PHONE} | Email: {config.GYM_EMAIL}\nWebsite: {config.GYM_WEBSITE}")

#     pdf.set_xy(130, 10)
#     pdf.set_text_color(255, 255, 255)
#     pdf.set_font("Arial", 'B', 10)
#     pdf.cell(70, 5, "PAYMENT RECEIPT", 0, 1, 'R')
#     pdf.set_font("Arial", '', 8)
#     pdf.set_xy(130, 16)
#     pdf.cell(70, 4, f"Receipt No: {receipt_no}", 0, 1, 'R')
#     pdf.set_xy(130, 20)
#     pdf.cell(70, 4, f"Invoice No: {invoice_no}", 0, 1, 'R')
#     pdf.set_xy(130, 24)
#     pdf.cell(70, 4, f"Date: {datetime.now().strftime('%d %b %Y %I:%M %p')}", 0, 1, 'R')
#     pdf.set_xy(130, 28)
#     pdf.set_text_color(46, 204, 113)
#     pdf.set_font("Arial", 'B', 8)
#     pdf.cell(70, 4, "Status: SUCCESS", 0, 1, 'R')

#     pdf.ln(10)

#     pdf.set_text_color(17, 17, 17)
#     pdf.set_font("Arial", 'B', 10)
#     pdf.set_fill_color(255, 215, 0)
#     pdf.cell(95, 7, " MEMBER DETAILS", 1, 0, 'L', True)
#     pdf.cell(95, 7, " MEMBERSHIP DETAILS", 1, 1, 'L', True)

#     pdf.set_font("Arial", '', 9)
#     pdf.set_fill_color(245, 245, 245)
#     pdf.cell(40, 6, " Member Name:", 1, 0, 'L', True)
#     pdf.cell(55, 6, f" {user.get('name', '')}", 1, 0, 'L')
#     pdf.cell(40, 6, " Plan Name:", 1, 0, 'L', True)
#     pdf.cell(55, 6, f" {user.get('plan', '')}", 1, 1, 'L')

#     pdf.cell(40, 6, " Mobile:", 1, 0, 'L', True)
#     pdf.cell(55, 6, f" {user.get('phone', '')}", 1, 0, 'L')
#     pdf.cell(40, 6, " Start Date:", 1, 0, 'L', True)
#     pdf.cell(55, 6, f" {user.get('join_date').strftime('%d %b %Y')}", 1, 1, 'L')

#     pdf.cell(40, 6, " Email:", 1, 0, 'L', True)
#     pdf.cell(55, 6, f" {user.get('email', 'N/A')}", 1, 0, 'L')
#     pdf.cell(40, 6, " Expiry Date:", 1, 0, 'L', True)
#     pdf.cell(55, 6, f" {user.get('expiry_date').strftime('%d %b %Y')}", 1, 1, 'L')

#     pdf.cell(40, 6, " Member ID:", 1, 0, 'L', True)
#     pdf.cell(55, 6, f" {str(user['_id'])[-8:]}", 1, 0, 'L')
#     pdf.cell(40, 6, " Duration:", 1, 0, 'L', True)
#     pdf.cell(55, 6, f" {user.get('plan', '')}", 1, 1, 'L')

#     pdf.ln(5)

#     pdf.set_font("Arial", 'B', 10)
#     pdf.set_fill_color(255, 215, 0)
#     pdf.cell(0, 7, " PAYMENT DETAILS", 1, 1, 'L', True)

#     pdf.set_font("Arial", '', 9)
#     pdf.set_fill_color(245, 245, 245)
#     pdf.cell(50, 6, " Payment Gateway:", 1, 0, 'L', True)
#     pdf.cell(40, 6, " Razorpay", 1, 0, 'L')
#     pdf.cell(40, 6, " Payment Method:", 1, 0, 'L', True)
#     pdf.cell(60, 6, f" {payment.get('payment_method', 'N/A').upper()}", 1, 1, 'L')

#     pdf.cell(50, 6, " UPI App Used:", 1, 0, 'L', True)
#     pdf.cell(40, 6, f" {payment.get('upi_app', 'N/A')}", 1, 0, 'L')
#     pdf.cell(40, 6, " Transaction ID:", 1, 0, 'L', True)
#     pdf.cell(60, 6, f" {payment.get('transaction_id', 'N/A')}", 1, 1, 'L')

#     pdf.cell(50, 6, " Razorpay Order ID:", 1, 0, 'L', True)
#     pdf.cell(140, 6, f" {payment.get('order_id', 'N/A')}", 1, 1, 'L')

#     pdf.cell(50, 6, " Razorpay Payment ID:", 1, 0, 'L', True)
#     pdf.cell(140, 6, f" {payment.get('payment_id', 'N/A')}", 1, 1, 'L')

#     pdf.cell(50, 6, " Payment Date/Time:", 1, 0, 'L', True)
#     pdf.cell(140, 6, f" {payment.get('date', '')} {payment.get('time', '')}", 1, 1, 'L')

#     pdf.ln(5)

#     pdf.set_font("Arial", 'B', 10)
#     pdf.set_fill_color(255, 215, 0)
#     pdf.cell(0, 7, " PAYMENT SUMMARY", 1, 1, 'L', True)

#     pdf.set_font("Arial", '', 10)
#     pdf.set_fill_color(245, 245, 245)
#     pdf.cell(120, 7, " Membership Fee", 1, 0, 'R', True)
#     pdf.cell(70, 7, f" Rs. {user.get('amount', 0)}", 1, 1, 'L')

#     pdf.cell(120, 7, " Discount", 1, 0, 'R', True)
#     pdf.cell(70, 7, f" - Rs. {user.get('discount', 0)}", 1, 1, 'L')

#     pdf.cell(120, 7, " Taxes", 1, 0, 'R', True)
#     pdf.cell(70, 7, " Rs. 0", 1, 1, 'L')

#     pdf.set_font("Arial", 'B', 12)
#     pdf.set_fill_color(17, 17, 17)
#     pdf.set_text_color(255, 215, 0)
#     pdf.cell(120, 8, " TOTAL AMOUNT PAID", 1, 0, 'R', True)
#     pdf.cell(70, 8, f" Rs. {user.get('final_amount', 0)}", 1, 1, 'L', True)
#     pdf.set_text_color(17, 17, 17)

#     pdf.ln(5)
#     pdf.image(img_byte_arr, x=85, y=None, w=30)
#     pdf.set_font("Arial", '', 8)
#     pdf.set_text_color(100)
#     pdf.cell(0, 5, "Scan to verify receipt", 0, 1, 'C')

#     pdf.ln(5)
#     pdf.set_y(-50)
#     pdf.set_text_color(100)
#     pdf.set_font("Arial", 'I', 8)
#     pdf.multi_cell(0, 5, "Thank you for choosing our gym.\nThis receipt confirms that your payment has been successfully received.\nThis is a system-generated receipt and does not require a signature.", 0, 'C')

#     buffer = io.BytesIO()
#     buffer.write(pdf.output())
#     buffer.seek(0)
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
        
#         # BACKGROUND EMAIL ALERT
#         send_email_async("💬 New Feedback Received!", f"<h3>New Feedback</h3><p><b>Name:</b> {name}<br><b>Email:</b> {request.form.get('email')}<br><b>Message:</b> {message}</p>")
#          # BACKGROUND EMAIL ALERT
#         #upi_app_name = get_upi_app(payment.get('vpa', ''))
#         #send_email_async("✅ Payment Received!", f"<h3>Online Payment Successful</h3><p><b>Name:</b> {user.get('name')}<br><b>Amount:</b> ₹{user.get('final_amount')}<br><b>Plan:</b> {user.get('plan')}<br><b>Payment App:</b> {upi_app_name}<br><b>Transaction ID:</b> {payment.get('transaction_id', 'N/A')}</p>")
#         flash('✅ Feedback bhej diya! Thank you.', 'success')
#         return redirect(url_for('main.contact'))
    
#     # YE LINE MISSING THI JISKI WAJAH SE ERROR AA RAHA THA
#     return render_template('contact.html')













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
IST = pytz.timezone('Asia/Kolkata')

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
    today = datetime.now(IST).date()
    
    users = db.users.find({"status": "Active"})
    for user in users:
        expiry = user.get('expiry_date')
        if not expiry: continue
            
        if isinstance(expiry, str):
            try: expiry = datetime.strptime(expiry, '%d-%m-%Y').date()
            except: continue
        elif isinstance(expiry, datetime):
            expiry = expiry.date()
                
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
                    'expiry_date': str(expiry),
                    'status': 'pending',
                    'created_at': datetime.now(IST)
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
    
    # IST Timezone Fix for Dashboard Stats
    today_ist = datetime.now(IST)
    today_str = today_ist.strftime('%d %b %Y')
    today_start = today_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    
    today_regs = db.users.count_documents({'join_date': {'$gte': today_start}})
    today_revenue = sum(p.get('amount_paid', 0) for p in db.payments.find({'date': today_str}))
    
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
            current_expiry = user.get('expiry_date', datetime.now(IST))
            if isinstance(current_expiry, str):
                current_expiry = datetime.now(IST)
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