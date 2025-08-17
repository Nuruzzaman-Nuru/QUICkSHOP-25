from ecommerce import create_app, db
from sqlalchemy import text

app = create_app()

def add_payment_columns():
    with app.app_context():
        with db.engine.connect() as conn:
            # Add payment columns to order table
            try:
                conn.execute(text('''
                    ALTER TABLE "order" ADD COLUMN payment_method VARCHAR(20) NOT NULL DEFAULT 'cod'
                '''))
                conn.execute(text('''
                    ALTER TABLE "order" ADD COLUMN payment_status VARCHAR(20) NOT NULL DEFAULT 'pending'
                '''))
                conn.execute(text('''
                    ALTER TABLE "order" ADD COLUMN payment_details JSON
                '''))
                conn.execute(text('''
                    ALTER TABLE "order" ADD COLUMN payment_transaction_id VARCHAR(100)
                '''))
                conn.commit()
                print("Successfully added payment columns to order table")
            except Exception as e:
                print(f"Error adding payment columns (they might already exist): {e}")

if __name__ == '__main__':
    add_payment_columns()
