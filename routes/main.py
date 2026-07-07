# from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
# from models.database import get_db
# from datetime import datetime
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from fpdf import FPDF
# import io
# import config

# main_bp = Blueprint('main', __name__)

# def send_welcome_email(to_email, name):
#     if not config.MAIL_EMAIL or not config.MAIL_PASSWORD: return False
#     msg = MIMEMultipart('alternative')
#     msg['Subject'] = "Welcome to Spartan Fitness Zone! 💪"
#     msg['From'] = config.MAIL_EMAIL
#     msg['To'] = to_email
#     html = f"<h2>Welcome {name}!</h2><p>Thank you for joining Spartan Fitness Zone.</p>"
#     part = MIMEText(html, 'html')
#     msg.attach(part)
#     try:
#         server = smtplib.SMTP('smtp.gmail.com', 587)
#         server.starttls()
#         server.login(config.MAIL_EMAIL, config.MAIL_PASSWORD)
#         server.sendmail(config.MAIL_EMAIL, to_email, msg.as_string())
#         server.quit()
#         return True
#     except: return False

# def add_months(source_date, months):
#     new_month = source_date.month - 1 + months
#     new_year = source_date.year + new_month // 12
#     new_month = new_month % 12 + 1
#     return datetime(new_year, new_month, source_date.day)

# @main_bp.route('/')
# def index():
#     db = get_db()
#     active_users = db.users.count_documents({'status': 'Active'})
#     return render_template('index.html', active_users=active_users, upi_id=config.UPI_ID)

# @main_bp.route('/register', methods=['POST'])
# def register_user():
#     if request.method == 'POST':
#         name = request.form.get('name', '').strip()
#         phone = request.form.get('phone', '').strip()
#         email = request.form.get('email', '').strip()
#         gender = request.form.get('gender', 'Male')
#         batch = request.form.get('batch', 'Morning')
#         address = request.form.get('address', '').strip()
#         comment = request.form.get('comment', '').strip()
#         plan = request.form.get('plan', 'Monthly')
#         payment_method = request.form.get('payment_method', 'Cash')
#         join_date_str = request.form.get('join_date') # Naya Join Date field
        
#         if not name or not phone:
#             flash('⚠️ Naam aur Phone zaroori hai!', 'error')
#             return redirect(url_for('main.index'))
        
#         # Agar join date nahi di toh aaj ki date le lo
#         try:
#             join_date = datetime.strptime(join_date_str, '%Y-%m-%d') if join_date_str else datetime.now()
#         except:
#             join_date = datetime.now()
            
#         db = get_db()
#         if db.users.find_one({'phone': phone}):
#             flash('⚠️ Ye phone number already registered hai!', 'error')
#             return redirect(url_for('main.index'))
        
#         months_map = {'Monthly': 1, 'Quarterly': 3, '6 months': 6, 'Yearly': 12}
#         amount_map = {'Monthly': 1200, 'Quarterly': 3000, '6 months': 5000, 'Yearly': 8000}
#         amount = amount_map.get(plan, 1200)
        
#         user_data = {
#             'name': name, 'phone': phone, 'email': email, 'gender': gender,
#             'batch': batch, 'address': address, 'comment': comment, 'plan': plan,
#             'payment_method': payment_method, 'amount': amount,
#             'status': 'Active' if payment_method == 'Cash' else 'Pending',
#             'join_date': join_date,
#             'expiry_date': add_months(join_date, months_map.get(plan, 1)) # Expiry ab form wali date se calculate hoga
#         }
        
#         result = db.users.insert_one(user_data)
#         reg_id = str(result.inserted_id)
        
#         if email: send_welcome_email(email, name)
        
#         # Notification code bilkul hata diya gaya hai
        
#         if payment_method == 'Online':
#             return redirect(url_for('main.payment_success', user_id=reg_id))
        
#         flash('✅ Registration Successful!', 'success')
#         return redirect(url_for('main.index'))

# # Naya Route: Payment Success aur WhatsApp Receipt
# @main_bp.route('/payment_success/<user_id>')
# def payment_success(user_id):
#     db = get_db()
#     from bson import ObjectId
#     user = db.users.find_one({'_id': ObjectId(user_id)})
#     if not user:
#         return redirect(url_for('main.index'))
    
#     # WhatsApp link generate karna
#     wa_number = config.ADMIN_WHATSAPP
#     wa_text = f"Hi Admin! I am {user['name']}. I have completed my online payment of ₹{user['amount']} for the {user['plan']} plan. My Registration ID is {str(user['_id'])[-8:]}. Please confirm."
#     wa_link = f"https://wa.me/{wa_number}?text={wa_text.replace(' ', '%20')}"
    
