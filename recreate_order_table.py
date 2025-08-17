from ecommerce import create_app, db
from ecommerce.models.order import Order
import sqlite3
import os

def recreate_order_table():
    app = create_app()
    
    with app.app_context():
        try:
            # Get existing orders data
            db_path = os.path.join(os.path.dirname(__file__), 'instance', 'ecommerce.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get existing orders
            print("Backing up existing orders...")
            cursor.execute('SELECT * FROM "order"')
            existing_orders = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            
            print(f"Found {len(existing_orders)} existing orders")
            print(f"Existing columns: {column_names}")
            
            print("Creating backup table...")
            cursor.execute('CREATE TABLE order_backup AS SELECT * FROM "order"')
            
            print("Dropping existing order table...")
            cursor.execute('DROP TABLE "order"')
            
            print("Creating new order table with payment columns...")
            
            # Create the table with all columns including payment columns
            cursor.execute('''
                CREATE TABLE "order" (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    shop_id INTEGER NOT NULL,
                    delivery_person_id INTEGER,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    total_amount FLOAT NOT NULL DEFAULT 0.0,
                    delivery_fee FLOAT NOT NULL DEFAULT 5.0,
                    delivery_address VARCHAR(200),
                    delivery_lat FLOAT,
                    delivery_lng FLOAT,
                    created_at DATETIME,
                    updated_at DATETIME,
                    estimated_delivery_time DATETIME,
                    special_instructions TEXT,
                    payment_method VARCHAR(20) NOT NULL DEFAULT 'cod',
                    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    payment_details JSON,
                    payment_transaction_id VARCHAR(100),
                    FOREIGN KEY(customer_id) REFERENCES user(id),
                    FOREIGN KEY(shop_id) REFERENCES shop(id),
                    FOREIGN KEY(delivery_person_id) REFERENCES user(id)
                )
            ''')
            
            print("Restoring order data...")
            
            # Prepare the insert statement with only the columns that existed in the old table
            old_columns = [col for col in column_names if col != 'id']
            placeholders = ','.join(['?' for _ in old_columns])
            columns_str = ','.join(old_columns)
            
            # Insert the old data back
            for order in existing_orders:
                values = order[1:]  # Skip the id column
                try:
                    cursor.execute(f'INSERT INTO "order" ({columns_str}) VALUES ({placeholders})', values)
                except Exception as e:
                    print(f"Error inserting order: {e}")
                    continue
            
            conn.commit()
            print("Successfully recreated the order table with payment columns!")
            
            # Verify the new table structure
            cursor.execute("PRAGMA table_info('order')")
            new_columns = cursor.fetchall()
            print("\nNew table structure:")
            for col in new_columns:
                print(f"Column: {col[1]}, Type: {col[2]}, NotNull: {col[3]}, Default: {col[4]}")
            
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
            
            # Try to restore from backup if something went wrong
            try:
                cursor.execute('DROP TABLE IF EXISTS "order"')
                cursor.execute('ALTER TABLE order_backup RENAME TO "order"')
                conn.commit()
                print("Restored from backup after error")
            except:
                print("Could not restore from backup")
        finally:
            conn.close()

if __name__ == '__main__':
    recreate_order_table()