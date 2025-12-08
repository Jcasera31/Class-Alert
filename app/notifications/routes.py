from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.notifications import bp
from app import db, socketio
from app.models import Notification
from datetime import datetime


@bp.route('/')
@login_required
def view_notifications():
    """Display user notifications"""
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
