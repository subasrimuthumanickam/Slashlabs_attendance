import os
import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm

from app import db
from models import User,Department

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    
    # Create a simple form for CSRF protection
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        username = request.form.get('username')
        password = request.form.get('password')
        
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=remember)
        
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('auth.dashboard'))
    print("error", form.errors)
    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    
    # Create a simple form for CSRF protection
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        department = request.form.get('department')
        full_name = request.form.get('full_name')
        
        # Check if user already exists
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.', 'danger')
            return redirect(url_for('auth.register'))
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Create new user
        new_user = User(
            username=username, 
            email=email, 
            full_name=full_name,
            department_id=department if department else None,
            role='employee'
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    
    departments = Department.query.order_by(Department.name).all()
    return render_template('register.html', form=form, departments=departments)


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    
    # Get the user's attendance records
    from models import Attendance
    
    attendances = Attendance.query.filter_by(user_id=current_user.id).order_by(Attendance.check_in_time.desc()).limit(10).all()
    
    return render_template('dashboard.html', attendances=attendances)


@auth_bp.route('/reports')
@login_required
def reports():
    from models import Attendance
    from sqlalchemy import extract, func
    
    # Get attendance stats for the current month
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    
    monthly_attendance = Attendance.query.filter(
        Attendance.user_id == current_user.id,
        extract('month', Attendance.check_in_time) == current_month,
        extract('year', Attendance.check_in_time) == current_year
    ).all()
    
    # Count statistics
    total_days = len(monthly_attendance)
    present_days = sum(1 for a in monthly_attendance if a.status == 'present')
    late_days = sum(1 for a in monthly_attendance if a.status == 'late')
    absent_days = sum(1 for a in monthly_attendance if a.status == 'absent')
    
    # Get attendance by day of week
    day_stats = db.session.query(
        extract('dow', Attendance.check_in_time).label('day_of_week'),
        func.count(Attendance.id)
    ).filter(
        Attendance.user_id == current_user.id
    ).group_by('day_of_week').all()
    
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    day_counts = [0] * 7
    
    for day, count in day_stats:
        # PostgreSQL DOW is 0 (Sunday) to 6 (Saturday)
        day_counts[int(day)] = count
    
    return render_template(
        'reports.html',
        attendance_data={
            'total': total_days,
            'present': present_days,
            'late': late_days,
            'absent': absent_days
        },
        day_labels=days,
        day_counts=day_counts
    )
