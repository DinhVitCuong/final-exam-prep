from app import create_app, db
from models import Test, QAs

app = create_app()

with app.app_context():
    try:
        # Delete all rows from the Test table
        db.session.query(Test).delete()
        
        # Commit the changes to make them permanent
        db.session.commit()
        
        print("All data from the Test table has been deleted successfully.")
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        print(f"An error occurred while deleting data: {e}")