#     return render_template('payment_success.html', user=user, wa_link=wa_link, reg_id=user_id)

# @main_bp.route('/download_receipt/<user_id>')
# def download_receipt(user_id):
#     db = get_db()
#     from bson import ObjectId
#     user = db.users.find_one({'_id': ObjectId(user_id)})
#     if not user:
#         flash('User not found!', 'error')
#         return redirect(url_for('main.index'))

#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_fill_color(17, 17, 17)
#     pdf.rect(0, 0, 210, 297, 'F')
    
#     pdf.set_text_color(255, 212, 0)
#     pdf.set_font("Arial", 'B', 28)
#     pdf.cell(0, 15, "SFZ", 0, 1, 'C')
#     pdf.set_text_color(255, 255, 255)
#     pdf.set_font("Arial", 'B', 14)
#     pdf.cell(0, 10, "Spartan Fitness Zone", 0, 1, 'C')
#     pdf.set_text_color(150, 150, 150)
#     pdf.set_font("Arial", '', 10)
#     pdf.cell(0, 5, "E9 - First Floor, Sharma Colony, Nandpuri, Jaipur", 0, 1, 'C')
#     pdf.ln(10)
    
#     pdf.set_text_color(255, 212, 0)
#     pdf.set_font("Arial", 'B', 16)
#     pdf.cell(0, 10, "REGISTRATION RECEIPT", 0, 1, 'C')
#     pdf.ln(5)
    
#     pdf.set_font("Arial", '', 12)
#     data = [
#         ("Registration ID", str(user['_id'])[-8:]),
#         ("Name", user.get('name', '')),
#         ("Mobile Number", user.get('phone', '')),
#         ("Gender", user.get('gender', '')),
#         ("Batch", user.get('batch', '')),
#         ("Plan", user.get('plan', '')),
#         ("Joining Date", user.get('join_date').strftime('%d %b %Y')),
#         ("Comment", user.get('comment', 'N/A')),
#         ("Payment Status", "PAID" if user.get('payment_method') == 'Online' else "Pending"),
#         ("Date & Time", datetime.now().strftime('%d %b %Y, %I:%M %p'))
#     ]
    
#     for label, value in data:
#         pdf.set_text_color(150, 150, 150)
#         pdf.cell(60, 10, label, 0, 0)
#         pdf.set_text_color(255, 255, 255)
#         pdf.cell(0, 10, ": " + str(value), 0, 1)
        
#     pdf.ln(15)
#     pdf.set_text_color(100, 100, 100)
#     pdf.set_font("Arial", 'I', 8)
#     pdf.cell(0, 5, "This is a computer generated receipt.", 0, 1, 'C')
    
#     pdf_output = pdf.output()
#     buffer = io.BytesIO()
#     buffer.write(pdf_output)
#     buffer.seek(0)
    
#     return send_file(buffer, as_attachment=True, download_name=f"SFZ_Receipt_{user['name']}.pdf", mimetype='application/pdf')

# @main_bp.route('/services')
# def services():
#     services_list = [
#         {'icon': '🏋️', 'title': 'Strength Training', 'desc': 'Build raw power and muscle mass with certified trainers.'},
#         {'icon': '🥗', 'title': 'Nutritional Guidance', 'desc': 'Custom diet plans tailored to your body goals.'},
#         {'icon': '🔥', 'title': 'Weight / Fat Loss', 'desc': 'High-intensity routines to shred fat fast.'},
#         {'icon': '🍔', 'title': 'Weight Gain', 'desc': 'Mass building programs and diet for healthy weight gain.'},
#         {'icon': '🏃', 'title': 'Cardio', 'desc': 'Improve stamina and heart health.'},
#         {'icon': '💃', 'title': 'Zumba', 'desc': 'Dance fitness for a fun, energetic workout.'},
#         {'icon': '🤸', 'title': 'Aerobics', 'desc': 'Rhythmic aerobic exercise to stretch and strengthen.'},
#         {'icon': '👨‍🏫', 'title': 'Personal Training', 'desc': 'One-on-one coaching for targeted results.'}
#     ]
#     return render_template('services.html', services=services_list)

