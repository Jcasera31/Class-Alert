from flask import render_template, redirect, url_for, request, flash, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.upload import bp
from app import db
from app.models import UploadedFile
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
    """Handle file upload"""
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
    
    flash(f'File "{filename}" uploaded successfully!', 'success')
    return redirect(url_for('upload.upload_page'))


@bp.route('/files/<filename>')
@login_required
def uploaded_file(filename):
    """Serve uploaded file"""
    user_folder = os.path.join(current_app.root_path, '..', 'uploads', str(current_user.id))
    return send_from_directory(user_folder, filename)
