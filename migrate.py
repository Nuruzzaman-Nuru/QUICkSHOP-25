from ecommerce import db, create_app
from ecommerce.models.shop import Product, Shop
from sqlalchemy import text

def migrate():
    with db.engine.connect() as conn:
        # Add email_notifications column to user table with default value
        try:
            conn.execute(text('''
                ALTER TABLE user 
                ADD COLUMN email_notifications BOOLEAN NOT NULL DEFAULT 1
            '''))
            print("Added email_notifications column to user table")
        except Exception as e:
            print(f"Error adding email_notifications column (it might already exist): {e}")

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
        
        # Add rating fields to product table
        try:
            conn.execute(text('ALTER TABLE product ADD COLUMN rating FLOAT DEFAULT 0.0'))
            conn.execute(text('ALTER TABLE product ADD COLUMN rating_count INTEGER DEFAULT 0'))
            print("Added rating fields to product table")
        except Exception as e:
            print(f"Error adding rating fields (they might already exist): {e}")

        # Create reviews table
        try:
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS review (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    rating INTEGER NOT NULL,
                    comment TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES product (id),
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            '''))
            print("Created reviews table")
        except Exception as e:
            print(f"Error creating reviews table (it might already exist): {e}")
        
        conn.commit()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        migrate()