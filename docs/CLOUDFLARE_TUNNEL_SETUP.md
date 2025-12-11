# Cloudflare Tunnel Setup: Local DB + Vercel Hosting

This guide shows how to securely expose your local Postgres database and files to Vercel using Cloudflare Tunnel.

## Architecture

```
Your Local Machine (Windows/Mac/Linux)
├── Postgres Database (localhost:5432)
├── File Uploads (./uploads)
└── Cloudflare Tunnel → Encrypts & exposes to internet
    ↓
Vercel (Hosted UI + API)
├── Connects to your local DB via Cloudflare Tunnel
├── Stores session data in your DB
└── Shows your app to the world
```

## Prerequisites

- Cloudflare account (free tier works great)
- Domain registered with Cloudflare (or migrated to Cloudflare DNS)
- cloudflared CLI installed
- Python/Flask running locally or ready to run

## Step 1: Install Cloudflare CLI (cloudflared)

### Option A: Download Executable (Easiest for Windows)

1. Go to: https://github.com/cloudflare/cloudflared/releases
2. Download `cloudflared-windows-amd64.exe` (for Windows 64-bit)
3. Save it to a folder, e.g., `C:\cloudflare\cloudflared.exe`
4. Add to PATH or reference it directly

Test installation:
```powershell
C:\cloudflare\cloudflared.exe --version
```

### Option B: Install via npm

```bash
npm install -g cloudflare-cli
```

### Option C: Install via Chocolatey (Windows)

```powershell
choco install cloudflare-wrangler
```

## Step 2: Authenticate with Cloudflare

Run this command to log in:

```bash
cloudflared tunnel login
```

This opens your browser to authenticate. Approve the request, and cloudflared will save your credentials locally.

## Step 3: Create a Tunnel

```bash
cloudflared tunnel create classalert-db
```

Output will show:
```
Tunnel credentials written to: C:\Users\YourUser\.cloudflared\<tunnel-id>.json
Tunnel classalert-db created with ID: <tunnel-id>
```

Save the tunnel ID — you'll need it later.

## Step 4: Configure Tunnel Route (DNS)

Map your tunnel to a subdomain:

```bash
cloudflared tunnel route dns classalert-db db.yourdomain.com
```

Replace `yourdomain.com` with your actual domain registered with Cloudflare.

Verify in Cloudflare Dashboard:
- Go to your domain → DNS records
- You should see a new `CNAME` record pointing to `classalert-db.cfargotunnel.com`

## Step 5: Configure Tunnel Config File

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: classalert-db
credentials-file: ~/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: db.yourdomain.com
    service: tcp://localhost:5432
  - service: http_status:404
```

Replace `<tunnel-id>` with your actual tunnel ID from Step 3.

## Step 6: Start the Tunnel

Run this command on your local machine (keep it running):

```bash
cloudflared tunnel run classalert-db
```

You should see output like:
```
Registered tunnel connection from <random-id>
+----------+------------------+-----------+------------------+------+----------+------------------------+
| Hostname | RPC Proto | Status    | Region | Latency | Handler  | Remarks  |
+----------+------------------+-----------+------------------+------+----------+------------------------+
| db.yourdomain.com | tcp   | HEALTHY   | us    | 12ms   | tcp      |          |
+----------+------------------+-----------+------------------+--+ 
Serving DNS routes from config file /Users/user/.cloudflared/config.yml
```

✅ **Your database is now accessible from the internet!**

## Step 7: Test Local Connection

From your local machine, test the tunnel:

```bash
psql postgresql://classalert_user:password@db.yourdomain.com:5432/classalert_db -c "SELECT 1"
```

You should see:
```
 ?column?
----------
        1
```

## Step 8: Configure Vercel Environment Variables

Go to your Vercel project settings and add:

```
DATABASE_URL = postgresql://classalert_user:your_password@db.yourdomain.com:5432/classalert_db
SECRET_KEY = your-secret-key-here
```

**Important:** Use the Cloudflare tunnel domain (`db.yourdomain.com`), not `localhost`.

## Step 9: Redeploy Vercel

Trigger a redeployment on Vercel:

```bash
vercel deploy --prod
```

Or just push to main branch if you have auto-deploy enabled.

Vercel will now connect to your local database!

## Step 10: Set Up Local Tunnel as a Service (Optional but Recommended)

### Windows (Task Scheduler)

1. Create a PowerShell script `C:\cloudflare\start-tunnel.ps1`:

```powershell
# Start Cloudflare tunnel and keep it running
& "C:\cloudflare\cloudflared.exe" tunnel run classalert-db

