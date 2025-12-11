import requests
from datetime import datetime, timedelta, timezone
import time

BASE = 'http://127.0.0.1:5000'

session = requests.Session()

# Credentials for test user (created earlier)
email = 'test@example.com'
password = 'testpass'

# 1) Log in
print('Logging in...')
resp = session.post(f'{BASE}/auth/login', data={'email': email, 'password': password}, allow_redirects=False)
if resp.status_code not in (302, 200):
    print('Login failed:', resp.status_code, resp.text[:200])
    raise SystemExit(1)
print('Login response:', resp.status_code)

# 2) Prepare a schedule a few minutes from now (use server-local timezone handling)
start_dt = datetime.now(timezone.utc) + timedelta(minutes=2)
end_dt = start_dt + timedelta(hours=1)
time_str = f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"
# Single-day schedule: today's weekday abbreviation
day_map = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
day_abbr = day_map[start_dt.astimezone().weekday() if False else start_dt.weekday()]

form = {
    'subject': 'E2E TEST CLASS',
    'days': day_abbr,
    'time': time_str,
    'semester': 'E2E',
    'academic_year': str(start_dt.year),
    'alarm_enabled': 'on',
    'alarm_offset': '1',  # 1 minute before
}

print('Posting new schedule:', form)
resp = session.post(f'{BASE}/schedule/add', data=form, allow_redirects=True)
print('Add schedule response:', resp.status_code)

print('Waiting up to 180 seconds for notification to be created...')
for i in range(36):
    r = requests.get(f'{BASE}/api/health')
    # Check DB directly by calling the check_notifications script locally
    from subprocess import Popen, PIPE, STDOUT
    p = Popen(["python", "scripts/check_notifications.py"], stdout=PIPE, stderr=STDOUT, cwd='.' )
    out = p.communicate()[0].decode('utf-8')
    print(out)
    if 'Found' in out and '1 notifications' in out or 'Found' in out and '0 notifications' not in out:
        print('Notification found, test complete')
        break
    time.sleep(5)
else:
    print('No notification observed in 180 seconds')
