from ecommerce import create_app, db
from ecommerce.models.user import User
import os

def init_db(app):
    with app.app_context():
        # Create database if it doesn't exist
        if not os.path.exists('instance/ecommerce.db'):
            db.create_all()
            print("Database created successfully!")

def create_admin_user():
    try:
        print("Creating Flask application...")
        app = create_app()
        
        print("Initializing database...")
        # Initialize database
        init_db(app)
        
        print("Setting up admin user...")
        with app.app_context():
            try:
            # Check if admin already exists
            admin = User.query.filter_by(email='nuru@admin.com').first()
            if admin:
                print("Updating existing admin user...")
                admin.username = 'adminnuru'
                admin.role = 'admin'
                admin.set_password('nuru1234')
            else:
                print("Creating new admin user...")
                admin = User(
                    username='adminnuru',
                    email='nuru@admin.com',
                    role='admin'
                )
                admin.set_password('nuru1234')
                db.session.add(admin)
            
            db.session.commit()
            print("\nAdmin user created/updated successfully!")
            print("======================================")
            print("Admin Login Details:")
            print("======================================")
            print(f"Username: adminnuru")
            print(f"Email: nuru@admin.com")
            print(f"Password: nuru1234")
            print(f"Role: admin")
            print("======================================")
            print("\nYou can now login at: /admin/login")
            
        except Exception as e:
            db.session.rollback()
            print(f"\nError managing admin user: {e}")
            print("\nTroubleshooting steps:")
            print("1. Make sure the database exists")
            print("2. Check if all required packages are installed")
            print("3. Verify the database connection")

if __name__ == '__main__':
    create_admin_user()
