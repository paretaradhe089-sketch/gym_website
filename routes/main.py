# from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
# from models.database import get_db
# from datetime import datetime
# from fpdf import FPDF
# import io
# import urllib.request
# import qrcode
# import config
# import razorpay

# main_bp = Blueprint('main', __name__)
# razorpay_client = razorpay.Client(auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET))

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
#     if '@ibl' in vpa or '@upi' in vpa: return 'BHIM UPI'
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
#                 'payment_method': payment['method'], 'upi_app': get_upi_app(payment.get('vpa', '')), 'vpa': payment.get('vpa', 'N/A'),
#                 'status': 'SUCCESS',
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

#     receipt_no = f"SFZ{str(user['_id'])[-6:]}"
#     invoice_no = f"INV-2024-{str(user['_id'])[-4:]}"

#     # QR Code Generation
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

#     # Header Background
#     pdf.set_fill_color(17, 17, 17)
#     pdf.rect(0, 0, 210, 40, 'F')

#     # Logo Load from URL
#     logo_url = "https://z-cdn-media.chatglm.cn/files/66dfb45d-eb25-46d5-87a9-2f527f8758cf.jpeg?auth_key=1883997017-3faf8b3e4e594a43b060a3bc21b1c3e2-0-799070c3fe3307a0f0a85b395b3404df"
#     try:
#         with urllib.request.urlopen(logo_url) as response:
#             logo_data = io.BytesIO(response.read())
#             pdf.image(logo_data, x=10, y=8, w=20)
#     except:
#         pass

#     # Gym Details
#     pdf.set_xy(35, 10)
#     pdf.set_text_color(255, 215, 0)
#     pdf.set_font("Arial", 'B', 16)
#     pdf.cell(0, 8, config.GYM_NAME, 0, 1)

#     pdf.set_xy(35, 18)
#     pdf.set_text_color(255, 255, 255)
#     pdf.set_font("Arial", '', 8)
#     pdf.multi_cell(80, 4, f"{config.GYM_ADDRESS}\nPhone: {config.GYM_PHONE} | Email: {config.GYM_EMAIL}\nWebsite: {config.GYM_WEBSITE}")

#     # Right side: Receipt Info
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

#     # Member & Membership Details
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

#     # Payment Details
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

#     # Summary
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

#     # QR Code Image
#     pdf.ln(5)
#     pdf.image(img_byte_arr, x=85, y=None, w=30)
#     pdf.set_font("Arial", '', 8)
#     pdf.set_text_color(100)
#     pdf.cell(0, 5, "Scan to verify receipt", 0, 1, 'C')

#     # Footer
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
#         flash('✅ Feedback bhej diya! Thank you.', 'success')
#         return redirect(url_for('main.contact'))
#     return render_template('contact.html')













































# from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
# from models.database import get_db
# from datetime import datetime
# from fpdf import FPDF
# import io
# import urllib.request
# import qrcode
# import config
# import razorpay

# main_bp = Blueprint('main', __name__)
# razorpay_client = razorpay.Client(auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET))

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
#     if '@ibl' in vpa or '@upi' in vpa: return 'BHIM UPI'
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
#                 'payment_method': payment['method'], 'upi_app': get_upi_app(payment.get('vpa', '')), 'vpa': payment.get('vpa', 'N/A'),
#                 'status': 'SUCCESS',
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

#     receipt_no = f"SFZ{str(user['_id'])[-6:]}"
#     invoice_no = f"INV-2024-{str(user['_id'])[-4:]}"

#     # QR Code Generation
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

#     # Header Background
#     pdf.set_fill_color(17, 17, 17)
#     pdf.rect(0, 0, 210, 40, 'F')

#     # Logo Load from URL
#     logo_url = "https://z-cdn-media.chatglm.cn/files/66dfb45d-eb25-46d5-87a9-2f527f8758cf.jpeg?auth_key=1883997017-3faf8b3e4e594a43b060a3bc21b1c3e2-0-799070c3fe3307a0f0a85b395b3404df"
#     try:
#         with urllib.request.urlopen(logo_url) as response:
#             logo_data = io.BytesIO(response.read())
#             pdf.image(logo_data, x=10, y=8, w=20)
#     except:
#         pass

#     # Gym Details
#     pdf.set_xy(35, 10)
#     pdf.set_text_color(255, 215, 0)
#     pdf.set_font("Arial", 'B', 16)
#     pdf.cell(0, 8, config.GYM_NAME, 0, 1)

