from app import app, db
from sqlalchemy import text

def update_db():
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Add reminder_12h_sent column
                conn.execute(text("ALTER TABLE appointment ADD COLUMN IF NOT EXISTS reminder_12h_sent BOOLEAN DEFAULT FALSE"))
                # Add reminder_1h_sent column
                conn.execute(text("ALTER TABLE appointment ADD COLUMN IF NOT EXISTS reminder_1h_sent BOOLEAN DEFAULT FALSE"))
                conn.commit()
                print("Successfully added reminder columns to the appointment table.")
        except Exception as e:
            print(f"Error updating appointment table: {e}")

if __name__ == "__main__":
    update_db()
