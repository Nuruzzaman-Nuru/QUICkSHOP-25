from ecommerce import db, create_app
from ecommerce.models.shop import Product
from sqlalchemy import text

def migrate():
    with db.engine.connect() as conn:
        # Add category column to product table
        try:
            conn.execute(text('ALTER TABLE product ADD COLUMN category VARCHAR(50)'))
            print("Added category column to product table")
        except Exception as e:
            print(f"Error adding column (it might already exist): {e}")
        
        conn.commit()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        migrate()