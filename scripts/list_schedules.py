from app import create_app, db
from app.models import Schedule, User

app = create_app()
with app.app_context():
    user = User.query.filter_by(email='test@example.com').first()
    if not user:
        print('No test user')
    else:
        scheds = Schedule.query.filter_by(user_id=user.id).order_by(Schedule.created_at.desc()).limit(10).all()
        print(f'Found {len(scheds)} schedules for {user.username}:')
        for s in scheds:
            print(s.id, s.subject, s.days, s.time, s.alarm_enabled, s.alarm_offset_minutes, s.created_at)
