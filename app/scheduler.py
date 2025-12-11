"""
Background scheduler for class notifications
Two modes:
- Per-occurrence persistent jobs (preferred): uses APScheduler jobstore to schedule exact notifications
- Fallback interval check: scans schedules periodically to catch missed events

Notifications fired by jobs create Notification rows and emit socket events. Jobs are re-scheduled for the next weekly occurrence.
"""

from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.date import DateTrigger
import math
import traceback

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
    # Convert UTC `now` to local timezone to evaluate the schedule's local weekday
    try:
        local_tz = datetime.now().astimezone().tzinfo
        local_now = now.astimezone(local_tz)
    except Exception:
        local_now = now

    day_map = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    today_abbr = day_map[local_now.weekday()]
    days_field = (schedule.days or '').lower()
    return today_abbr.lower() in days_field


def _next_start_datetime_for_schedule(schedule, from_dt: datetime):
    """Return next datetime for the schedule start at or after from_dt (search up to 14 days)."""
    start_time = _parse_start_time(schedule.time or '')
    if not start_time:
        return None

    # Normalize days list into set of weekday indices
    day_map = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}
    days_field = (schedule.days or '').lower()
    days = [d.strip() for d in days_field.replace(',', ' ').split() if d.strip()]
    target_weekdays = [day_map.get(d[:3]) for d in days if d[:3] in day_map]

    # If no days specified, assume any day
    if not target_weekdays:
        target_weekdays = list(range(7))

    # Determine local timezone
    try:
        local_tz = datetime.now().astimezone().tzinfo
    except Exception:
        local_tz = timezone.utc

    # Search next 14 days for matching weekday
    for delta in range(0, 14):
        candidate_date = (from_dt + timedelta(days=delta)).date()
        if candidate_date.weekday() in target_weekdays:
            # Combine with schedule's start_time in local timezone
            candidate_local = datetime.combine(candidate_date, start_time)
            # Attach local tz and convert to UTC
            try:
                candidate_local = candidate_local.replace(tzinfo=local_tz)
                candidate_utc = candidate_local.astimezone(timezone.utc)
            except Exception:
                # Fallback: treat as naive UTC
                candidate_utc = datetime.combine(candidate_date, start_time).replace(tzinfo=timezone.utc)

            if candidate_utc >= from_dt.astimezone(timezone.utc):
                return candidate_utc
    return None


def _job_id_for(schedule_id: int, seconds_before: int):
    return f"sched_{schedule_id}_{int(seconds_before)}"


def _fire_notification(schedule_id: int, seconds_before: int):
    """Job handler: create notification for schedule and re-schedule next week's job."""
    try:
        from app import db
        from app.models import Schedule, Notification
        global _app, _socketio
        if not _app:
            return

        with _app.app_context():
            sched = Schedule.query.get(schedule_id)
            if not sched or not sched.alarm_enabled:
                return

            # Build message
            if seconds_before == 0:
                msg = f"🔔 CLASS STARTING NOW: {sched.subject} at {sched.time}"
                ntype = 'warning'
            elif seconds_before == 1800:
                msg = f"⏰ Class in 30 minutes: {sched.subject} at {sched.time}"
                ntype = 'info'
            elif seconds_before == 3600:
                msg = f"⏰ Class in 1 hour: {sched.subject} at {sched.time}"
                ntype = 'info'
            else:
                mins = int(seconds_before / 60)
                msg = f"⏰ Class in {mins} minutes: {sched.subject} at {sched.time}"
                ntype = 'info'

            # Avoid duplicates today (use UTC-aware start of day)
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            existing = Notification.query.filter(
                Notification.user_id == sched.user_id,
                Notification.message == msg,
                Notification.timestamp >= today_start
            ).first()
            if existing:
                return

            notification = Notification(
                user_id=sched.user_id,
                message=msg,
                notification_type=ntype
            )
            db.session.add(notification)
            db.session.commit()

            try:
                _socketio.emit('new_notification', {
                    'user_id': sched.user_id,
                    'message': msg,
                    'type': ntype
                })
            except Exception:
                pass

            # Reschedule this job for next week's same weekday (use UTC)
            next_start = _next_start_datetime_for_schedule(sched, datetime.now(timezone.utc) + timedelta(days=1))
            if next_start:
                run_date = next_start - timedelta(seconds=seconds_before)
                job_id = _job_id_for(schedule_id, seconds_before)
                try:
                    scheduler.add_job(
                        func=_fire_notification,
                        trigger=DateTrigger(run_date=run_date),
                        args=[schedule_id, seconds_before],
                        id=job_id,
                        replace_existing=True
                    )
                except Exception:
                    traceback.print_exc()
    except Exception:
        traceback.print_exc()


