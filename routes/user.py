from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import User, Attendance, LeaveRequest
from app import db
from datetime import datetime, date, timedelta
from functools import wraps

user_bp = Blueprint('user', __name__, url_prefix='/user')

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@user_bp.route('/dashboard')
@login_required
@user_required
def dashboard():
    today = date.today()
    today_attendance = current_user.get_today_attendance()
    month_stats = current_user.get_month_stats()
    
    recent_attendance = Attendance.query.filter_by(user_id=current_user.id)\
        .order_by(Attendance.check_in.desc()).limit(10).all()
    
    pending_leaves = LeaveRequest.query.filter_by(
        user_id=current_user.id, status='pending'
    ).count()
    
    return render_template('user/dashboard.html',
        today_attendance=today_attendance,
        month_stats=month_stats,
        recent_attendance=recent_attendance,
        pending_leaves=pending_leaves,
        today=today
    )

@user_bp.route('/check-in', methods=['POST'])
@login_required
@user_required
def check_in():
    today = date.today()
    existing = Attendance.query.filter(
        Attendance.user_id == current_user.id,
        Attendance.date == today
    ).first()
    
    if existing:
        flash('You have already checked in today.', 'warning')
        return redirect(url_for('user.dashboard'))
    
    now = datetime.now()
    # Consider late if after 9:30 AM
    status = 'late' if now.hour > 9 or (now.hour == 9 and now.minute > 30) else 'present'
    
    attendance = Attendance(
        user_id=current_user.id,
        check_in=now,
        status=status,
        date=today
    )
    db.session.add(attendance)
    db.session.commit()
    
    if status == 'late':
        flash('Checked in successfully. Note: You are marked as late.', 'warning')
    else:
        flash('Checked in successfully!', 'success')
    return redirect(url_for('user.dashboard'))

@user_bp.route('/check-out', methods=['POST'])
@login_required
@user_required
def check_out():
    today = date.today()
    attendance = Attendance.query.filter(
        Attendance.user_id == current_user.id,
        Attendance.date == today
    ).first()
    
    if not attendance:
        flash('You have not checked in today.', 'warning')
        return redirect(url_for('user.dashboard'))
    
    if attendance.check_out:
        flash('You have already checked out today.', 'warning')
        return redirect(url_for('user.dashboard'))
    
    attendance.check_out = datetime.now()
    attendance.calculate_hours()
    db.session.commit()
    
    flash(f'Checked out successfully! Working hours: {attendance.working_hours}h', 'success')
    return redirect(url_for('user.dashboard'))

@user_bp.route('/attendance-history')
@login_required
@user_required
def attendance_history():
    page = request.args.get('page', 1, type=int)
    records = Attendance.query.filter_by(user_id=current_user.id)\
        .order_by(Attendance.check_in.desc())\
        .paginate(page=page, per_page=15, error_out=False)
    
    return render_template('user/attendance_history.html', records=records)

@user_bp.route('/leave-request', methods=['GET', 'POST'])
@login_required
@user_required
def leave_request():
    if request.method == 'POST':
        leave_type = request.form.get('leave_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        reason = request.form.get('reason', '').strip()
        
        if not all([leave_type, start_date, end_date, reason]):
            flash('All fields are required.', 'danger')
            return render_template('user/leave_request.html')
        
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return render_template('user/leave_request.html')
        
        if start > end:
            flash('Start date must be before end date.', 'danger')
            return render_template('user/leave_request.html')
        
        leave = LeaveRequest(
            user_id=current_user.id,
            leave_type=leave_type,
            start_date=start,
            end_date=end,
            reason=reason
        )
        db.session.add(leave)
        db.session.commit()
        
        flash('Leave request submitted successfully!', 'success')
        return redirect(url_for('user.my_leaves'))
    
    return render_template('user/leave_request.html')

@user_bp.route('/my-leaves')
@login_required
@user_required
def my_leaves():
    leaves = LeaveRequest.query.filter_by(user_id=current_user.id)\
        .order_by(LeaveRequest.created_at.desc()).all()
    return render_template('user/my_leaves.html', leaves=leaves)

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@user_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', current_user.full_name)
        current_user.phone = request.form.get('phone', current_user.phone)
        current_user.department = request.form.get('department', current_user.department)
        
        new_password = request.form.get('new_password', '')
        if new_password:
            if len(new_password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return render_template('user/profile.html')
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    
    return render_template('user/profile.html')
