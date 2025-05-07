from ecommerce import db, create_app
from ecommerce.models.shop import Product, Shop
from sqlalchemy import text

def migrate():
    with db.engine.connect() as conn:
        # Add category column to product table
        try:
            conn.execute(text('ALTER TABLE product ADD COLUMN category VARCHAR(50)'))
            print("Added category column to product table")
        except Exception as e:
            print(f"Error adding column (it might already exist): {e}")
            
        # Add about column to shop table
        try:
            conn.execute(text('ALTER TABLE shop ADD COLUMN about TEXT'))
            print("Added about column to shop table")
        except Exception as e:
            print(f"Error adding column (it might already exist): {e}")
        
        # Add contact fields to shop table
        try:
            conn.execute(text('ALTER TABLE shop ADD COLUMN phone VARCHAR(20)'))
            conn.execute(text('ALTER TABLE shop ADD COLUMN email VARCHAR(120)'))
            conn.execute(text('ALTER TABLE shop ADD COLUMN website VARCHAR(200)'))
            conn.execute(text('ALTER TABLE shop ADD COLUMN business_hours TEXT'))
            print("Added contact columns to shop table")
        except Exception as e:
            print(f"Error adding columns (they might already exist): {e}")
        
        conn.commit()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        migrate()