# @main_bp.route('/contact', methods=['GET', 'POST'])
# def contact():
#     db = get_db()
#     if request.method == 'POST':
#         name = request.form.get('name', '').strip()
#         email = request.form.get('email', '').strip()
#         message = request.form.get('message', '').strip()
#         if not name or not message:
#             flash('⚠️ Naam aur Message zaroori hai!', 'error')
#             return redirect(url_for('main.contact'))
#         db.feedback.insert_one({'name': name, 'email': email, 'message': message, 'created_at': datetime.now()})
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
import config
import razorpay

main_bp = Blueprint('main', __name__)
razorpay_client = razorpay.Client(auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET))

def send_welcome_email(to_email, name):
    if not config.MAIL_EMAIL or not config.MAIL_PASSWORD: return False
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Welcome to Spartan Fitness Zone! 💪"
    msg['From'] = config.MAIL_EMAIL
    msg['To'] = to_email
    html = f"<h2>Welcome {name}!</h2><p>Thank you for joining Spartan Fitness Zone.</p>"
    part = MIMEText(html, 'html')
    msg.attach(part)
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(config.MAIL_EMAIL, config.MAIL_PASSWORD)
        server.sendmail(config.MAIL_EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except: return False

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

@main_bp.route('/create_order', methods=['POST'])
def create_order():
    data = request.json
    amount = int(data.get('amount', 1200)) * 100
    
    db = get_db()
    user_data = {
        'name': data.get('name'), 'phone': data.get('phone'), 'email': data.get('email'),
        'gender': data.get('gender'), 'batch': data.get('batch'), 'address': data.get('address'),
        'comment': data.get('comment'), 'plan': data.get('plan'), 'amount': int(data.get('amount', 1200)),
        'payment_method': 'Online', 'status': 'Pending',
        'join_date': datetime.now(),
        'expiry_date': add_months(datetime.now(), {'Monthly': 1, 'Quarterly': 3, '6 months': 6, 'Yearly': 12}.get(data.get('plan'), 1))
    }
    result = db.users.insert_one(user_data)
    user_id = str(result.inserted_id)
    
    order = razorpay_client.order.create({
        'amount': amount,
        'currency': 'INR',
        'receipt': f'spz_rcpt_{user_id[-8:]}',
        'notes': {'user_id': user_id, 'name': data.get('name')}
    })
    
    return jsonify({'order_id': order['id'], 'user_id': user_id, 'amount': amount})

@main_bp.route('/register', methods=['POST'])
def register_user():
    db = get_db()
    
    if request.form.get('payment_method') == 'Cash':
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
            'plan': plan, 'amount': amount, 'payment_method': 'Cash', 'status': 'Active',
            'join_date': join_date, 'expiry_date': add_months(join_date, {'Monthly': 1, 'Quarterly': 3, '6 months': 6, 'Yearly': 12}.get(plan, 1))
        }
        db.users.insert_one(user_data)
        flash('✅ Registration Successful!', 'success')
        return redirect(url_for('main.index'))
        
    return redirect(url_for('main.index'))

@main_bp.route('/verify_payment', methods=['POST'])
def verify_payment():
    db = get_db()
    from bson import ObjectId
    
    data = request.json
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_signature = data.get('razorpay_signature')
    user_id = data.get('user_id')
    
    try:
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        payment = razorpay_client.payment.fetch(razorpay_payment_id)
        if payment['status'] == 'captured' or payment['method'] == 'upi':
            db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'status': 'Active'}})
            
            user = db.users.find_one({'_id': ObjectId(user_id)})
            transaction = {
                'user_id': user_id,
                'name': user.get('name'),
                'phone': user.get('phone'),
                'email': user.get('email'),
                'plan': user.get('plan'),
                'amount': user.get('amount'),
                'transaction_id': razorpay_payment_id,
                'order_id': razorpay_order_id,
                'payment_method': payment['method'],
                'status': 'SUCCESS',
                'date': datetime.now()
            }
            db.payments.insert_one(transaction)
            
            return jsonify({'status': 'success', 'user_id': user_id})
        else:
            return jsonify({'status': 'failed'})
            
    except Exception as e:
        print(f"Payment Verification Failed: {e}")
        return jsonify({'status': 'failed', 'error': str(e)})

