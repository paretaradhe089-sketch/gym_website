from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from models.database import get_db
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fpdf import FPDF
import io
import config

main_bp = Blueprint('main', __name__)

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
    return render_template('index.html', active_users=active_users, upi_id=config.UPI_ID)

@main_bp.route('/register', methods=['POST'])
def register_user():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        gender = request.form.get('gender', 'Male')
        batch = request.form.get('batch', 'Morning')
        address = request.form.get('address', '').strip()
        comment = request.form.get('comment', '').strip()
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
        amount = amount_map.get(plan, 1200)
        
        user_data = {
            'name': name, 'phone': phone, 'email': email, 'gender': gender,
            'batch': batch, 'address': address, 'comment': comment, 'plan': plan,
            'payment_method': payment_method, 'amount': amount,
            'status': 'Active' if payment_method == 'Cash' else 'Pending',
            'join_date': join_date,
            'expiry_date': add_months(join_date, months_map.get(plan, 1))
        }
        
        result = db.users.insert_one(user_data)
        reg_id = str(result.inserted_id)
        
        if email: send_welcome_email(email, name)
        
        # Sirf Naye User ki notification banegi
        db.notifications.insert_one({
            'type': 'New User', 'message': f'🆕 Naya User: {name} ({phone}) - Plan: {plan}',
            'user_phone': phone, 'created_at': datetime.now(), 'is_read': False
        })
        
        if payment_method == 'Online':
            flash('✅ Registration Successful! Apna PDF receipt download karein.', 'success')
            return redirect(url_for('main.download_receipt', user_id=reg_id))
        
        flash('✅ Registration Successful!', 'success')
        return redirect(url_for('main.index'))

@main_bp.route('/download_receipt/<user_id>')
def download_receipt(user_id):
    db = get_db()
    from bson import ObjectId
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('main.index'))

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
    pdf.cell(0, 10, "REGISTRATION RECEIPT", 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font("Arial", '', 12)
    data = [
        ("Registration ID", str(user['_id'])[-8:]),
        ("Name", user.get('name', '')),
        ("Mobile Number", user.get('phone', '')),
        ("Gender", user.get('gender', '')),
        ("Batch", user.get('batch', '')),
        ("Plan", user.get('plan', '')),
        ("Joining Date", user.get('join_date').strftime('%d %b %Y')),
        ("Comment", user.get('comment', 'N/A')),
        ("Payment Status", "PAID" if user.get('payment_method') == 'Online' else "Pending"),
        ("Date & Time", datetime.now().strftime('%d %b %Y, %I:%M %p'))
    ]
    
    for label, value in data:
        pdf.set_text_color(150, 150, 150)
        pdf.cell(60, 10, label, 0, 0)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, ": " + str(value), 0, 1)
        
    pdf.ln(15)
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 5, "This is a computer generated receipt.", 0, 1, 'C')
    
    pdf_output = pdf.output()
    buffer = io.BytesIO()
    buffer.write(pdf_output)
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f"SFZ_Receipt_{user['name']}.pdf", mimetype='application/pdf')

@main_bp.route('/services')
def services():
    # Aapke naye 8 services
    services_list = [
        {'icon': '🏋️', 'title': 'Strength Training', 'desc': 'Build raw power and muscle mass with certified trainers.'},
        {'icon': '🥗', 'title': 'Nutritional Guidance', 'desc': 'Custom diet plans tailored to your body goals.'},
        {'icon': '🔥', 'title': 'Weight / Fat Loss', 'desc': 'High-intensity routines to shred fat fast.'},
        {'icon': '🍔', 'title': 'Weight Gain', 'desc': 'Mass building programs and diet for healthy weight gain.'},
        {'icon': '🏃', 'title': 'Cardio', 'desc': 'Improve stamina and heart health.'},
        {'icon': '💃', 'title': 'Zumba', 'desc': 'Dance fitness for a fun, energetic workout.'},
        {'icon': '🤸', 'title': 'Aerobics', 'desc': 'Rhythmic aerobic exercise to stretch and strengthen.'},
        {'icon': '👨‍🏫', 'title': 'Personal Training', 'desc': 'One-on-one coaching for targeted results.'}
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