def check_and_send_notifications():
    """Check all schedules and send notifications at appropriate times."""
    # Allow the scheduler to run without a SocketIO instance (worker mode).
    if not _app:
        return
    
    from app.models import Schedule, Notification
    from app import db
    
    with _app.app_context():
        # Use timezone-aware UTC now for calculations
        now = datetime.now(timezone.utc)
        
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
            # Determine next start in UTC for this schedule
            next_start = _next_start_datetime_for_schedule(sched, now)
            if not next_start:
                print(f"  ⏭️ Skipping {sched.subject} - no upcoming occurrence found, days: {sched.days}")
                continue

            # Skip if not scheduled for today in local timezone
            if not _should_notify_today(sched, now):
                try:
                    local_tz = datetime.now().astimezone().tzinfo
                    local_next = next_start.astimezone(local_tz)
                    print(f"  ⏭️ Skipping {sched.subject} - not scheduled for {local_next.strftime('%a')}, days: {sched.days}")
                except Exception:
                    print(f"  ⏭️ Skipping {sched.subject} - not scheduled today, days: {sched.days}")
                continue

            print(f"  ✓ Checking {sched.subject} - time: {sched.time}")
            # Calculate time difference in seconds relative to UTC now
            delta_seconds = (next_start - now).total_seconds()
            print(f"    ⏱️ Delta: {delta_seconds:.1f} seconds (until next start UTC: {next_start.isoformat()})")
            
            # Clean up notifications for this class if it's already passed by 5+ minutes
            if delta_seconds < -300:  # older than 5 minutes
                # Delete old notifications for this subject
                Notification.query.filter(
                    Notification.user_id == sched.user_id,
                    Notification.message.like(f"%{sched.subject}%")
                ).delete(synchronize_session=False)
                db.session.commit()
                print(f"    🗑️ Class passed, cleaned up old notifications")
                continue
            
            # Determine notification times based on fixed offsets (in seconds)
            notification_times = []
            # Standard targets: 1 hour, 30 minutes, and start
            targets = [3600, 1800, 0]
            # Include custom alarm offset if provided (in minutes)
            try:
                custom_offset = int(sched.alarm_offset_minutes) if sched.alarm_offset_minutes is not None else None
            except Exception:
                custom_offset = None
            if custom_offset is not None and custom_offset not in (60, 30):
                # convert minutes to seconds
                targets.append(custom_offset * 60)

            # Threshold is half the check interval (we will run every 5 seconds)
            threshold = 4  # seconds
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            for t in targets:
                # Check if delta_seconds is within threshold of target t
                if abs(delta_seconds - t) <= threshold:
                    # Build message depending on t
                    if t == 0:
                        msg = f"🔔 CLASS STARTING NOW: {sched.subject} at {sched.time}"
                        ntype = 'warning'
                    elif t == 1800:
                        msg = f"⏰ Class in 30 minutes: {sched.subject} at {sched.time}"
                        ntype = 'info'
                    elif t == 3600:
                        msg = f"⏰ Class in 1 hour: {sched.subject} at {sched.time}"
                        ntype = 'info'
                    else:
                        mins = int(t / 60)
                        msg = f"⏰ Class in {mins} minutes: {sched.subject} at {sched.time}"
                        ntype = 'info'

                    # Ensure we didn't already send this exact message today
                    existing = Notification.query.filter(
                        Notification.user_id == sched.user_id,
                        Notification.message == msg,
                        Notification.timestamp >= today_start
                    ).first()

                    if not existing:
                        notification_times.append({'message': msg, 'type': ntype})
            
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
                except Exception:
                    pass  # Socket might not be connected


