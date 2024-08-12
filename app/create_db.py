# create_db.py
import sys
import os

# Add the parent directory of the script to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, Base, engine
from app.models import User, Movie, Rating, Comment  # Ensure all models are imported

def create_tables():
    """Create the database tables."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

if __name__ == "__main__":
    create_tables()  # Optionally, you can use init_db() if it does this
    # init_db()


