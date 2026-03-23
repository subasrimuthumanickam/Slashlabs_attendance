import os
import datetime
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from models import User, Attendance
from utils import allowed_file, token_required

api_bp = Blueprint('api', __name__)


@api_bp.route('/login', methods=['POST'])
def api_login():
    auth = request.json
    
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'message': 'Authentication failed. Missing credentials.'}), 401
    
    user = User.query.filter_by(username=auth.get('username')).first()
    
    if not user or not user.check_password(auth.get('password')):
        return jsonify({'message': 'Authentication failed. Invalid credentials.'}), 401
    
    # Generate token
    from utils import generate_token
    token = generate_token(user.id)
    
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role
        }
    })


@api_bp.route('/attendance/check-in', methods=['POST'])
@token_required
def check_in(current_user):
    # Check if already checked in today
    today = datetime.datetime.now().date()
    existing_attendance = Attendance.query.filter(
        Attendance.user_id == current_user.id,
        db.func.date(Attendance.check_in_time) == today
    ).first()
    
    # if existing_attendance and not existing_attendance.check_out_time:
    #     return jsonify({'message': 'You are already checked in today.'}), 400

    if existing_attendance:
     return jsonify({'message': 'You have already checked in today.'}), 400
    
    # Process image upload
    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_path = f"uploads/{filename}"
    
    # Get location
    location = request.form.get('location', '')
    
    # Create new attendance record
    new_attendance = Attendance(
        user_id=current_user.id,
        check_in_time=datetime.datetime.now(),
        status=request.form.get('status', 'present'),
        image_path=image_path,
        location=location,
        notes=request.form.get('notes', '')
    )
    
    db.session.add(new_attendance)
    db.session.commit()
    
    return jsonify({
        'message': 'Check-in successful',
        'attendance': {
            'id': new_attendance.id,
            'check_in_time': new_attendance.check_in_time,
            'status': new_attendance.status
        }
    }), 201


@api_bp.route('/attendance/check-out', methods=['POST'])
@token_required
def check_out(current_user):
    # Find today's check-in
    today = datetime.datetime.now().date()
    attendance = Attendance.query.filter(
        Attendance.user_id == current_user.id,
        db.func.date(Attendance.check_in_time) == today,
        Attendance.check_out_time == None
    ).first()
    
    if not attendance:
        return jsonify({'message': 'No active check-in found for today.'}), 404
    
    # Update check-out time
    attendance.check_out_time = datetime.datetime.now()
    
    # Process image upload
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            attendance.image_path = f"uploads/{filename}"
    
    # Update notes if provided
    if request.form.get('notes'):
        attendance.notes = request.form.get('notes')
    
    db.session.commit()
    
    return jsonify({
        'message': 'Check-out successful',
        'attendance': {
            'id': attendance.id,
            'check_in_time': attendance.check_in_time,
            'check_out_time': attendance.check_out_time,
            'status': attendance.status
        }
    })


@api_bp.route('/attendance/history', methods=['GET'])
@token_required
def get_attendance_history(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Query with optional date filters
    query = Attendance.query.filter_by(user_id=current_user.id)
    
    if request.args.get('start_date'):
        start_date = datetime.datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
        query = query.filter(Attendance.check_in_time >= start_date)
    
    if request.args.get('end_date'):
        end_date = datetime.datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
        query = query.filter(Attendance.check_in_time <= end_date)
    
    # Sort by check-in time (newest first)
    query = query.order_by(Attendance.check_in_time.desc())
    
    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page)
    
    # Format the attendance data
    history = []
    for attendance in pagination.items:
        history.append({
            'id': attendance.id,
            'check_in_time': attendance.check_in_time.isoformat(),
            'check_out_time': attendance.check_out_time.isoformat() if attendance.check_out_time else None,
            'status': attendance.status,
            'image_path': attendance.image_path,
            'location': attendance.location,
            'notes': attendance.notes
        })
    
    return jsonify({
        'attendances': history,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@api_bp.route('/users/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'full_name': current_user.full_name,
        'role': current_user.role,
        'department': current_user.department.name if current_user.department else None,
        'position': current_user.position_rel.title if current_user.position_rel else None
    })


@api_bp.route('/users/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.json
    
    if data.get('email') and data['email'] != current_user.email:
        # Check if email already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already in use.'}), 400
        current_user.email = data['email']
    
    if data.get('full_name'):
        current_user.full_name = data['full_name']
    
    if data.get('password'):
        current_user.set_password(data['password'])
    
    db.session.commit()
    
    return jsonify({
        'message': 'Profile updated successfully',
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'full_name': current_user.full_name
        }
    })
