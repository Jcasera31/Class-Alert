Scheduler deployment notes

Overview
- For reliable alarms in production, run a dedicated scheduler worker process using a persistent database (Postgres recommended).
- Do NOT rely on Vercel or serverless to run the worker — they are ephemeral and won't persist jobs or background threads.

Steps
1) Provision a Postgres database and obtain a connection URL, e.g.:
   postgresql://<user>:<password>@<host>:5432/<database>

2) Update environment on your host:
   - Set `DATABASE_URL` or `SQLALCHEMY_DATABASE_URI` to the Postgres URL.
   - Ensure `SECRET_KEY` is set in production.

3) Install dependencies (ensure `psycopg2-binary` is available for Postgres):
   ```powershell
   & venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pip install psycopg2-binary
   ```

4) Run DB migrations or create tables:
   ```powershell
   & venv\Scripts\Activate.ps1
   python -c "from app import create_app, db; app=create_app();
from app import models; 
with app.app_context(): db.create_all()"
   ```

5) Run the scheduler worker on your server (systemd, supervisor, or Docker recommended):
   ```powershell
   & venv\Scripts\Activate.ps1
   setx DATABASE_URL "postgresql://..."
   python scheduler_worker.py
   ```

Notes
- The worker starts APScheduler with a `SQLAlchemyJobStore` using the app's `SQLALCHEMY_DATABASE_URI`.
- The web process (Flask) can still serve the UI; the worker solely runs the scheduler.
- Consider running the worker as a service (systemd on Linux) or in a container to ensure it restarts on failure.
- If you want SocketIO notifications to be emitted to connected clients, keep the web process running SocketIO; the worker will still create Notification rows in the DB.

Security
- Keep DB credentials secret; use environment variables and a secrets manager where possible.
- Use SSL/TLS for the DB connection if available.

If you want, I can also:
- Add a `systemd` unit or `docker-compose` snippet to run the worker.
- Add a small health endpoint to verify the worker is alive.

Docker Compose example
----------------------
Below is a quick example to run Postgres + web + worker locally using Docker Compose. Create a `docker-compose.yml` at the project root and use `docker compose up --build`.

systemd unit example
---------------------
Create a file `/etc/systemd/system/classalert-scheduler.service` with contents:

```
[Unit]
Description=ClassAlert Scheduler Worker
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/class-alert
Environment=SQLALCHEMY_DATABASE_URI=postgresql://user:pass@db:5432/classalert
Environment=SECRET_KEY=your-secret
ExecStart=/path/to/venv/bin/python /path/to/class-alert/scheduler_worker.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then enable and start:
```
sudo systemctl daemon-reload
sudo systemctl enable classalert-scheduler
sudo systemctl start classalert-scheduler
```

This will keep the scheduler worker running and restart it automatically if it fails.

---

Production Deployment Checklist
================================

Follow these steps to deploy ClassAlert with a production-grade scheduler on a Linux server.

### Prerequisites
- Linux server or VPS (DigitalOcean, Linode, AWS EC2, etc.)
- Postgres 12+
- Python 3.10+
- Git

### Step-by-Step Setup

#### 1. Clone and install

\\\ash
git clone https://github.com/Jcasera31/Class-Alert.git
cd Class-Alert
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install psycopg2-binary
\\\

#### 2. Configure environment

\\\ash
export DATABASE_URL="postgresql://user:pass@localhost:5432/classalert_db"
export SECRET_KEY="your-secure-key"
export FLASK_ENV="production"
\\\

#### 3. Create Postgres database

\\\ash
sudo su - postgres
psql
CREATE DATABASE classalert_db;
CREATE USER classalert_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE classalert_db TO classalert_user;
\q
\\\

#### 4. Initialize database

\\\ash
source venv/bin/activate
python -c "from app import create_app, db; from app import models; app = create_app(); app.app_context().push(); db.create_all()"
\\\

#### 5. Deploy scheduler as systemd service

Create /etc/systemd/system/classalert-scheduler.service:

\\\ini
[Unit]
Description=ClassAlert Scheduler Worker
After=network.target postgresql.service

[Service]
Type=simple
User=classalert
WorkingDirectory=/path/to/Class-Alert
Environment="PATH=/path/to/Class-Alert/venv/bin"
Environment="DATABASE_URL=postgresql://user:pass@localhost:5432/classalert_db"
Environment="SECRET_KEY=your-secure-key"
ExecStart=/path/to/Class-Alert/venv/bin/python /path/to/Class-Alert/scheduler_worker.py
Restart=always

[Install]
WantedBy=multi-user.target
\\\

Then:

\\\ash
sudo systemctl daemon-reload
sudo systemctl enable classalert-scheduler
sudo systemctl start classalert-scheduler
sudo systemctl status classalert-scheduler
\\\

#### 6. Monitor and maintain

\\\ash
# Check status
sudo systemctl status classalert-scheduler

# View logs
sudo journalctl -u classalert-scheduler -f

# Backup database
pg_dump \$DATABASE_URL\ > backup-\.sql
\\\

### Docker Alternative

See docker-compose.yml for a complete container-based setup:

\\\ash
docker-compose up -d
\\\

This starts Postgres, web server, and scheduler worker automatically.

