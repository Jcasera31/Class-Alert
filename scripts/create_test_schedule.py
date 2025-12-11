from app import create_app, db
from app.models import User, Schedule
from datetime import datetime, timedelta, timezone
import os

app = create_app()

with app.app_context():
    db.create_all()

    # Create or get test user
    user = User.query.filter_by(username='testuser').first()
    if not user:
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        print('Created test user')
    else:
        print('Found existing test user')

    # Build schedule time a few minutes from now (use timezone-aware UTC)
    start_dt = datetime.now(timezone.utc) + timedelta(minutes=3)
    end_dt = start_dt + timedelta(hours=1)
    time_str = f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"

    # Weekday abbreviation for today
    day_map = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_abbr = day_map[start_dt.weekday()]

    schedule = Schedule(
        user_id=user.id,
        subject='TEST CLASS - Alarm Check',
        days=day_abbr,
        time=time_str,
        semester='Test',
        academic_year=str(start_dt.year),
        alarm_enabled=True,
        alarm_offset_minutes=1  # custom offset 1 minute before for quick testing
    )
    db.session.add(schedule)
    db.session.commit()
    print(f'Created schedule {schedule.id} starting at {time_str} on {day_abbr}')
