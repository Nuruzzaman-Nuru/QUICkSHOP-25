from ecommerce import create_app, db

app = create_app()

with app.app_context():
    # Add the new column
    with db.engine.connect() as conn:
        conn.execute('ALTER TABLE user ADD COLUMN email_notifications BOOLEAN DEFAULT TRUE')
        conn.commit()

print("Database updated successfully!")
