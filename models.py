import os
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
# Table create department
class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    users = db.relationship('User', backref='department', lazy=True)

    def __repr__(self):
        return f'<Department {self.name}>'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='employee')  # 'admin' or 'employee'
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    position = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with Attendance
    attendances = db.relationship('Attendance', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    check_in_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    check_out_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='present')  # 'present', 'absent', 'late'
    image_path = db.Column(db.String(255))
    location = db.Column(db.String(255))
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Attendance {self.id} - User {self.user_id}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
