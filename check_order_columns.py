from ecommerce import create_app, db
from sqlalchemy import text

app = create_app()

def check_columns():
    with app.app_context():
        with db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info('order')"))
            columns = result.fetchall()
            print("\nOrder table columns:")
            for col in columns:
                print(f"- {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")

if __name__ == '__main__':
    check_columns()
