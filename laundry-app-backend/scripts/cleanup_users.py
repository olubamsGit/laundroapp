import sys
import os
from datetime import datetime, timedelta, timezone

# Add the project root to the path so we can import app
sys.path.append(os.getcwd())

from app.db.session import SessionLocal # Adjust this import to your session path
from app.models.user import User

def cleanup():
    db = SessionLocal()
    try:
        # Define the cutoff (24 hours ago)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Query for users who are unverified AND older than 24h
        unverified_users = db.query(User).filter(
            User.is_verified == False,
            User.created_at <= cutoff
        )
        
        count = unverified_users.count()
        unverified_users.delete(synchronize_session=False)
        db.commit()
        
        print(f"Cleanup finished. Removed {count} unverified users.")
    except Exception as e:
        print(f"Cleanup failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup()