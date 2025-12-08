# ClassAlert Web Application

A Flask-based web application for managing class schedules and alerts.

## Features

- **User Authentication**: Register, login, and manage user accounts
- **Schedule Management**: Add, edit, and delete class schedules
- **Notifications**: Real-time alerts for upcoming classes
- **File Upload**: Upload Certificate of Registration (COR) PDFs
- **Settings**: Update account information
- **Responsive Design**: Works on desktop and mobile devices

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository** (or navigate to the project directory)

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - Windows (PowerShell):
     ```powershell
     .\venv\Scripts\Activate
     ```
   - Windows (CMD):
     ```cmd
     venv\Scripts\activate.bat

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Set environment variables** (optional):
   Create a `.env` file in the root directory:
   ```
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///classalert.db
   FLASK_ENV=development
   ```

6. **Initialize the database**:
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

## Running the Application

### Development Mode

```bash
python app/run.py
```

Or using Flask CLI:
```bash
flask run
```

The application will be available at `http://localhost:5000`

### Production Mode

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

## Project Structure

```
class-alert/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models.py            # Database models
│   ├── run.py               # Application entry point
│   ├── auth/                # Authentication routes
│   ├── dashboard/           # Dashboard routes
│   ├── schedule/            # Schedule management routes
│   ├── upload/              # File upload routes
│   ├── settings/            # Settings routes
│   └── notifications/       # Notification routes
├── static/
│   ├── css/                 # Stylesheets
│   ├── js/                  # JavaScript files
│   ├── images/              # Images
│   └── audio/               # Audio files for alerts
├── templates/
│   ├── base.html            # Base template
│   ├── auth/                # Authentication templates
│   ├── dashboard/           # Dashboard templates
│   └── settings/            # Settings templates
├── config.py                # Configuration settings
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Usage

### First-time Setup

1. Start the application
2. Navigate to `http://localhost:5000/auth/register`
3. Create a new account
4. Log in with your credentials

### Adding Classes

1. Go to "My Schedule" from the dashboard
2. Click "Add Class"
3. Fill in the class details (subject, days, time, etc.)
4. Configure alarm settings
5. Click "Save"

### Uploading COR

1. Go to "Upload COR" from the dashboard
2. Select your PDF file
3. Click "Upload"
4. The file will be stored in your account

### Managing Settings

1. Click the menu button in the header
2. Select "Settings"
3. Update your username, email, or password
4. Click "Save Changes"

## Features in Detail

### Real-time Notifications

The application uses Flask-SocketIO to deliver real-time notifications for:
- Upcoming classes
- Schedule changes
- Important alerts

### Responsive Design

The UI is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones

### Security Features

- Password hashing with Werkzeug
- CSRF protection
- Secure session management
- SQL injection prevention

## Technologies Used

- **Backend**: Flask 3.0
- **Database**: SQLAlchemy with SQLite
- **Authentication**: Flask-Login
- **Real-time**: Flask-SocketIO
- **Frontend**: HTML5, CSS3, JavaScript
- **Icons**: Remix Icon

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on the repository.