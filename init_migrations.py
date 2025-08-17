from ecommerce import create_app, db
from flask_migrate import init, stamp

app = create_app()

with app.app_context():
    # Initialize migrations
    init()
    
    # Create all tables
    db.create_all()
    
    # Mark the database as up to date
    stamp()

print("Migration system initialized successfully!")
