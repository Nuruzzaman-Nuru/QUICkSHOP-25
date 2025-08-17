import sqlite3
import os

def check_table_structure():
    # Get the absolute path to the database file
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'ecommerce.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get table info
        cursor.execute("PRAGMA table_info('order')")
        columns = cursor.fetchall()
        
        print("\nOrder table structure:")
        print("----------------------")
        for col in columns:
            print(f"Column: {col[1]}")
            print(f"Type: {col[2]}")
            print(f"Nullable: {not col[3]}")
            print(f"Default: {col[4]}")
            print("----------------------")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    check_table_structure()
