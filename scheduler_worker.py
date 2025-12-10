"""Scheduler worker
Run this on a server (not Vercel) to provide a persistent background worker
that runs APScheduler with a persistent jobstore (Postgres recommended).

Usage:
    set DATABASE_URL=postgresql://user:pass@host:5432/dbname
    venv\\Scripts\\Activate.ps1
    python scheduler_worker.py
"""
import atexit
import time
import os
from app import create_app
from app.scheduler import start_scheduler, stop_scheduler


def main():
    app = create_app()

    # Start scheduler without SocketIO (worker-only)
    try:
        start_scheduler(app, None)
        atexit.register(stop_scheduler)
        print('Scheduler worker started. Press Ctrl+C to exit.')
        # Keep the process alive
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print('Scheduler worker shutting down...')
    except Exception as e:
        print('Scheduler worker error:', e)


if __name__ == '__main__':
    main()
