from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    """User model for authentication and profile"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    
    # Google OAuth fields
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    profile_pic = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    schedules = db.relationship('Schedule', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    uploaded_files = db.relationship('UploadedFile', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Schedule(db.Model):
    """Schedule model for class timings"""
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    subject = db.Column(db.String(200), nullable=False)
    days = db.Column(db.String(100), nullable=True)  # e.g., "Mon, Wed, Fri"
    time = db.Column(db.String(50), nullable=True)   # e.g., "9:00 AM - 10:30 AM"
    
    semester = db.Column(db.String(50), nullable=True)  # e.g., "1st Semester"
    academic_year = db.Column(db.String(50), nullable=True)  # e.g., "AY 2024-2025"
    
    # Alarm settings
    alarm_enabled = db.Column(db.Boolean, default=True)
    alarm_offset_minutes = db.Column(db.Integer, default=30)  # minutes before class
    custom_alarm_time = db.Column(db.String(20), nullable=True)  # e.g., "08:30 AM"
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Schedule {self.subject} - {self.time}>'


class Notification(db.Model):
    """Notification model for alerts"""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    notification_type = db.Column(db.String(50), default='info')  # info, warning, success, danger
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<Notification {self.id} - {self.message[:30]}>'


class UploadedFile(db.Model):
    """Model for tracking uploaded COR files"""
    __tablename__ = 'uploaded_files'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)  # in bytes
    
    semester = db.Column(db.String(50), nullable=True)
    academic_year = db.Column(db.String(50), nullable=True)
    
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<UploadedFile {self.filename}>'
