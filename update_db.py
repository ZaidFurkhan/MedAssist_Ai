from app import app, db
from sqlalchemy import text

def update_db():
    with app.app_context():
        try:
            # Check if user_id exists in appointment table
            with db.engine.connect() as conn:
                # Add user_id column to appointment table if it doesn't exist
                conn.execute(text("ALTER TABLE appointment ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES \"user\"(id)"))
                conn.commit()
                print("Added user_id column to appointment table.")
        except Exception as e:
            print(f"Error updating appointment table: {e}")

if __name__ == "__main__":
    update_db()
