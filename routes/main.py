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

# ─── Helper Functions ───────────────────────────────────────────────

def send_welcome_email(to_email, name):
    if not config.MAIL_EMAIL or not config.MAIL_PASSWORD:
        return False
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Welcome to Spartan Fitness Zone! 💪"
    msg['From'] = config.MAIL_EMAIL
    msg['To'] = to_email
    html = f"<h2>Welcome {name}!</h2><p>Thank you for joining Spartan Fitness Zone.</p>"
    msg.attach(MIMEText(html, 'html'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(config.MAIL_EMAIL, config.MAIL_PASSWORD)
        server.sendmail(config.MAIL_EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except:
        return False

def add_months(source_date, months):
    new_month = source_date.month - 1 + months
    new_year = source_date.year + new_month // 12
    new_month = new_month % 12 + 1
    return datetime(new_year, new_month, source_date.day)

# ─── Routes ─────────────────────────────────────────────────────────

@main_bp.route('/')
def index():
    db = get_db()
    active_users = db.users.count_documents({'status': 'Active'})
    return render_template('index.html', active_users=active_users, upi_id=config.UPI_ID)

@main_bp.route('/create_order', methods=['POST'])
def create_order():
    data = request.json
    amount = int(data.get('amount', 1200)) * 100

    db = get_db()
    join_date = datetime.now()
    months_map = {'Monthly': 1, 'Quarterly': 3, '6 months': 6, 'Yearly': 12}

    user_data = {
        'name': data.get('name'),
        'phone': data.get('phone'),
        'email': data.get('email'),
        'gender': data.get('gender'),
        'batch': data.get('batch'),
        'address': data.get('address'),
        'comment': data.get('comment'),
        'plan': data.get('plan', 'Monthly'),
        'amount': int(data.get('amount', 1200)),
        'payment_method': 'Online',
        'status': 'Pending',
        'join_date': join_date,
        'expiry_date': add_months(join_date, months_map.get(data.get('plan', 'Monthly'), 1))
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

    if request.form.get('payment_method') != 'Cash':
        return redirect(url_for('main.index'))

    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    gender = request.form.get('gender', 'Male')
    batch = request.form.get('batch', 'Morning')
    address = request.form.get('address', '').strip()
    comment = request.form.get('comment', '').strip()
    plan = request.form.get('plan', 'Monthly')

    if not name or not phone:
        flash('⚠️ Naam aur Phone zaroori hai!', 'error')
        return redirect(url_for('main.index'))

    if db.users.find_one({'phone': phone}):
        flash('⚠️ Ye phone number already registered hai!', 'error')
        return redirect(url_for('main.index'))

    join_date = datetime.now()
    months_map = {'Monthly': 1, 'Quarterly': 3, '6 months': 6, 'Yearly': 12}
    amount_map = {'Monthly': 1200, 'Quarterly': 3000, '6 months': 5000, 'Yearly': 8000}
    amount = amount_map.get(plan, 1200)

    user_data = {
        'name': name,
        'phone': phone,
        'email': email,
        'gender': gender,
        'batch': batch,
        'address': address,
        'comment': comment,
        'plan': plan,
        'payment_method': 'Cash',
        'amount': amount,
        'status': 'Active',
        'join_date': join_date,
        'expiry_date': add_months(join_date, months_map.get(plan, 1))
    }

    result = db.users.insert_one(user_data)
    reg_id = str(result.inserted_id)

    if email:
        send_welcome_email(email, name)

    db.notifications.insert_one({
        'type': 'New User',
        'message': f'🆕 Naya User: {name} ({phone}) - Plan: {plan}',
        'user_phone': phone,
        'created_at': datetime.now(),
        'is_read': False
    })

    flash('✅ Registration Successful!', 'success')
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
                'order_id': razorpay_order_id,
                'payment_id': razorpay_payment_id,
                'transaction_id': razorpay_payment_id,
                'payment_method': payment['method'],
                'status': 'SUCCESS',
                'date': datetime.now().strftime('%d %b %Y'),
                'time': datetime.now().strftime('%I:%M %p'),
                'receipt': f"SFZ{str(user_id)[-6:]}"
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
    if not user:
        return redirect(url_for('main.index'))

    wa_text = f"Hi Admin! I am {user['name']}. I have completed my online payment of ₹{user['amount']} for the {user['plan']} plan. My Reg ID is {str(user['_id'])[-8:]}."
    wa_link = f"https://wa.me/{config.ADMIN_WHATSAPP}?text={wa_text.replace(' ', '%20')}"

    return render_template('payment_success.html', user=user, wa_link=wa_link, reg_id=user_id)

@main_bp.route('/download_receipt/<user_id>')
def download_receipt(user_id):
    db = get_db()
    from bson import ObjectId
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('main.index'))

    payment = db.payments.find_one({'user_id': user_id})
    is_online = payment is not None

    pdf = FPDF()
    pdf.add_page()

    # Black Background
    pdf.set_fill_color(17, 17, 17)
    pdf.rect(0, 0, 210, 297, 'F')

    # Header
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
    title = "PAYMENT RECEIPT" if is_online else "REGISTRATION RECEIPT"
    pdf.cell(0, 10, title, 0, 1, 'C')
    pdf.ln(5)

    pdf.set_font("Arial", '', 12)

    if is_online:
        data = [
            ("Receipt Number", f"SFZ{str(user['_id'])[-6:]}"),
            ("Member Name", user.get('name', '')),
            ("Member ID", str(user['_id'])[-8:]),
            ("Membership Plan", user.get('plan', '')),
            ("Amount Paid", f"₹{user.get('amount', 0)}"),
            ("Payment Date", payment.get('date', '')),
            ("Payment Time", payment.get('time', '')),
            ("Razorpay Order ID", payment.get('order_id', 'N/A')),
            ("Razorpay Payment ID", payment.get('payment_id', 'N/A')),
            ("Transaction ID", payment.get('transaction_id', 'N/A')),
            ("Payment Method", payment.get('payment_method', 'N/A').upper()),
            ("Payment Status", "SUCCESS")
        ]
    else:
        data = [
            ("Registration ID", str(user['_id'])[-8:]),
            ("Name", user.get('name', '')),
            ("Mobile Number", user.get('phone', '')),
            ("Gender", user.get('gender', '')),
            ("Batch", user.get('batch', '')),
            ("Plan", user.get('plan', '')),
            ("Joining Date", user.get('join_date').strftime('%d %b %Y')),
            ("Comment", user.get('comment', 'N/A')),
            ("Payment Status", "CASH"),
            ("Date & Time", datetime.now().strftime('%d %b %Y, %I:%M %p'))
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

    pdf.set_text_color(100, 100, 100)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 5, "This is a computer generated receipt.", 0, 1, 'C')

    buffer = io.BytesIO()
    buffer.write(pdf.output())
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"SFZ_Receipt_{user['name']}.pdf", mimetype='application/pdf')

@main_bp.route('/services')
def services():
    services_list = [
        {'icon': '🏋️', 'title': 'Strength Training', 'desc': 'Build raw power and muscle mass with progressive overload and expert guidance.', 'img': 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800&q=80', 'benefits': ['Increased Muscle Mass', 'Better Bone Density', 'Enhanced Metabolism', 'Improved Posture']},
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
        db.feedback.insert_one({
            'name': name,
            'email': email,
            'message': message,
            'created_at': datetime.now()
        })
        flash('✅ Feedback bhej diya! Thank you.', 'success')
        return redirect(url_for('main.contact'))
    return render_template('contact.html')
