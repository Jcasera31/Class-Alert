from app import create_app, socketio, db
from app.models import User, Schedule, Notification, UploadedFile

app = create_app()


@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell"""
    return {
        'db': db,
        'User': User,
        'Schedule': Schedule,
        'Notification': Notification,
        'UploadedFile': UploadedFile
    }


if __name__ == '__main__':
    # Run the application with SocketIO
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
