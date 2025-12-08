from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user
from app.auth import bp
from app import db
from app.models import User
from urllib.parse import urlencode
import os


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please provide both email and password.', 'danger')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect to next page if specified
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.home'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not username or not email or not password:
            flash('Please fill in all fields.', 'danger')
            return render_template('auth/register.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Alternative signup route"""
    return register()


@bp.route('/logout')
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/google-login')
def google_login():
    """Initiate Google OAuth login"""
    # This is a placeholder - you'll need to set up Google OAuth credentials
    # For now, redirect to regular login
    flash('Google OAuth not configured yet. Please use email/password login.', 'warning')
    return redirect(url_for('auth.login'))


@bp.route('/google-callback')
def google_callback():
    """Handle Google OAuth callback"""
    # This is a placeholder for Google OAuth callback
    flash('Google OAuth not configured yet.', 'warning')
    return redirect(url_for('auth.login'))
