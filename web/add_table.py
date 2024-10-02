from app import create_app, db
from flask_migrate import upgrade, migrate, init, stamp
from models import TestDate, TempTest, Knowledge, Analysis, TodoList  # Import your model

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        # Initialize migration if needed (only the first time)
        stamp()  # Stamp the migration history
        
        # Create migration and upgrade database
        migrate()  # Detect changes in the models
        upgrade()  # Apply changes to the database
        
        print("Database migration completed, ReviewLessons table added!")
