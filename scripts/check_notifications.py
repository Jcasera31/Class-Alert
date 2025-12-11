from app import create_app, db
from app.models import Notification, User

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='testuser').first()
    if not user:
        print('No test user found')
    else:
        notifs = Notification.query.filter_by(user_id=user.id).order_by(Notification.timestamp.desc()).all()
        print(f'Found {len(notifs)} notifications for user {user.username}:')
        for n in notifs:
            print(n.timestamp, n.message, n.notification_type)
