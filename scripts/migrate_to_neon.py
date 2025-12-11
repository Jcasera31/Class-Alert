"""
Database Migration Helper - Neon Postgres Setup

This script helps you migrate from SQLite to Neon Postgres.
Run this after setting up your Neon database.

Usage:
    1. Set DATABASE_URL environment variable to your Neon connection string
    2. Run: python scripts/migrate_to_neon.py
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Schedule, Notification


def migrate_to_neon():
    """Initialize database schema in Neon Postgres"""
    
    print("\n" + "="*60)
    print("ClassAlert - Neon Postgres Migration")
    print("="*60 + "\n")
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL') or os.getenv('SQLALCHEMY_DATABASE_URI')
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL not set!")
        print("\nPlease set your Neon connection string:")
        print("  Windows PowerShell:")
        print('    $env:DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"')
        print("\n  Windows CMD:")
        print('    set DATABASE_URL=postgresql://user:pass@host/db?sslmode=require')
        print("\n  Linux/Mac:")
        print('    export DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"')
        return False
    
    # Check if it's Neon
    if 'neon.tech' not in database_url and 'neon' not in database_url:
        print(f"⚠️  WARNING: Database URL doesn't look like Neon:")
        print(f"   {database_url[:50]}...")
        confirm = input("\nContinue anyway? (y/N): ")
        if confirm.lower() != 'y':
            return False
    
    print(f"✓ Database URL detected: {database_url[:30]}...{database_url[-20:]}")
    print(f"✓ Creating Flask app...")
    
    # Create app with Neon configuration
    app = create_app()
    
    with app.app_context():
        print(f"✓ Connected to database")
        print(f"✓ Database URI: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
        
        # Test connection
        try:
            from sqlalchemy import text
            result = db.session.execute(text('SELECT version()')).fetchone()
            print(f"✓ Database version: {result[0][:50]}...")
        except Exception as e:
            print(f"❌ ERROR: Could not connect to database")
            print(f"   {str(e)}")
            return False
        
        # Create all tables
        print("\n📊 Creating database tables...")
        try:
            db.create_all()
            print("✓ Created table: user")
            print("✓ Created table: schedule")
            print("✓ Created table: notification")
            print("✓ Created table: apscheduler_jobs (for persistent scheduling)")
        except Exception as e:
            print(f"❌ ERROR: Could not create tables")
            print(f"   {str(e)}")
            return False
        
        # Verify tables exist
        print("\n🔍 Verifying tables...")
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✓ Found {len(tables)} tables: {', '.join(tables)}")
        except Exception as e:
            print(f"⚠️  Warning: Could not verify tables: {str(e)}")
        
        print("\n" + "="*60)
        print("✅ Migration Complete!")
        print("="*60)
        print("\nNext Steps:")
        print("1. Update Vercel environment variables:")
        print("   - Go to Vercel project settings")
        print("   - Add DATABASE_URL with your Neon connection string")
        print("   - Add SECRET_KEY with a secure random string")
        print("\n2. Deploy to Vercel:")
        print("   vercel deploy --prod")
        print("\n3. Test your app:")
        print("   - Visit your Vercel URL")
        print("   - Create a test user and schedule")
        print("   - Verify data appears in Neon dashboard")
        print("\n" + "="*60)
        
    return True


def test_connection():
    """Test connection to Neon database"""
    print("\n🔍 Testing database connection...")
    
    database_url = os.getenv('DATABASE_URL') or os.getenv('SQLALCHEMY_DATABASE_URI')
    if not database_url:
        print("❌ DATABASE_URL not set")
        return False
    
    app = create_app()
    with app.app_context():
        try:
            from sqlalchemy import text
            result = db.session.execute(text('SELECT 1')).fetchone()
            if result[0] == 1:
                print("✅ Connection successful!")
                
                # Show table counts
                try:
                    user_count = db.session.execute(text('SELECT COUNT(*) FROM "user"')).fetchone()[0]
                    schedule_count = db.session.execute(text('SELECT COUNT(*) FROM schedule')).fetchone()[0]
                    notification_count = db.session.execute(text('SELECT COUNT(*) FROM notification')).fetchone()[0]
                    
                    print(f"\n📊 Current Data:")
                    print(f"   Users: {user_count}")
                    print(f"   Schedules: {schedule_count}")
                    print(f"   Notifications: {notification_count}")
                except Exception as e:
                    print(f"   (Tables not yet created)")
                
                return True
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            return False
    
    return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate ClassAlert to Neon Postgres')
    parser.add_argument('--test', action='store_true', help='Test connection only')
    args = parser.parse_args()
    
    if args.test:
        success = test_connection()
    else:
        success = migrate_to_neon()
    
    sys.exit(0 if success else 1)
