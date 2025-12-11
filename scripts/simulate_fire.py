from app import create_app, socketio
import app.scheduler as sched

app = create_app()
# Inject app and socketio into scheduler module
sched._app = app
sched._socketio = socketio

with app.app_context():
    # Fire notification for schedule id 1, 60 seconds before (custom)
    sched._fire_notification(1, 60)
    print('Simulated _fire_notification(1, 60)')
