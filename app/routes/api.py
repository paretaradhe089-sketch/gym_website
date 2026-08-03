# routes/api.py
# API routes for AJAX calls etc.

from flask import Blueprint, jsonify, request, session
from models.database import get_db
from utils.helpers import login_required

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/user-info')
@login_required
def user_info():
    """Logged-in user ki info return karta hai (JSON format)"""
    return jsonify({
        'id': session.get('user_id'),
        'name': session.get('user_name'),
        'email': session.get('user_email')
    })

@api_bp.route('/api/bmi-history')
@login_required
def bmi_history():
    """User ka BMI history return karta hai"""
    db = get_db()
    records = db.execute(
        'SELECT * FROM bmi_records WHERE user_id = ? ORDER BY created_at DESC LIMIT 10',
        (session['user_id'],)
    ).fetchall()
    
    return jsonify([dict(row) for row in records])