import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Load environment variables
DATABASE_URL = "postgresql://neondb_owner:npg_hMyon5KvqJU7@ep-solitary-leaf-anvjfaty-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PredictionRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    predicted_disease = db.Column(db.String(255), nullable=False)
    top_predictions = db.Column(db.Text, nullable=False)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    severity = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    hospital_name = db.Column(db.String(255), nullable=False)
    doctor_name = db.Column(db.String(255), nullable=False)
    appointment_date = db.Column(db.String(50), nullable=False)
    appointment_time = db.Column(db.String(50), nullable=False)
    patient_name = db.Column(db.String(255), nullable=False)
    patient_phone = db.Column(db.String(50), nullable=False)
    appointment_type = db.Column(db.String(50), default='In-Person')
    clinical_brief = db.Column(db.Text, nullable=True)
    reminder_12h_sent = db.Column(db.Boolean, default=False)
    reminder_1h_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ClinicalMemory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symptom_hash = db.Column(db.String(64), index=True)
    disease_name = db.Column(db.String(100))
    correction_count = db.Column(db.Integer, default=1)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('symptom_hash', 'disease_name', name='_symptom_disease_uc'),)

def init():
    with app.app_context():
        print("--- FINAL CLEAN DATABASE REFRESH STARTED ---")
        try:
            db.drop_all()
            print("[1/2] Dropped existing tables.")
            db.create_all()
            print("[2/2] Created fresh tables (Severity, Clinical Memory, Age/Gender included).")
            print("\n--- DATABASE IS NOW READY AND MINIMAL! ---")
        except Exception as e:
            print(f"\nFATAL ERROR: {str(e)}")

if __name__ == "__main__":
    init()
