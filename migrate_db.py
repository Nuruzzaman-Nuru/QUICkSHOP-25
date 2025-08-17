from ecommerce import create_app, db
from flask_migrate import Migrate, upgrade
import os

def migrate_database():
    app = create_app()
    
    with app.app_context():
        # Initialize migration
        migrate = Migrate(app, db)
        
        # Get the migrations directory path
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        
        try:
            # Apply all pending migrations
            upgrade(directory=migrations_dir)
            print("Successfully applied migrations!")
            
        except Exception as e:
            print(f"Error applying migrations: {e}")
            
            # If there's an error, try to create tables directly
            try:
                print("Attempting to create tables directly...")
                db.create_all()
                print("Successfully created tables!")
            except Exception as e:
                print(f"Error creating tables: {e}")

if __name__ == '__main__':
    migrate_database()
