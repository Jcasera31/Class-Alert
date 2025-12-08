from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.schedule import bp
from app import db
from app.models import Schedule
from sqlalchemy import distinct


@bp.route('/')
@bp.route('/schedules')
@login_required
def view_schedules():
    """View and filter class schedules"""
    # Get filter parameters
    search_query = request.args.get('q', '').strip()
    semester_filter = request.args.get('semester', '')
    
    # Base query
    query = Schedule.query.filter_by(user_id=current_user.id)
    
    # Apply search filter
    if search_query:
        query = query.filter(Schedule.subject.ilike(f'%{search_query}%'))
    
    # Apply semester/year filter
    selected_semester = None
    selected_year = None
    if semester_filter and '||' in semester_filter:
        selected_semester, selected_year = semester_filter.split('||')
        query = query.filter_by(semester=selected_semester, academic_year=selected_year)
    
    # Get schedules
    schedules = query.order_by(Schedule.created_at.desc()).all()
    
    # Get all available terms for filter dropdown
    terms = db.session.query(
        distinct(Schedule.semester),
        Schedule.academic_year
    ).filter_by(user_id=current_user.id).all()
    
    # Format terms
    terms = [(sem, year) for sem, year in terms if sem and year]
    
    return render_template(
        'dashboard/schedule.html',
        schedules=schedules,
        terms=terms,
        selected_semester=selected_semester,
        selected_year=selected_year,
        q=search_query
    )


@bp.route('/add', methods=['POST'])
@login_required
def add_schedule():
    """Add a new class schedule"""
    subject = request.form.get('subject', '').strip()
    days = request.form.get('days', '').strip()
    time = request.form.get('time', '').strip()
    semester = request.form.get('semester', '').strip()
    academic_year = request.form.get('academic_year', '').strip()
    
    alarm_enabled = request.form.get('alarm_enabled') == 'on'
    alarm_offset = request.form.get('alarm_offset', '30')
    custom_alarm_time = request.form.get('custom_alarm_time', '').strip()
    
    if not subject:
        flash('Subject is required.', 'danger')
        return redirect(url_for('schedule.view_schedules'))
    
    # Convert alarm_offset to integer
    try:
        alarm_offset = int(alarm_offset)
    except (ValueError, TypeError):
        alarm_offset = 30
    
    # Create new schedule
    schedule = Schedule(
        user_id=current_user.id,
        subject=subject,
        days=days,
        time=time,
        semester=semester,
        academic_year=academic_year,
        alarm_enabled=alarm_enabled,
        alarm_offset_minutes=alarm_offset,
        custom_alarm_time=custom_alarm_time if custom_alarm_time else None
    )
    
    db.session.add(schedule)
    db.session.commit()
    
    flash(f'Class "{subject}" added successfully!', 'success')
    return redirect(url_for('schedule.view_schedules'))


@bp.route('/edit/<int:schedule_id>', methods=['POST'])
@login_required
def edit_schedule(schedule_id):
    """Edit an existing class schedule"""
    schedule = Schedule.query.filter_by(id=schedule_id, user_id=current_user.id).first_or_404()
    
    schedule.subject = request.form.get('subject', '').strip()
    schedule.days = request.form.get('days', '').strip()
    schedule.time = request.form.get('time', '').strip()
    schedule.semester = request.form.get('semester', '').strip()
    schedule.academic_year = request.form.get('academic_year', '').strip()
    
    schedule.alarm_enabled = request.form.get('alarm_enabled') == 'on'
    
    alarm_offset = request.form.get('alarm_offset', '30')
    try:
        schedule.alarm_offset_minutes = int(alarm_offset)
    except (ValueError, TypeError):
        schedule.alarm_offset_minutes = 30
    
    custom_alarm_time = request.form.get('custom_alarm_time', '').strip()
    schedule.custom_alarm_time = custom_alarm_time if custom_alarm_time else None
    
    db.session.commit()
    
    flash(f'Class "{schedule.subject}" updated successfully!', 'success')
    return redirect(url_for('schedule.view_schedules'))


@bp.route('/delete/<int:schedule_id>', methods=['POST'])
@login_required
def delete_schedule_route(schedule_id):
    """Delete a class schedule"""
    schedule = Schedule.query.filter_by(id=schedule_id, user_id=current_user.id).first_or_404()
    
    subject_name = schedule.subject
    db.session.delete(schedule)
    db.session.commit()
    
    flash(f'Class "{subject_name}" deleted successfully.', 'success')
    return redirect(url_for('schedule.view_schedules'))
