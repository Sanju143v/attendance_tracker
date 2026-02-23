from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from routes.auth import auth_bp
    from routes.user import user_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        from models import User, Attendance, LeaveRequest
        db.create_all()
        # Create default admin if not exists
        _create_default_admin()

    return app

def _create_default_admin():
    from models import User
    admin = User.query.filter_by(email='admin@attendance.com').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@attendance.com',
            full_name='System Administrator',
            role='admin',
            department='Administration',
            is_approved=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
