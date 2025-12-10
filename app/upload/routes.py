from flask import render_template, redirect, url_for, request, flash, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.upload import bp
from app import db
from app.models import UploadedFile, Schedule
from app.utils.pdf_parser import parse_cor_pdf
import os


ALLOWED_EXTENSIONS = {'pdf', 'PDF'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@bp.route('/')
@login_required
def upload_page():
    """Display upload page with list of uploaded files"""
    # Get user's uploaded files
    files_db = UploadedFile.query.filter_by(user_id=current_user.id).order_by(
        UploadedFile.uploaded_at.desc()
    ).all()
    
    # Get filenames
    files = [f.filename for f in files_db]
    
    return render_template('dashboard/upload.html', files=files)


@bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload and automatically extract schedule data"""
    if 'file' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('upload.upload_page'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('upload.upload_page'))
    
    if not allowed_file(file.filename):
        flash('Only PDF files are allowed.', 'danger')
        return redirect(url_for('upload.upload_page'))
    
    # Secure filename and save
    filename = secure_filename(file.filename)
    
    # Create uploads directory if it doesn't exist
    upload_folder = os.path.join(current_app.root_path, '..', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Create user-specific folder
    user_folder = os.path.join(upload_folder, str(current_user.id))
    os.makedirs(user_folder, exist_ok=True)
    
    # Save file
    filepath = os.path.join(user_folder, filename)
    file.save(filepath)
    
    # Get file size
    file_size = os.path.getsize(filepath)
    
    # Save to database
    uploaded_file = UploadedFile(
        user_id=current_user.id,
        filename=filename,
        filepath=filepath,
        file_size=file_size
    )
    
    db.session.add(uploaded_file)
    db.session.commit()
    
    # Parse PDF and extract schedule data
    try:
        schedules = parse_cor_pdf(filepath)
        
        if schedules:
            added_count = 0
            for sched_data in schedules:
                # Check if schedule already exists
                existing = Schedule.query.filter_by(
                    user_id=current_user.id,
                    subject=sched_data['subject'],
                    days=sched_data['days'],
                    time=sched_data['time']
                ).first()
                
                if not existing:
                    # Create new schedule entry
                    schedule = Schedule(
                        user_id=current_user.id,
                        subject=sched_data['subject'],
                        days=sched_data['days'],
                        time=sched_data['time'],
                        semester=sched_data.get('semester', ''),
                        academic_year=sched_data.get('academic_year', ''),
                        alarm_enabled=True,
                        alarm_offset_minutes=30
                    )
                    db.session.add(schedule)
                    added_count += 1
            
            db.session.commit()
            
            flash(f'File "{filename}" uploaded successfully! {added_count} schedule(s) extracted and added.', 'success')
            return redirect(url_for('schedule.view_schedules'))
        else:
            flash(f'File "{filename}" uploaded but no schedule data could be extracted. Please check the PDF format.', 'warning')
            return redirect(url_for('schedule.view_schedules'))
    
    except Exception as e:
        flash(f'File "{filename}" uploaded but PDF parsing failed: {str(e)}', 'warning')
        print(f"PDF parsing error: {e}")
        return redirect(url_for('schedule.view_schedules'))


@bp.route('/delete/<filename>', methods=['POST'])
@login_required
def delete_file(filename):
    """Delete an uploaded file"""
    # Get the file record from database
    uploaded_file = UploadedFile.query.filter_by(
        user_id=current_user.id,
        filename=filename
    ).first()
    
    if not uploaded_file:
        flash('File not found.', 'danger')
        return redirect(url_for('upload.upload_page'))
    
    # Delete file from filesystem
    try:
        if os.path.exists(uploaded_file.filepath):
            os.remove(uploaded_file.filepath)
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'danger')
        return redirect(url_for('upload.upload_page'))
    
    # Delete record from database
    db.session.delete(uploaded_file)
    db.session.commit()
    
    flash(f'File "{filename}" deleted successfully.', 'success')
    return redirect(url_for('upload.upload_page'))


@bp.route('/files/<filename>')
@login_required
def uploaded_file(filename):
    """Serve uploaded file"""
    user_folder = os.path.join(current_app.root_path, '..', 'uploads', str(current_user.id))
    return send_from_directory(user_folder, filename)
