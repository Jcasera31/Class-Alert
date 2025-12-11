# Neon Postgres Setup Guide

Quick guide to set up ClassAlert with Neon's free Postgres hosting.

## Why Neon?

- ✅ **Free tier:** 10GB storage, 512MB RAM
- ✅ **No credit card required**
- ✅ **Automatic backups**
- ✅ **Fast setup** (5 minutes)
- ✅ **Serverless** - scales to zero when not in use
- ✅ **Built-in connection pooling**

## Step 1: Create Neon Account

1. Go to: https://neon.tech
2. Click **"Sign Up"**
3. Sign up with GitHub (easiest) or email
4. Verify email if prompted

## Step 2: Create Database Project

1. Once logged in, you'll see the dashboard
2. Click **"Create Project"** (or it auto-creates one)
3. Configure:
   - **Name:** `classalert-db`
   - **Region:** Choose closest to your users (e.g., US East, EU, Asia)
   - **Postgres version:** 16 (recommended)
4. Click **"Create Project"**

## Step 3: Get Connection String

After project creation, you'll see:

```
postgresql://username:password@ep-xxx-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**Important:** Copy this entire string! You'll need it in the next steps.

The format is:
```
postgresql://[username]:[password]@[host]/[database]?sslmode=require
```

## Step 4: Set Up Local Environment

### Windows PowerShell:
```powershell
cd C:\Casera1Github\class-alert
$env:DATABASE_URL="your-neon-connection-string-here"
```

### Windows CMD:
```cmd
cd C:\Casera1Github\class-alert
set DATABASE_URL=your-neon-connection-string-here
```

### Linux/Mac:
```bash
cd /path/to/class-alert
export DATABASE_URL="your-neon-connection-string-here"
```

## Step 5: Run Database Migration

This creates all the tables in your Neon database:

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
.\venv\Scripts\Activate.ps1  # Windows PowerShell

# Run migration
python scripts/migrate_to_neon.py
```

You should see:
```
✓ Database URL detected: postgresql://...
✓ Creating Flask app...
✓ Connected to database
✓ Created table: user
✓ Created table: schedule
✓ Created table: notification
✅ Migration Complete!
```

## Step 6: Configure Vercel

Go to your Vercel project settings:

1. Go to: https://vercel.com/dashboard
2. Select your `class-alert` project
3. Go to **Settings** → **Environment Variables**
4. Add these variables:

| Variable Name | Value |
|---------------|-------|
| `DATABASE_URL` | Your Neon connection string |
| `SECRET_KEY` | Generate with: `python -c "import secrets; print(secrets.token_hex(32))"` |

**Important:** Make sure to add for all environments (Production, Preview, Development)

## Step 7: Deploy to Vercel

```bash
vercel deploy --prod
```

Or if you have auto-deploy enabled:
```bash
git push origin main
```

Vercel will automatically rebuild and deploy with the new database connection.

## Step 8: Verify Everything Works

1. **Visit your Vercel URL:**
   ```
   https://class-alert-xxxxx.vercel.app
   ```

2. **Create a test account:**
   - Click "Sign Up"
   - Create a user
   - Add a test schedule

3. **Check Neon Dashboard:**
   - Go back to https://console.neon.tech
   - Click your project
   - Go to **SQL Editor**
   - Run: `SELECT * FROM "user";`
   - You should see your test user!

## Monitoring Your Database

### View Data in Neon Console

```sql
-- See all users
SELECT id, username, email, created_at FROM "user";

-- See all schedules
SELECT id, user_id, class_name, start_time, end_time, days_of_week 
FROM schedule;

-- See all notifications
SELECT id, user_id, timestamp, message 
FROM notification 
ORDER BY timestamp DESC 
LIMIT 10;
```

### Check Database Size

Go to: Neon Console → Your Project → Usage

You'll see:
- Storage used
- Compute time used
- Active connections

Free tier limits:
- **10 GB storage**
- **100 hours compute time/month**
- **Unlimited** connections

## Troubleshooting

### Connection Error: "connection refused"

- Check that `sslmode=require` is in your connection string
- Verify your IP isn't blocked (Neon allows all IPs by default)

### Migration Failed: "table already exists"

The tables are already created. Test with:
```bash
python scripts/migrate_to_neon.py --test
```

### Vercel Can't Connect

1. Check environment variable is set in Vercel
2. Make sure you added it to **all environments**
3. Trigger a new deployment after adding variables

### Slow Performance

- Neon free tier scales down when not in use (cold start ~1-2s)
- For production, consider upgrading to paid tier for always-on compute

## Local Development with Neon

You can also use Neon for local development:

```bash
# Set DATABASE_URL in your terminal
export DATABASE_URL="your-neon-connection-string"

# Run locally
python run.py
```

Your local app will connect to Neon just like Vercel does!

## Backups

Neon automatically backs up your data:
- **Point-in-time recovery:** Restore to any point in the last 7 days (free tier)
- **Manual backups:** Use Neon console to create snapshots

### Manual Backup via pg_dump:

```bash
pg_dump $DATABASE_URL > backup-$(date +%Y%m%d).sql
```

### Restore from Backup:

```bash
psql $DATABASE_URL < backup-20251211.sql
```

## Cost Estimate (Free Tier)

| Feature | Free Tier | Usage Estimate |
|---------|-----------|----------------|
| Storage | 10 GB | ~1-2 GB for typical app |
| Compute | 100 hrs/month | ~50-70 hrs/month active |
| Connections | Unlimited | No limit |
| Backups | 7 days | Automatic |

**Result:** Should easily stay within free tier for development/demo!

## Upgrade Path

If you outgrow free tier:
- **Launch Plan:** $19/month (always-on compute, 50GB storage)
- **Scale Plan:** $69/month (autoscaling, 500GB storage)

## Next Steps

✅ Database set up and running
✅ Vercel connected to Neon
✅ App deployed and accessible

**Optional improvements:**
1. Set up monitoring (Neon has built-in metrics)
2. Configure connection pooling (built-in, no setup needed)
3. Add database indexes for better performance
4. Set up automated backups via cron

## Resources

- Neon Console: https://console.neon.tech
- Neon Docs: https://neon.tech/docs
- Connection String Help: https://neon.tech/docs/connect/connection-string
- Vercel Integration: https://vercel.com/integrations/neon

## Support

Questions? Check:
1. Neon status: https://neonstatus.com
2. Test connection: `python scripts/migrate_to_neon.py --test`
3. View Vercel logs: `vercel logs`
4. Check Neon console for connection metrics
