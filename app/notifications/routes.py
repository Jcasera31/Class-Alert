from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.notifications import bp
from app import db, socketio
from app.models import Notification, Schedule


def _parse_start_time(time_str: str):
    """Return datetime.time parsed from a range string like "01:00 PM - 02:30 PM"."""
    if not time_str:
        return None
    start_part = time_str.split('-')[0].strip()
    for fmt in ("%I:%M %p", "%I:%M%p"):
        try:
            return datetime.strptime(start_part, fmt).time()
        except ValueError:
            continue
    return None


def _should_notify_today(schedule: Schedule, now: datetime):
    day_map = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    today_abbr = day_map[now.weekday()]
    days_field = (schedule.days or '').lower()
    return today_abbr.lower() in days_field


def _create_upcoming_notifications_for_user(user_id: int):
    now = datetime.now()
    schedules = Schedule.query.filter_by(user_id=user_id, alarm_enabled=True).all()
    for sched in schedules:
        if not _should_notify_today(sched, now):
            continue

        start_time = _parse_start_time(sched.time or '')
        if not start_time:
            continue

        start_dt = datetime.combine(now.date(), start_time)
        delta_minutes = (start_dt - now).total_seconds() / 60
        if delta_minutes < 0:
            continue  # already started/passed

        if delta_minutes <= 60:  # within an hour
            mins = max(1, int(delta_minutes))
            message = f"Upcoming class: {sched.subject} at {sched.time} today (starts in {mins} min)"

            # Avoid duplicate notifications for the same message on the same day
            recent = Notification.query.filter_by(user_id=user_id, message=message).order_by(Notification.timestamp.desc()).first()
            if recent and recent.timestamp.date() == now.date():
                continue

            notification = Notification(
                user_id=user_id,
                message=message,
                notification_type='info'
            )
            db.session.add(notification)
            db.session.commit()

            socketio.emit('new_notification', {
                'user_id': user_id,
                'message': message
            })


@bp.route('/')
@login_required
def view_notifications():
    """Display user notifications"""
    # Notifications are now created by the background scheduler
    # No need to create them on page view
    
    # Get all notifications for current user
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.timestamp.desc()
    ).all()
    
    # Mark all as read
    for notification in notifications:
        if not notification.is_read:
            notification.is_read = True
    
    db.session.commit()
    
    return render_template('dashboard/notifications.html', notifications=notifications)


@bp.route('/create', methods=['POST'])
@login_required
def create_notification():
    """Create a new notification (for testing)"""
    message = request.form.get('message', 'Test notification')
    
    notification = Notification(
        user_id=current_user.id,
        message=message,
        notification_type='info'
    )
    
    db.session.add(notification)
    db.session.commit()
    
    # Emit socket event
    socketio.emit('new_notification', {
        'user_id': current_user.id,
        'message': message
    })
    
    flash('Notification created!', 'success')
    return redirect(url_for('notifications.view_notifications'))


@bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark notification as read"""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Delete a notification"""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(notification)
    db.session.commit()
    
    flash('Notification deleted.', 'success')
    return redirect(url_for('notifications.view_notifications'))


@bp.route('/clear-all', methods=['POST'])
@login_required
def clear_all_notifications():
    """Delete all notifications except upcoming class notifications"""
    # Only delete notifications that are NOT about upcoming classes
    # Keep notifications that contain alarm emojis (🔔 or ⏰)
    Notification.query.filter(
        Notification.user_id == current_user.id,
        ~Notification.message.contains('🔔'),
        ~Notification.message.contains('⏰')
    ).delete(synchronize_session=False)
    db.session.commit()
    
    flash('Old notifications cleared. Upcoming class alerts preserved.', 'success')
    return redirect(url_for('notifications.view_notifications'))
