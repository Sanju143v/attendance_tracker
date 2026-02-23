from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import User, Attendance, LeaveRequest
from app import db
from datetime import datetime, date, timedelta
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    today = date.today()
    
    total_users = User.query.filter_by(role='user').count()
    approved_users = User.query.filter_by(role='user', is_approved=True).count()
    pending_users = User.query.filter_by(role='user', is_approved=False).count()
    
    today_checkins = Attendance.query.filter(Attendance.date == today).count()
    pending_leaves = LeaveRequest.query.filter_by(status='pending').count()
    
    recent_attendance = Attendance.query.join(User)\
        .order_by(Attendance.check_in.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
        total_users=total_users,
        approved_users=approved_users,
        pending_users=pending_users,
        today_checkins=today_checkins,
        pending_leaves=pending_leaves,
        recent_attendance=recent_attendance,
        today=today
    )

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    status_filter = request.args.get('status', 'all')
    
    query = User.query.filter_by(role='user')
    if status_filter == 'approved':
        query = query.filter_by(is_approved=True)
    elif status_filter == 'pending':
        query = query.filter_by(is_approved=False)
    
    users = query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users, status_filter=status_filter)

@admin_bp.route('/users/<int:user_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f'{user.full_name} has been approved.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'{user.full_name} has been removed.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_approved = not user.is_approved
    db.session.commit()
    status = 'activated' if user.is_approved else 'deactivated'
    flash(f'{user.full_name} has been {status}.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/attendance')
@login_required
@admin_required
def view_attendance():
    selected_date = request.args.get('date', date.today().isoformat())
    try:
        filter_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        filter_date = date.today()
    
    records = Attendance.query.join(User)\
        .filter(Attendance.date == filter_date)\
        .order_by(Attendance.check_in.desc()).all()
    
    # Get users who haven't checked in
    checked_in_ids = [r.user_id for r in records]
    absent_users = User.query.filter(
        User.role == 'user',
        User.is_approved == True,
        ~User.id.in_(checked_in_ids) if checked_in_ids else True
    ).all()
    
    return render_template('admin/attendance.html',
        records=records,
        absent_users=absent_users,
        selected_date=filter_date
    )

@admin_bp.route('/attendance/report')
@login_required
@admin_required
def attendance_report():
    month = request.args.get('month', date.today().month, type=int)
    year = request.args.get('year', date.today().year, type=int)
    
    users = User.query.filter_by(role='user', is_approved=True).all()
    report_data = []
    
    for user in users:
        stats = user.get_month_stats(year, month)
        report_data.append({
            'user': user,
            'stats': stats
        })
    
    return render_template('admin/report.html',
        report_data=report_data,
        month=month,
        year=year
    )

@admin_bp.route('/leaves')
@login_required
@admin_required
def manage_leaves():
    status_filter = request.args.get('status', 'pending')
    
    query = LeaveRequest.query.join(User)
    if status_filter != 'all':
        query = query.filter(LeaveRequest.status == status_filter)
    
    leaves = query.order_by(LeaveRequest.created_at.desc()).all()
    return render_template('admin/leaves.html', leaves=leaves, status_filter=status_filter)

@admin_bp.route('/leaves/<int:leave_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    leave.status = 'approved'
    leave.admin_remarks = request.form.get('remarks', '')
    leave.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Leave request approved.', 'success')
    return redirect(url_for('admin.manage_leaves'))

@admin_bp.route('/leaves/<int:leave_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    leave.status = 'rejected'
    leave.admin_remarks = request.form.get('remarks', '')
    leave.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Leave request rejected.', 'info')
    return redirect(url_for('admin.manage_leaves'))

@admin_bp.route('/api/dashboard-stats')
@login_required
@admin_required
def dashboard_stats():
    today = date.today()
    
    total_users = User.query.filter_by(role='user', is_approved=True).count()
    today_present = Attendance.query.filter(Attendance.date == today).count()
    today_late = Attendance.query.filter(
        Attendance.date == today, Attendance.status == 'late'
    ).count()
    pending_leaves = LeaveRequest.query.filter_by(status='pending').count()
    
    # Weekly trend
    week_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        count = Attendance.query.filter(Attendance.date == d).count()
        week_data.append({
            'date': d.strftime('%a'),
            'count': count
        })
    
    return jsonify({
        'total_users': total_users,
        'today_present': today_present,
        'today_late': today_late,
        'today_absent': max(0, total_users - today_present),
        'pending_leaves': pending_leaves,
        'week_trend': week_data
    })