# If tunnel crashes, restart it
while ($true) {
    & "C:\cloudflare\cloudflared.exe" tunnel run classalert-db
    Start-Sleep -Seconds 5
}
```

2. Open Task Scheduler:
```powershell
taskmgr
```

3. Create Basic Task:
   - Name: "Cloudflare Tunnel - ClassAlert"
   - Trigger: At startup
   - Action: Run PowerShell script `C:\cloudflare\start-tunnel.ps1`
   - Check "Run with highest privileges"

### Linux/Mac (Systemd or LaunchD)

For Linux, install as a service:

```bash
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

For Mac, use LaunchD:

```bash
# Create launch agent
mkdir -p ~/Library/LaunchAgents

cat > ~/Library/LaunchAgents/com.cloudflare.tunnel.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cloudflare.tunnel</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/cloudflared</string>
        <string>tunnel</string>
        <string>run</string>
        <string>classalert-db</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.cloudflare.tunnel.plist
```

## Verification Checklist

- [ ] Cloudflare account created and domain added
- [ ] `cloudflared` CLI installed and working
- [ ] Tunnel created and authenticated
- [ ] DNS route configured (`db.yourdomain.com`)
- [ ] Tunnel running and showing "HEALTHY"
- [ ] Local psql connection test passes
- [ ] Vercel environment variables updated with tunnel URL
- [ ] Vercel redeployed
- [ ] App is working on Vercel and creating data in local DB

## Testing the Full Setup

1. **On your local machine:**
   - Start the tunnel: `cloudflared tunnel run classalert-db`
   - Keep it running in the background

2. **From Vercel:**
   - Visit your Vercel URL: https://class-alert-xxxxx.vercel.app
   - Create a test user/schedule
   - Check if data appears in your local database:
     ```bash
     psql $DATABASE_URL -c "SELECT * FROM user LIMIT 1"
     ```

3. **Monitor the tunnel:**
   - If something goes wrong, check tunnel logs:
     ```bash
     cloudflared tunnel logs classalert-db
     ```

## Security Considerations

✅ **What's Secure:**
- Cloudflare encrypts all traffic (TLS 1.3)
- Database credentials not exposed (tunnel handles auth)
- Your IP address is hidden
- DDoS protection included (Cloudflare)

⚠️ **What to Monitor:**
- Keep Cloudflare tunnel running on your machine
- Monitor bandwidth (free tier has limits)
- Regularly back up your database
- Use strong database passwords

## Troubleshooting

### Tunnel won't connect

```bash
# Check if already running
cloudflared tunnel list

# Force logout and re-login
cloudflared tunnel logout
cloudflared tunnel login
```

### DNS not resolving

- Wait 5-10 minutes for DNS to propagate
- Check Cloudflare Dashboard → DNS records
- Verify CNAME points to `classalert-db.cfargotunnel.com`

### Vercel can't connect to DB

1. Test from your machine first:
   ```bash
   psql postgresql://user:pass@db.yourdomain.com:5432/db -c "SELECT 1"
   ```

2. Check tunnel logs:
   ```bash
   cloudflared tunnel logs classalert-db
   ```

3. Verify DATABASE_URL in Vercel environment:
   ```bash
   vercel env pull
   grep DATABASE_URL .env.local
   ```

### Connection timeout errors

- Tunnel might be down (restart it)
- Firewall blocking port 5432 locally (check Windows Defender)
- Postgres not running on your machine

### Slow performance

- Cloudflare free tier has some rate limiting
- Your internet connection matters (upload speed critical)
- Consider Cloudflare Pro if experiencing issues

## Next Steps

1. **File Storage:** Configure S3-compatible storage or use local folder served by Flask
2. **Scheduler Worker:** Run `scheduler_worker.py` locally to handle background jobs
3. **Email Notifications:** Add email service (SendGrid, Mailgun) for production
4. **Monitoring:** Set up monitoring for tunnel uptime and database health

## Additional Resources

- Cloudflare Tunnel Docs: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
- Cloudflared CLI Docs: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/
- Supported Services: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/configuration/

## Support

For issues:
1. Check Cloudflare status: https://www.cloudflarestatus.com
2. View tunnel logs: `cloudflared tunnel logs classalert-db`
3. Test DB connection: `psql $DATABASE_URL -c "SELECT 1"`
4. Check Vercel logs: `vercel logs`