@main_bp.route('/payment_success/<user_id>')
def payment_success(user_id):
    db = get_db()
    from bson import ObjectId
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if not user: return redirect(url_for('main.index'))
    
    wa_text = f"Hi Admin! I am {user['name']}. I have completed my online payment of ₹{user['amount']} for the {user['plan']} plan. My Registration ID is {str(user['_id'])[-8:]}. Please confirm."
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
    
    pdf.set_text_color(255, 212, 0)
    pdf.set_font("Arial", 'B', 28)
    pdf.cell(0, 15, "SFZ", 0, 1, 'C')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Spartan Fitness Zone", 0, 1, 'C')
    pdf.set_text_color(150, 150, 150)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, "E9 - First Floor, Sharma Colony, Nandpuri, Jaipur", 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_text_color(255, 212, 0)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "PAYMENT RECEIPT", 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font("Arial", '', 12)
    data = [
        ("Receipt Number", f"SFZ{str(user['_id'])[-6:]}"),
        ("Member Name", user.get('name', '')),
        ("Member ID", str(user['_id'])[-8:]),
        ("Membership Plan", user.get('plan', '')),
        ("Amount Paid", f"₹{user.get('amount', 0)}"),
        ("Date", datetime.now().strftime('%d %b %Y')),
        ("Time", datetime.now().strftime('%I:%M %p')),
        ("Razorpay Payment ID", payment.get('transaction_id', 'N/A') if payment else 'N/A'),
        ("Transaction ID", payment.get('transaction_id', 'N/A') if payment else 'N/A'),
        ("Payment Method", payment.get('payment_method', 'N/A').upper() if payment else 'CASH'),
        ("Payment Status", "SUCCESS"),
    ]
    
    for label, value in data:
        pdf.set_text_color(150, 150, 150)
        pdf.cell(60, 10, label, 0, 0)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, ": " + str(value), 0, 1)
        
    pdf.ln(15)
    pdf.set_text_color(255, 212, 0)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Thank You for choosing Spartan Fitness Zone!", 0, 1, 'C')
    
    pdf_output = pdf.output()
    buffer = io.BytesIO()
    buffer.write(pdf_output)
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f"SFZ_Receipt_{user['name']}.pdf", mimetype='application/pdf')

@main_bp.route('/services')
def services():
    services_list = [
        {'icon': '🏋️', 'title': 'Strength Training', 'desc': 'Build raw power and muscle mass with progressive overload and expert guidance.', 'img': 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800&q=80', 'benefits': ['Increased Muscle Mass', 'Better Bone Density', 'Enhanced Metabolism', 'Improved Posture']},
        {'icon': '🥗', 'title': 'Nutritional Guidance', 'desc': 'Custom diet plans tailored to your body goals for long-term health.', 'img': 'https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=800&q=80', 'benefits': ['Personalized Diet Chart', 'Fat Loss Support', 'Muscle Gain Diet', 'Lifestyle Management']},
        {'icon': '🔥', 'title': 'Weight Loss', 'desc': 'High-intensity routines designed to shred fat fast and safely.', 'img': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&q=80', 'benefits': ['Rapid Fat Burn', 'Increased Stamina', 'Core Strengthening', 'Boosted Confidence']},
        {'icon': '💪', 'title': 'Muscle Building', 'desc': 'Hypertrophy focused training protocols for maximum muscle growth.', 'img': 'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=800&q=80', 'benefits': ['Targeted Muscle Growth', 'Strength Optimization', 'Supplement Guidance', 'Recovery Techniques']},
        {'icon': '🏃', 'title': 'Cardio Training', 'desc': 'Improve heart health and endurance with modern equipment.', 'img': 'https://images.unsplash.com/photo-1538805060514-97d9cc17730c?w=800&q=80', 'benefits': ['Heart Health', 'Lung Capacity', 'Endurance Boost', 'Stress Relief']},
        {'icon': '🤼', 'title': 'CrossFit', 'desc': 'High-intensity functional movements to push your limits.', 'img': 'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=800&q=80', 'benefits': ['Full Body Workout', 'Agility & Speed', 'Community Support', 'Functional Strength']},
        {'icon': '🧘', 'title': 'Yoga', 'desc': 'Improve flexibility, balance, and mental peace.', 'img': 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=800&q=80', 'benefits': ['Flexibility', 'Mental Peace', 'Injury Prevention', 'Better Breathing']},
        {'icon': '🏃‍♂️', 'title': 'Functional Training', 'desc': 'Exercises that mimic daily activities for real-world strength.', 'img': 'https://images.unsplash.com/photo-1599058917212-d750089bc07e?w=800&q=80', 'benefits': ['Real-world Strength', 'Balance Improvement', 'Core Stability', 'Mobility']}
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
        db.feedback.insert_one({'name': name, 'email': email, 'message': message, 'created_at': datetime.now()})
        flash('✅ Feedback bhej diya! Thank you.', 'success')
        return redirect(url_for('main.contact'))
    return render_template('contact.html')
