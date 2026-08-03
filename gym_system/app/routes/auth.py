# routes/auth.py
# Authentication related routes: Login, Register, Logout

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import get_db
from utils.helpers import validate_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    # Agar already login hai to home par bhej do
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone = request.form.get('phone', '').strip()
        
        # Validation
        if not name or not email or not password:
            flash('⚠️ Name, Email aur Password zaroori hain!', 'error')
            return redirect(url_for('auth.register'))
        
        if not validate_email(email):
            flash('⚠️ Please valid email daalein!', 'error')
            return redirect(url_for('auth.register'))
        
        if len(password) < 6:
            flash('⚠️ Password kam se kam 6 characters ka hona chahiye!', 'error')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('⚠️ Password aur Confirm Password match nahi karte!', 'error')
            return redirect(url_for('auth.register'))
        
        db = get_db()
        
        # Check karein ki email already exist to nahi karta
        existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            flash('⚠️ Ye email already registered hai! Login karein.', 'error')
            return redirect(url_for('auth.register'))
        
        # Password ko hash karke store karein (security ke liye)
        hashed_password = generate_password_hash(password)
        
        # User ko database mein insert karein
        db.execute(
            'INSERT INTO users (name, email, password, phone) VALUES (?, ?, ?, ?)',
            (name, email, hashed_password, phone)
        )
        db.commit()
        
        flash('✅ Registration successful! Ab login karein.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('⚠️ Email aur Password dono daalein!', 'error')
            return redirect(url_for('auth.login'))
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        # Check karein user exist karta hai ya nahi aur password sahi hai ya nahi
        if user and check_password_hash(user['password'], password):
            # Session mein user info store karein
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session.permanent = True
            
            flash(f'👋 Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('❌ Galat email ya password!', 'error')
            return redirect(url_for('auth.login'))
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('👋 Aap successfully logout ho gaye!', 'success')
    return redirect(url_for('main.index'))