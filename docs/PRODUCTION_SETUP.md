# Production Deployment Guide

Follow these steps to deploy ClassAlert with a production-grade scheduler on a Linux server.

## Prerequisites
- Linux server or VPS (DigitalOcean, Linode, AWS EC2, etc.)
- Postgres 12+
- Python 3.10+
- Git
- Domain name (recommended)

## Step-by-Step Setup

### 1. Clone and install

```bash
git clone https://github.com/Jcasera31/Class-Alert.git
cd Class-Alert
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install psycopg2-binary
```

### 2. Configure environment variables

Create `.env` or set environment variables:

```bash
export DATABASE_URL="postgresql://classalert_user:secure_password@localhost:5432/classalert_db"
export SECRET_KEY="your-very-secure-random-key-here"
export FLASK_ENV="production"
```

### 3. Create Postgres database and user

```bash
sudo su - postgres
psql

-- In psql:
CREATE DATABASE classalert_db;
CREATE USER classalert_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE classalert_db TO classalert_user;
ALTER DATABASE classalert_db OWNER TO classalert_user;
\q
```

### 4. Initialize the database schema

```bash
source venv/bin/activate
python -c "from app import create_app, db; from app import models; app = create_app(); app.app_context().push(); db.create_all()"
```

### 5. Deploy scheduler worker as systemd service

Create `/etc/systemd/system/classalert-scheduler.service`:

```ini
[Unit]
Description=ClassAlert Scheduler Worker
After=network.target postgresql.service

[Service]
Type=simple
User=classalert
WorkingDirectory=/path/to/Class-Alert
Environment="PATH=/path/to/Class-Alert/venv/bin"
Environment="DATABASE_URL=postgresql://classalert_user:secure_password@localhost:5432/classalert_db"
Environment="SECRET_KEY=your-very-secure-random-key-here"
Environment="FLASK_ENV=production"
ExecStart=/path/to/Class-Alert/venv/bin/python /path/to/Class-Alert/scheduler_worker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Replace `/path/to/Class-Alert` with the actual deployment path.

Enable and start the scheduler:

```bash
sudo systemctl daemon-reload
sudo systemctl enable classalert-scheduler
sudo systemctl start classalert-scheduler
sudo systemctl status classalert-scheduler
```

### 6. Deploy web server with Gunicorn

Create `/etc/systemd/system/classalert-web.service`:

```ini
[Unit]
Description=ClassAlert Web Server
After=network.target postgresql.service

[Service]
Type=notify
User=classalert
WorkingDirectory=/path/to/Class-Alert
Environment="PATH=/path/to/Class-Alert/venv/bin"
Environment="DATABASE_URL=postgresql://classalert_user:secure_password@localhost:5432/classalert_db"
Environment="SECRET_KEY=your-very-secure-random-key-here"
Environment="FLASK_ENV=production"
ExecStart=/path/to/Class-Alert/venv/bin/gunicorn --workers=4 --bind 127.0.0.1:5000 --timeout 60 api.index:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable classalert-web
sudo systemctl start classalert-web
sudo systemctl status classalert-web
```

### 7. Configure Nginx reverse proxy

Create `/etc/nginx/sites-available/classalert`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    client_max_body_size 16M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60;
        proxy_connect_timeout 60;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/classalert /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 8. Set up SSL/TLS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

This automatically configures Nginx with SSL and sets up auto-renewal.

### 9. Verify everything is working

```bash
# Test the web server
curl https://yourdomain.com

# Create a test schedule from the web UI
# Visit https://yourdomain.com and log in

# Check scheduler logs
sudo journalctl -u classalert-scheduler -f

# Check web server logs
sudo journalctl -u classalert-web -f

# Check admin jobs endpoint (requires login)
curl -b cookies.txt https://yourdomain.com/admin/jobs
```

## Monitoring and Maintenance

### Check service status

```bash
sudo systemctl status classalert-scheduler
sudo systemctl status classalert-web
sudo systemctl status nginx
```

### View logs

```bash
# Scheduler logs
sudo journalctl -u classalert-scheduler -n 100

# Web server logs
sudo journalctl -u classalert-web -n 100

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Database backups

```bash
# Full backup
pg_dump $DATABASE_URL > classalert-backup-$(date +%Y%m%d-%H%M%S).sql

# Restore from backup
psql $DATABASE_URL < classalert-backup-20251211-120000.sql
```

### Restart services

```bash
# Restart just the scheduler
sudo systemctl restart classalert-scheduler

# Restart just the web server
sudo systemctl restart classalert-web

# Restart all services
sudo systemctl restart classalert-scheduler classalert-web nginx
```

## Docker Alternative

Use `docker-compose.yml` for a complete containerized setup:

```bash
docker-compose up -d
```

This starts:
- Postgres database
- Flask web server
- APScheduler worker

All services are automatically managed and will restart on failure.

## Troubleshooting

### Scheduler not creating notifications

```bash
# Check if scheduler is running
sudo systemctl status classalert-scheduler

# Check logs for errors
sudo journalctl -u classalert-scheduler -n 50

# Verify database connection
psql $DATABASE_URL -c "SELECT 1"

# List scheduled jobs
curl https://yourdomain.com/admin/jobs
```

### Web server not responding

```bash
# Check if web server is running
sudo systemctl status classalert-web

# Test locally
curl http://127.0.0.1:5000

# Check Nginx
sudo nginx -t
sudo systemctl status nginx
```

### Database connection issues

```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check database exists
psql -l | grep classalert

# Verify user permissions
psql $DATABASE_URL -c "SELECT * FROM schedule LIMIT 1"
```

### SSL certificate issues

```bash
# Renew certificate manually
sudo certbot renew

# Check certificate status
sudo certbot certificates

# Debug Nginx SSL
sudo nginx -t
sudo systemctl reload nginx
```

## Next Steps

1. **Set up monitoring** — Consider using Prometheus/Grafana or SimpleMonitoring
2. **Automate backups** — Set up a cron job to backup the database daily
3. **Enable per-user timezones** — Store user timezone and convert UI inputs accordingly
4. **Add metrics** — Monitor job execution times and notification delays
5. **Scale horizontally** — Run multiple web instances behind a load balancer if needed

## Support

For issues, check:
- Scheduler logs: `sudo journalctl -u classalert-scheduler -f`
- Web logs: `sudo journalctl -u classalert-web -f`
- Database: `psql $DATABASE_URL`
- `/admin/jobs` endpoint (requires login)

Questions? Check the main `README.md` for architecture details and the `.env.example` file for configuration options.
