import sqlite3

def add_phone_column():
    conn = sqlite3.connect("instance/ecommerce.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE user ADD COLUMN phone VARCHAR(20)")
        conn.commit()
        print("Successfully added phone column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Phone column already exists")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_phone_column()
