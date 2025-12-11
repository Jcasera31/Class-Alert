from app import create_app, db
from app.models import User, Notification, Schedule
from datetime import datetime, timedelta
from time import sleep

app = create_app()
with app.app_context():
    client = app.test_client()

    # Ensure test user exists
    user = User.query.filter_by(email='test@example.com').first()
    if not user:
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        print('Created test user')

    # Login via test client
    resp = client.post('/auth/login', data={'email': 'test@example.com', 'password': 'testpass'}, follow_redirects=True)
    print('Login status:', resp.status_code)

    # Create schedule a couple minutes from now
    start_dt = datetime.now() + timedelta(minutes=2)
    end_dt = start_dt + timedelta(hours=1)
    time_str = f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"
    day_map = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_abbr = day_map[start_dt.weekday()]

    form = {
        'subject': 'E2E TEST CLASS',
        'days': [day_abbr],
        'time': time_str,
        'semester': 'E2E',
        'academic_year': str(start_dt.year),
        'alarm_enabled': 'on',
        'alarm_offset': '1',
    }

    resp = client.post('/schedule/add', data=form, follow_redirects=True)
    print('Add schedule status:', resp.status_code)

    # Wait up to 180 seconds for notification to appear
    for i in range(36):
        notifs = Notification.query.filter_by(user_id=user.id).order_by(Notification.timestamp.desc()).all()
        if any('E2E TEST CLASS' in n.message or 'E2E TEST CLASS' in getattr(n, 'message', '') for n in notifs):
            print('Found notification(s):')
            for n in notifs[:5]:
                print(n.timestamp, n.message)
            break
        print('No notification yet, sleeping 5s...')
        sleep(5)
    else:
        print('No notification observed within 180s')
