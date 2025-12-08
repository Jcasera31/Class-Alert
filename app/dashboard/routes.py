from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.dashboard import bp
from app.models import Schedule
from sqlalchemy import distinct


@bp.route('/')
@bp.route('/home')
@login_required
def home():
    """Dashboard home page"""
    return render_template('dashboard/home.html')


@bp.route('/cor-history')
@login_required
def cor_history():
    """Display COR upload history by semester"""
    # Get distinct semester/year combinations for current user
    records = db.session.query(
        distinct(Schedule.semester),
        Schedule.academic_year
    ).filter_by(user_id=current_user.id).all()
    
    # Format records for template
    formatted_records = [(sem, year) for sem, year in records if sem and year]
    
    return render_template('dashboard/cor_history.html', records=formatted_records)


# Import db here to avoid circular import
from app import db
