import psycopg2

DATABASE_URL = "postgresql://neondb_owner:npg_hMyon5KvqJU7@ep-solitary-leaf-anvjfaty-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def force_reset():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Force drop all tables with CASCADE
        tables = ['chat_message', 'appointment', 'prediction_record', 'clinical_memory', 'user', 'apscheduler_jobs']
        
        print("--- MASTER RESET STARTED ---")
        for table in tables:
            try:
                cur.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
                print(f"Dropped {table} (and dependents).")
            except Exception as e:
                print(f"Skipped {table}: {e}")
        
        conn.commit()
        cur.close()
        conn.close()
        print("\n--- DATABASE IS NOW COMPLETELY EMPTY! ---")
    except Exception as e:
        print(f"FATAL ERROR during reset: {e}")

if __name__ == "__main__":
    force_reset()