#     pdf.set_xy(35, 18)
#     pdf.set_text_color(255, 255, 255)
#     pdf.set_font("Arial", '', 8)
#     pdf.multi_cell(80, 4, f"{config.GYM_ADDRESS}\nPhone: {config.GYM_PHONE} | Email: {config.GYM_EMAIL}\nWebsite: {config.GYM_WEBSITE}")

#     # Right side: Receipt Info
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

#     # Member & Membership Details
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

#     # Payment Details
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

#     # Summary
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

#     # QR Code Image
#     pdf.ln(5)
#     pdf.image(img_byte_arr, x=85, y=None, w=30)
#     pdf.set_font("Arial", '', 8)
#     pdf.set_text_color(100)
#     pdf.cell(0, 5, "Scan to verify receipt", 0, 1, 'C')

#     # Footer
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
#         flash('✅ Feedback bhej diya! Thank you.', 'success')
#         return redirect(url_for('main.contact'))
#     return render_template('contact.html')
















from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from models.database import get_db
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fpdf import FPDF
import io
import urllib.request
import qrcode
import config
import razorpay
import threading 
import socket # Naya import for IPv4 fix

main_bp = Blueprint('main', __name__)
razorpay_client = razorpay.Client(auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET))

# === EMAIL FUNCTION WITH IPv4 FIX ===
class IPv4_SMTP(smtplib.SMTP):
    """Force IPv4 to avoid Render's IPv6 network unreachable error"""
    address_family = socket.AF_INET

def send_admin_email(subject, body):
    if not config.MAIL_EMAIL or not config.MAIL_PASSWORD:
        print("--- DEBUG: Email/Password missing ---")
        return False
        
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = config.MAIL_EMAIL
    msg['To'] = config.MAIL_EMAIL
    part = MIMEText(body, 'html')
    msg.attach(part)
    
    try:
        print("--- DEBUG: Connecting to Gmail via IPv4... ---")
        # Yahan smtplib.SMTP ki jagah IPv4_SMTP use kiya hai
        server = IPv4_SMTP('smtp.gmail.com', 587, timeout=15) 
        server.starttls()
        server.login(config.MAIL_EMAIL, config.MAIL_PASSWORD)
        server.sendmail(config.MAIL_EMAIL, config.MAIL_EMAIL, msg.as_string())
        server.quit()
        print("--- DEBUG: Email sent successfully! ---")
        return True
    except Exception as e:
        print(f"--- DEBUG: Email Error: {e} ---")
        return False

# === BACKGROUND THREAD FUNCTION ===
def send_email_async(subject, body):
    """Email ko background mein bhejne ke liye, taaki website slow na ho"""
    thread = threading.Thread(target=send_admin_email, args=(subject, body))
    thread.daemon = True
    thread.start()

def add_months(source_date, months):
    new_month = source_date.month - 1 + months
    new_year = source_date.year + new_month // 12
    new_month = new_month % 12 + 1
    return datetime(new_year, new_month, source_date.day)

