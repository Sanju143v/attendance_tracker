import os

basedir = os.path.abspath(os.path.dirname(__file__))

# Vercel serverless can only write to /tmp
if os.environ.get('VERCEL'):
    db_path = '/tmp/attendance.db'
else:
    db_path = os.path.join(basedir, 'attendance.db')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'attendance-tracker-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + db_path
    SQLALCHEMY_TRACK_MODIFICATIONS = False
