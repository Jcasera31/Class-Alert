from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user, logout_user
from app.settings import bp
from app import db
from app.models import User


@bp.route('/')
@login_required
def view_settings():
    """Display settings page"""
    return render_template('settings/settings.html')


@bp.route('/update', methods=['POST'])
@login_required
def update_settings():
    """Update user account settings"""
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    
    if not username or not email:
        flash('Username and email are required.', 'danger')
        return redirect(url_for('settings.view_settings'))
    
    # Check if username is taken by another user
    if username != current_user.username:
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken.', 'danger')
            return redirect(url_for('settings.view_settings'))
    
    # Check if email is taken by another user
    if email != current_user.email:
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('settings.view_settings'))
    
    # Update user info
    current_user.username = username
    current_user.email = email
    
    # Update password if provided
    if password:
        current_user.set_password(password)
    
    db.session.commit()
    
    flash('Settings updated successfully!', 'success')
    return redirect(url_for('settings.view_settings'))


@bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account"""
    user = current_user
    
    # Log out user
    logout_user()
    
    # Delete user (cascades to schedules, notifications, files)
    db.session.delete(user)
    db.session.commit()
    
    flash('Your account has been deleted.', 'info')
    return redirect(url_for('auth.login'))
