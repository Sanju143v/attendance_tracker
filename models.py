from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    department = db.Column(db.String(100), default='General')
    phone = db.Column(db.String(20), default='')
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    attendances = db.relationship('Attendance', backref='user', lazy=True)
    leave_requests = db.relationship('LeaveRequest', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def get_today_attendance(self):
        today = date.today()
        return Attendance.query.filter(
            Attendance.user_id == self.id,
            db.func.date(Attendance.check_in) == today
        ).first()

    def get_month_stats(self, year=None, month=None):
        if not year:
            year = date.today().year
        if not month:
            month = date.today().month
        
        records = Attendance.query.filter(
            Attendance.user_id == self.id,
            db.extract('year', Attendance.check_in) == year,
            db.extract('month', Attendance.check_in) == month
        ).all()
        
        total_days = len(records)
        present_days = sum(1 for r in records if r.status == 'present')
        late_days = sum(1 for r in records if r.status == 'late')
        total_hours = sum(r.working_hours or 0 for r in records)
        
        return {
            'total_days': total_days,
            'present_days': present_days,
            'late_days': late_days,
            'absent_days': 0,
            'total_hours': round(total_hours, 2)
        }


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    check_out = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='present')  # present, late, absent, half-day
    working_hours = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text, default='')
    date = db.Column(db.Date, default=date.today)
    
    def calculate_hours(self):
        if self.check_in and self.check_out:
            diff = self.check_out - self.check_in
            self.working_hours = round(diff.total_seconds() / 3600, 2)
        return self.working_hours


class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)  # sick, casual, vacation
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    admin_remarks = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
