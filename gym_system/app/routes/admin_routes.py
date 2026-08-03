from flask import Blueprint, render_template, request, jsonify, current_app
from app.models import Member
from app.utils.date_utils import get_today_ist
from app.services.membership_service import process_expired_members, renew_member
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
def dashboard():
    today = get_today_ist()
    today_end = datetime.combine(today, datetime.max.time())
    members = Member.objects(expiry_date__lte=today_end).order_by('-expiry_date')
    return render_template('dashboard.html', members=members, today=today)

@admin_bp.route('/api/member/<member_id>/renew', methods=['POST'])
def api_renew_member(member_id):
    success = renew_member(member_id)
    if success:
        return jsonify({"status": "success", "message": "Membership renewed successfully!"}), 200
    return jsonify({"status": "error", "message": "Member not found."}), 404

@admin_bp.route('/api/scheduler/run', methods=['POST'])
def api_run_scheduler():
    secret = request.headers.get('X-Scheduler-Secret')
    expected_secret = current_app.config.get('SCHEDULER_SECRET')
    
    if not secret or secret != expected_secret:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    result = process_expired_members()
    return jsonify({"status": "success", "data": result}), 200