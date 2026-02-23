from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'user')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if role == 'admin' and not user.is_admin():
                flash('You do not have admin privileges.', 'danger')
                return render_template('auth/login.html')
            
            if not user.is_approved and not user.is_admin():
                flash('Your account is pending approval. Please contact the administrator.', 'warning')
                return render_template('auth/login.html')
            
            login_user(user, remember=True)
            next_page = request.args.get('next')
            if user.is_admin():
                return redirect(next_page or url_for('admin.dashboard'))
            return redirect(next_page or url_for('user.dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        department = request.form.get('department', 'General')
        phone = request.form.get('phone', '')
        
        # Validations
        if not all([username, email, full_name, password]):
            flash('All fields are required.', 'danger')
            return render_template('auth/signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/signup.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('auth/signup.html')
        
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            department=department,
            phone=phone,
            role='user',
            is_approved=False
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! Please wait for admin approval.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
