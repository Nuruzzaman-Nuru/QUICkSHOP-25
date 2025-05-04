from ecommerce import db, create_app
from ecommerce.models.shop import Product
from sqlalchemy import text

def migrate():
    with db.engine.connect() as conn:
        # Add estimated_delivery_time column to order table
        try:
            conn.execute(text('ALTER TABLE "order" ADD COLUMN estimated_delivery_time TIMESTAMP'))
            print("Added estimated_delivery_time column to order table")
        except Exception as e:
            print(f"Error adding column (it might already exist): {e}")
            
        # Add special_instructions column to order table
        try:
            conn.execute(text('ALTER TABLE "order" ADD COLUMN special_instructions TEXT'))
            print("Added special_instructions column to order table")
        except Exception as e:
            print(f"Error adding column (it might already exist): {e}")
            
        # Add continue_iteration column to product table
        try:
            conn.execute(text('ALTER TABLE product ADD COLUMN continue_iteration BOOLEAN DEFAULT FALSE'))
            print("Added continue_iteration column to product table")
        except Exception as e:
            print(f"Error adding column (it might already exist): {e}")
            
        conn.execute(text("ALTER TABLE product ADD COLUMN image_url VARCHAR(255)"))
        conn.commit()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        migrate()