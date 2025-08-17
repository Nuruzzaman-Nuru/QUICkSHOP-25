import sqlite3
import os

def add_payment_columns():
    # Get the absolute path to the database file
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'ecommerce.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add payment columns one by one
        columns = [
            ("payment_method", "VARCHAR(20) NOT NULL DEFAULT 'cod'"),
            ("payment_status", "VARCHAR(20) NOT NULL DEFAULT 'pending'"),
            ("payment_details", "JSON"),
            ("payment_transaction_id", "VARCHAR(100)")
        ]
        
        for column_name, column_type in columns:
            try:
                cursor.execute(f'''
                    ALTER TABLE "order" 
                    ADD COLUMN {column_name} {column_type}
                ''')
                print(f"Successfully added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"Column {column_name} already exists")
                else:
                    print(f"Error adding column {column_name}: {e}")
        
        conn.commit()
        print("Successfully updated the order table!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    add_payment_columns()
