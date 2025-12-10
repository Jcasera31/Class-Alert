"""
Background scheduler for class notifications
Checks every minute and sends alerts at:
- 1 hour before class
- 30 minutes before class
- At class start time
"""

from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

# Global references
_app = None
_socketio = None
scheduler = BackgroundScheduler()


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


def _should_notify_today(schedule, now: datetime):
    """Check if schedule is for today."""
    day_map = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    today_abbr = day_map[now.weekday()]
    days_field = (schedule.days or '').lower()
    return today_abbr.lower() in days_field


def check_and_send_notifications():
    """Check all schedules and send notifications at appropriate times."""
    if not _app or not _socketio:
        return
    
    from app.models import Schedule, Notification
    from app import db
    
    with _app.app_context():
        now = datetime.now()
        
        # Clean up old notifications (older than 2 hours)
        cleanup_time = now - timedelta(hours=2)
        old_notifications = Notification.query.filter(
            Notification.timestamp < cleanup_time
        ).delete(synchronize_session=False)
        if old_notifications > 0:
            db.session.commit()
        
        # Get all enabled schedules
        schedules = Schedule.query.filter_by(alarm_enabled=True).all()
        
        print(f"\n[SCHEDULER] Checking {len(schedules)} enabled schedules at {now.strftime('%H:%M:%S')}")
        
        for sched in schedules:
            # Skip if not scheduled for today
            if not _should_notify_today(sched, now):
                print(f"  ⏭️ Skipping {sched.subject} - not scheduled for {now.strftime('%a')}, days: {sched.days}")
                continue
            
            print(f"  ✓ Checking {sched.subject} - time: {sched.time}")
            
            # Parse start time
            start_time = _parse_start_time(sched.time or '')
            if not start_time:
                print(f"    ❌ Failed to parse time: {sched.time}")
                continue
            
            print(f"    ✓ Parsed start time: {start_time}")
            
            # Create datetime for class start
            start_dt = datetime.combine(now.date(), start_time)
            
            # Calculate time difference in minutes
            delta_minutes = (start_dt - now).total_seconds() / 60
            
            print(f"    ⏱️ Delta: {delta_minutes:.1f} minutes")
            
            # Clean up notifications for this class if it's already passed by 5+ minutes
            if delta_minutes < -5:
                # Delete old notifications for this subject
                Notification.query.filter(
                    Notification.user_id == sched.user_id,
                    Notification.message.like(f"%{sched.subject}%")
                ).delete(synchronize_session=False)
                db.session.commit()
                print(f"    🗑️ Class passed, cleaned up old notifications")
                continue
            
            # Determine notification times based on alarm offset
            offset = sched.alarm_offset_minutes or 30
            notification_times = []
            
            # Check if we should send notifications based on time windows
            # Use wider windows to catch the notification once
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Always notify at class start time
            if -1 <= delta_minutes <= 1:  # Within 1 minute of start
                # Check if we already sent a "starting now" notification for this class at this time today
                existing = Notification.query.filter(
                    Notification.user_id == sched.user_id,
                    Notification.message == f"🔔 CLASS STARTING NOW: {sched.subject} at {sched.time}",
                    Notification.timestamp >= today_start
                ).first()
                
                if not existing:
                    notification_times.append({
                        'message': f"🔔 CLASS STARTING NOW: {sched.subject} at {sched.time}",
                        'type': 'warning'
                    })
            
            # Notify at 30 minutes before
            if 29 <= delta_minutes <= 31:
                # Check if we already sent a "30 minutes" notification for this class at this time today
                existing = Notification.query.filter(
                    Notification.user_id == sched.user_id,
                    Notification.message == f"⏰ Class in 30 minutes: {sched.subject} at {sched.time}",
                    Notification.timestamp >= today_start
                ).first()
                
                if not existing:
                    notification_times.append({
                        'message': f"⏰ Class in 30 minutes: {sched.subject} at {sched.time}",
                        'type': 'info'
                    })
            
            # Notify at 1 hour before
            if 59 <= delta_minutes <= 61:
                # Check if we already sent a "1 hour" notification for this class at this time today
                existing = Notification.query.filter(
                    Notification.user_id == sched.user_id,
                    Notification.message == f"⏰ Class in 1 hour: {sched.subject} at {sched.time}",
                    Notification.timestamp >= today_start
                ).first()
                
                if not existing:
                    notification_times.append({
                        'message': f"⏰ Class in 1 hour: {sched.subject} at {sched.time}",
                        'type': 'info'
                    })
            
            # Send notifications
            for notif_data in notification_times:
                # Create notification
                notification = Notification(
                    user_id=sched.user_id,
                    message=notif_data['message'],
                    notification_type=notif_data['type']
                )
                db.session.add(notification)
                db.session.commit()
                
                # Emit socket event for real-time notification
                try:
                    _socketio.emit('new_notification', {
                        'user_id': sched.user_id,
                        'message': notif_data['message'],
                        'type': notif_data['type']
                    })
                except:
                    pass  # Socket might not be connected


def start_scheduler(app, socketio):
    """Start the background scheduler."""
    global _app, _socketio
    _app = app
    _socketio = socketio
    
    if not scheduler.running:
        scheduler.add_job(
            func=check_and_send_notifications,
            trigger="interval",
            minutes=1,  # Check every minute
            id='class_notifications',
            name='Check and send class notifications',
            replace_existing=True
        )
        scheduler.start()
        print("✓ Background scheduler started - checking for class notifications every minute")


def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        print("✓ Background scheduler stopped")