def start_scheduler(app, socketio):
    """Start the background scheduler."""
    global _app, _socketio
    _app = app
    _socketio = socketio
    
    if not scheduler.running:
        # Try to configure a persistent jobstore using the application's DB URI.
        try:
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
            if db_uri and 'default' not in getattr(scheduler, '_jobstores', {}):
                scheduler.add_jobstore(SQLAlchemyJobStore(url=db_uri), 'default')
                print(f"✓ APScheduler jobstore configured with: {db_uri}")
        except Exception:
            traceback.print_exc()

        # Interval fallback to catch missed events and support demo/serverless setups.
        scheduler.add_job(
            func=check_and_send_notifications,
            trigger="interval",
            seconds=5,  # Check every 5 seconds for alarm-like precision
            id='class_notifications',
            name='Check and send class notifications',
            replace_existing=True
        )

        scheduler.start()
        print("✓ Background scheduler started - checking for class notifications every 5 seconds")

        # Schedule per-occurrence jobs for existing enabled schedules (if any)
        try:
            from app.models import Schedule
            with app.app_context():
                schedules = Schedule.query.filter_by(alarm_enabled=True).all()
                for s in schedules:
                    try:
                        schedule_jobs_for_schedule(s)
                    except Exception:
                        traceback.print_exc()
        except Exception:
            # models may not be available in some contexts
            pass


def schedule_jobs_for_schedule(schedule):
    """Create per-occurrence DateTrigger jobs for the next matching occurrence of a schedule.

    This schedules jobs for the standard targets: 1 hour (3600s), 30 minutes (1800s), start (0s),
    and any custom `alarm_offset_minutes` configured on the schedule (if provided and not duplicate).
    """
    if not schedule or not getattr(schedule, 'id', None):
        return

    try:
        now = datetime.now(timezone.utc)
        next_start = _next_start_datetime_for_schedule(schedule, now)
        if not next_start:
            return

        # Standard targets
        targets = [3600, 1800, 0]
        try:
            custom_offset = int(schedule.alarm_offset_minutes) if schedule.alarm_offset_minutes is not None else None
        except Exception:
            custom_offset = None
        if custom_offset is not None and custom_offset * 60 not in targets:
            targets.append(custom_offset * 60)

        for t in targets:
            run_date = next_start - timedelta(seconds=t)
            # don't schedule jobs in the past
            if run_date < now - timedelta(seconds=5):
                continue

            job_id = _job_id_for(schedule.id, t)
            try:
                scheduler.add_job(
                    func=_fire_notification,
                    trigger=DateTrigger(run_date=run_date),
                    args=[schedule.id, t],
                    id=job_id,
                    replace_existing=True
                )
                print(f"Scheduled job {job_id} at {run_date} for schedule {schedule.id}")
            except Exception:
                traceback.print_exc()
    except Exception:
        traceback.print_exc()


def remove_jobs_for_schedule(schedule_id: int):
    """Remove any scheduled jobs associated with a schedule id."""
    if not schedule_id:
        return

    try:
        # Remove jobs by id pattern
        jobs = list(scheduler.get_jobs())
        for j in jobs:
            if str(j.id).startswith(f"sched_{schedule_id}_"):
                try:
                    scheduler.remove_job(j.id)
                    print(f"Removed job {j.id} for schedule {schedule_id}")
                except Exception:
                    traceback.print_exc()
    except Exception:
        traceback.print_exc()


def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        print("✓ Background scheduler stopped")