def get_upi_app(vpa):
    if not vpa: return "N/A"
    if '@ybl' in vpa or '@apl' in vpa: return 'PhonePe'
    if '@ok' in vpa or '@oksbi' in vpa: return 'Google Pay'
    if '@paytm' in vpa: return 'Paytm'
    return 'UPI'

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
    
    if not coupon: return jsonify({'valid': False, 'message': 'Invalid Coupon Code.'})
    if datetime.strptime(coupon['expiry_date'], '%Y-%m-%d') < datetime.now(): return jsonify({'valid': False, 'message': 'Coupon expired.'})
    if amount < coupon.get('min_amount', 0): return jsonify({'valid': False, 'message': f'Min amount ₹{coupon["min_amount"]} required.'})
        
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
    
    if db.users.find_one({'phone': data.get('phone')}): return jsonify({'error': 'Phone number already registered!'})
        
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
    
    # BACKGROUND EMAIL ALERT
    send_email_async("🆕 New Online Registration Pending!", f"<h3>New User Registered (Online Pending)</h3><p><b>Name:</b> {user_data['name']}<br><b>Phone:</b> {user_data['phone']}<br><b>Plan:</b> {user_data['plan']}</p>")
    
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
    
    # BACKGROUND EMAIL ALERT
    send_email_async("💰 New Cash Registration!", f"<h3>New User Registered (Cash)</h3><p><b>Name:</b> {name}<br><b>Phone:</b> {phone}<br><b>Plan:</b> {plan}<br><b>Amount:</b> ₹{amount}</p>")
    
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
                'payment_method': payment['method'], 'upi_app': get_upi_app(payment.get('vpa', '')), 'vpa': payment.get('vpa', 'N/A'),
                'status': 'SUCCESS',
                'date': datetime.now().strftime('%d %b %Y'), 'time': datetime.now().strftime('%I:%M %p'),
                'receipt': f"SFZ{str(user_id)[-6:]}"
            }
            db.payments.insert_one(transaction)
            
            # BACKGROUND EMAIL ALERT
            send_email_async("✅ Payment Received!", f"<h3>Online Payment Successful</h3><p><b>Name:</b> {user.get('name')}<br><b>Amount:</b> ₹{user.get('final_amount')}<br><b>Plan:</b> {user.get('plan')}</p>")
            
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

    receipt_no = f"SFZ{str(user['_id'])[-6:]}"
    invoice_no = f"INV-2024-{str(user['_id'])[-4:]}"

    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(f"Receipt No: {receipt_no}, Name: {user.get('name')}, Amount: Rs. {user.get('final_amount', 0)}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    img_byte_arr = io.BytesIO()
    qr_img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_fill_color(17, 17, 17)
    pdf.rect(0, 0, 210, 40, 'F')

    logo_url = "https://z-cdn-media.chatglm.cn/files/66dfb45d-eb25-46d5-87a9-2f527f8758cf.jpeg?auth_key=1883997017-3faf8b3e4e594a43b060a3bc21b1c3e2-0-799070c3fe3307a0f0a85b395b3404df"
    try:
        with urllib.request.urlopen(logo_url, timeout=5) as response:
            logo_data = io.BytesIO(response.read())
            pdf.image(logo_data, x=10, y=8, w=20)
    except:
        pass

    pdf.set_xy(35, 10)
    pdf.set_text_color(255, 215, 0)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 8, config.GYM_NAME, 0, 1)

    pdf.set_xy(35, 18)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", '', 8)
    pdf.multi_cell(80, 4, f"{config.GYM_ADDRESS}\nPhone: {config.GYM_PHONE} | Email: {config.GYM_EMAIL}\nWebsite: {config.GYM_WEBSITE}")

    pdf.set_xy(130, 10)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(70, 5, "PAYMENT RECEIPT", 0, 1, 'R')
    pdf.set_font("Arial", '', 8)
    pdf.set_xy(130, 16)
    pdf.cell(70, 4, f"Receipt No: {receipt_no}", 0, 1, 'R')
    pdf.set_xy(130, 20)
    pdf.cell(70, 4, f"Invoice No: {invoice_no}", 0, 1, 'R')
    pdf.set_xy(130, 24)
    pdf.cell(70, 4, f"Date: {datetime.now().strftime('%d %b %Y %I:%M %p')}", 0, 1, 'R')
    pdf.set_xy(130, 28)
    pdf.set_text_color(46, 204, 113)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(70, 4, "Status: SUCCESS", 0, 1, 'R')

    pdf.ln(10)

    pdf.set_text_color(17, 17, 17)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(255, 215, 0)
    pdf.cell(95, 7, " MEMBER DETAILS", 1, 0, 'L', True)
    pdf.cell(95, 7, " MEMBERSHIP DETAILS", 1, 1, 'L', True)

    pdf.set_font("Arial", '', 9)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(40, 6, " Member Name:", 1, 0, 'L', True)
    pdf.cell(55, 6, f" {user.get('name', '')}", 1, 0, 'L')
    pdf.cell(40, 6, " Plan Name:", 1, 0, 'L', True)
    pdf.cell(55, 6, f" {user.get('plan', '')}", 1, 1, 'L')

    pdf.cell(40, 6, " Mobile:", 1, 0, 'L', True)
    pdf.cell(55, 6, f" {user.get('phone', '')}", 1, 0, 'L')
    pdf.cell(40, 6, " Start Date:", 1, 0, 'L', True)
    pdf.cell(55, 6, f" {user.get('join_date').strftime('%d %b %Y')}", 1, 1, 'L')

    pdf.cell(40, 6, " Email:", 1, 0, 'L', True)
    pdf.cell(55, 6, f" {user.get('email', 'N/A')}", 1, 0, 'L')
    pdf.cell(40, 6, " Expiry Date:", 1, 0, 'L', True)
    pdf.cell(55, 6, f" {user.get('expiry_date').strftime('%d %b %Y')}", 1, 1, 'L')

    pdf.cell(40, 6, " Member ID:", 1, 0, 'L', True)
    pdf.cell(55, 6, f" {str(user['_id'])[-8:]}", 1, 0, 'L')
    pdf.cell(40, 6, " Duration:", 1, 0, 'L', True)
    pdf.cell(55, 6, f" {user.get('plan', '')}", 1, 1, 'L')

    pdf.ln(5)

    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(255, 215, 0)
    pdf.cell(0, 7, " PAYMENT DETAILS", 1, 1, 'L', True)

    pdf.set_font("Arial", '', 9)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(50, 6, " Payment Gateway:", 1, 0, 'L', True)
    pdf.cell(40, 6, " Razorpay", 1, 0, 'L')
    pdf.cell(40, 6, " Payment Method:", 1, 0, 'L', True)
    pdf.cell(60, 6, f" {payment.get('payment_method', 'N/A').upper()}", 1, 1, 'L')

    pdf.cell(50, 6, " UPI App Used:", 1, 0, 'L', True)
    pdf.cell(40, 6, f" {payment.get('upi_app', 'N/A')}", 1, 0, 'L')
    pdf.cell(40, 6, " Transaction ID:", 1, 0, 'L', True)
    pdf.cell(60, 6, f" {payment.get('transaction_id', 'N/A')}", 1, 1, 'L')

    pdf.cell(50, 6, " Razorpay Order ID:", 1, 0, 'L', True)
    pdf.cell(140, 6, f" {payment.get('order_id', 'N/A')}", 1, 1, 'L')

    pdf.cell(50, 6, " Razorpay Payment ID:", 1, 0, 'L', True)
    pdf.cell(140, 6, f" {payment.get('payment_id', 'N/A')}", 1, 1, 'L')

    pdf.cell(50, 6, " Payment Date/Time:", 1, 0, 'L', True)
    pdf.cell(140, 6, f" {payment.get('date', '')} {payment.get('time', '')}", 1, 1, 'L')

    pdf.ln(5)

    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(255, 215, 0)
    pdf.cell(0, 7, " PAYMENT SUMMARY", 1, 1, 'L', True)

    pdf.set_font("Arial", '', 10)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(120, 7, " Membership Fee", 1, 0, 'R', True)
    pdf.cell(70, 7, f" Rs. {user.get('amount', 0)}", 1, 1, 'L')

    pdf.cell(120, 7, " Discount", 1, 0, 'R', True)
    pdf.cell(70, 7, f" - Rs. {user.get('discount', 0)}", 1, 1, 'L')

    pdf.cell(120, 7, " Taxes", 1, 0, 'R', True)
    pdf.cell(70, 7, " Rs. 0", 1, 1, 'L')

    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(17, 17, 17)
    pdf.set_text_color(255, 215, 0)
    pdf.cell(120, 8, " TOTAL AMOUNT PAID", 1, 0, 'R', True)
    pdf.cell(70, 8, f" Rs. {user.get('final_amount', 0)}", 1, 1, 'L', True)
    pdf.set_text_color(17, 17, 17)

    pdf.ln(5)
    pdf.image(img_byte_arr, x=85, y=None, w=30)
    pdf.set_font("Arial", '', 8)
    pdf.set_text_color(100)
    pdf.cell(0, 5, "Scan to verify receipt", 0, 1, 'C')

    pdf.ln(5)
    pdf.set_y(-50)
    pdf.set_text_color(100)
    pdf.set_font("Arial", 'I', 8)
    pdf.multi_cell(0, 5, "Thank you for choosing our gym.\nThis receipt confirms that your payment has been successfully received.\nThis is a system-generated receipt and does not require a signature.", 0, 'C')

    buffer = io.BytesIO()
    buffer.write(pdf.output())
    buffer.seek(0)
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
        
        # BACKGROUND EMAIL ALERT
        send_email_async("💬 New Feedback Received!", f"<h3>New Feedback</h3><p><b>Name:</b> {name}<br><b>Email:</b> {request.form.get('email')}<br><b>Message:</b> {message}</p>")
        
        flash('✅ Feedback bhej diya! Thank you.', 'success')
        return redirect(url_for('main.contact'))
    return render_template('contact.html')