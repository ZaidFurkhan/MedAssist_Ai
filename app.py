from flask import Flask, render_template, request, jsonify, session, redirect
import os
from dotenv import load_dotenv
import requests as http_requests
import random
import string
import json
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq
import threading

# Load environment variables
load_dotenv()
import pickle
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from ml.predict import predict_disease

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_demo_123')

# Initialize Groq clients
groq_client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
groq_insights_client = Groq(api_key=os.environ.get('GROQ_INSIGHTS_API_KEY', os.environ.get('GROQ_API_KEY')))

# --- Brevo API Configuration ---
def get_brevo_api_key():
    key = os.environ.get('BREVO_API_KEY', '')
    if not key:
        print("[EMAIL] FATAL ERROR: Could not find BREVO_API_KEY in environment variables")
    return key

BREVO_SENDER_EMAIL = os.environ.get('BREVO_SENDER_EMAIL', 'majidmaazzaidfurkhan@gmail.com')
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

# Define base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configure SQLAlchemy (PostgreSQL default for demo)
# Automatically handle Render/Heroku 'postgres://' database URLs
# Configure SQLAlchemy (Postgres with absolute SQLite fallback for Windows stability)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 280,
    'pool_timeout': 30,
}

# --- Database Configuration (Simplified) ---
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"[Database] Connection Error: {e}")

@app.route('/api/db-debug')
def db_debug():
    """Diagnostic route to check database connection status."""
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return jsonify({
            "status": "connected",
            "uri": app.config['SQLALCHEMY_DATABASE_URI'].split('@')[-1], # Mask password
            "message": "Successfully reached PostgreSQL!"
        })
    except Exception as e:
        return jsonify({
            "status": "failed",
            "error": str(e),
            "tip": "Check your DATABASE_URL in .env and ensure port 5432 is not blocked by your firewall."
        }), 500


# --- Flask-APScheduler Configuration ---
try:
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    print("[Scheduler] Started successfully.")
except Exception as e:
    print(f"[Scheduler] Warning: Could not start scheduler: {e}")
    scheduler = None

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class PredictionRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)  # JSON-encoded list
    predicted_disease = db.Column(db.String(255), nullable=False)
    top_predictions = db.Column(db.Text, nullable=False)  # JSON-encoded list
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    severity = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hospital_name = db.Column(db.String(255), nullable=False)
    doctor_name = db.Column(db.String(255), nullable=False)
    appointment_date = db.Column(db.String(50), nullable=False)
    appointment_time = db.Column(db.String(50), nullable=False)
    patient_name = db.Column(db.String(255), nullable=False)
    patient_phone = db.Column(db.String(50), nullable=False)
    appointment_type = db.Column(db.String(50), nullable=False, default="In-Person") # In-Person or Online
    clinical_brief = db.Column(db.Text, nullable=True) # JSON-encoded brief
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Reminder flags
    reminder_12h_sent = db.Column(db.Boolean, default=False)
    reminder_1h_sent = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'hospital_name': self.hospital_name,
            'doctor_name': self.doctor_name,
            'appointment_date': self.appointment_date,
            'appointment_time': self.appointment_time,
            'appointment_type': self.appointment_type,
            'patient_name': self.patient_name,
            'patient_phone': self.patient_phone,
            'created_at': self.created_at.isoformat()
        }


class ClinicalMemory(db.Model):
    """Stores AI-driven corrections to improve future ML predictions."""
    id = db.Column(db.Integer, primary_key=True)
    symptom_hash = db.Column(db.String(64), index=True) # Unique hash for a set of symptoms
    disease_name = db.Column(db.String(100))
    correction_count = db.Column(db.Integer, default=1) # How many times AI suggested this for these symptoms
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('symptom_hash', 'disease_name', name='_symptom_disease_uc'),)

def get_symptom_hash(symptoms):
    """Generate a stable hash for a sorted list of symptoms."""
    s_list = sorted([s.strip().lower() for s in symptoms])
    import hashlib
    return hashlib.sha256(",".join(s_list).encode()).hexdigest()

# Create tables if they don't exist
with app.app_context():
    try:
        db.create_all()
        print("Database tables verified.")
    except Exception as e:
        print(f"Warning: Could not connect to database or create tables. {e}")


# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model', 'disease_model.pkl')
SYMPTOMS_PATH = os.path.join(BASE_DIR, 'model', 'symptoms.pkl')

@app.route('/')
def index():
    """Render the main UI page."""
    user_id = session.get('user_id')
    user = db.session.get(User, user_id) if user_id else None
    return render_template('index.html', user=user)


def _background_send_verification_email(app_instance, to_email, code):
    """Background worker to send a verification code email via Brevo REST API."""
    try:
        html_content = f"""
        <div style="font-family:Inter,sans-serif;max-width:480px;margin:auto;padding:32px;">
            <h2 style="color:#4F46E5;margin-bottom:8px;">Verify Your Email</h2>
            <p style="color:#64748B;">Use the code below to complete your Smart CDSS registration:</p>
            <div style="background:#EEF2FF;border-radius:12px;padding:24px 32px;text-align:center;margin:24px 0;">
                <span style="font-size:2.5rem;font-weight:800;letter-spacing:8px;color:#4F46E5;">{code}</span>
            </div>
            <p style="color:#94A3B8;font-size:0.85rem;">If you didn't register, please ignore this email.</p>
        </div>
        """
        headers = {
            "accept": "application/json",
            "api-key": get_brevo_api_key(),
            "content-type": "application/json"
        }
        payload = {
            "sender": {"email": BREVO_SENDER_EMAIL, "name": "MedAssist.ai"},
            "to": [{"email": to_email}],
            "subject": "Your Verification Code",
            "htmlContent": html_content
        }
        # Don't technically need app_context here since REST API relies solely on env vars
        response = http_requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=10)
        
        if response.status_code in (200, 201, 202):
            print(f"[EMAIL] Verification code sent to {to_email} via Brevo REST API")
            return True
        else:
            print(f"[EMAIL] Brevo API Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"[EMAIL] Failed to send email via Brevo REST API: {e}")
        return False

def send_verification_email(app_instance, to_email, code):
    """
    Sends the verification email synchronously via Brevo REST API.
    Returns True if successful, False if it fails.
    """
    return _background_send_verification_email(app_instance, to_email, code)
        
def send_appointment_email(appointment, user_email, email_type='confirmation', clinical_brief=None):
    """Send appointment email synchronously via Brevo REST API."""
    try:
        if not user_email:
            print("[EMAIL] No user email provided, skipping appointment email.")
            return False

        subject_map = {
            'confirmation': 'Appointment Confirmation - MedAssist.ai',
            '12h_reminder': 'Appointment Reminder (12 Hours) - MedAssist.ai',
            '1h_reminder': 'Appointment Reminder (1 Hour) - MedAssist.ai'
        }
        title_map = {
            'confirmation': 'Appointment Confirmed',
            '12h_reminder': 'Upcoming Appointment (12h)',
            '1h_reminder': 'Upcoming Appointment (1h)'
        }

        # AI Clinical Brief Section
        brief_html = ""
        if clinical_brief and email_type == 'confirmation':
            summary = clinical_brief.get('summary', '')
            symptoms = clinical_brief.get('symptoms', [])
            symptoms_html = "".join([f'<span style="background:#EEF2FF;color:#4338CA;padding:4px 10px;border-radius:12px;font-size:0.85rem;margin-right:6px;display:inline-block;margin-bottom:6px;">{s}</span>' for s in symptoms])
            
            brief_html = f"""
            <div style="margin-top:24px;padding:20px;border:1.5px dashed #E0E7FF;border-radius:16px;background:#F5F7FF;">
                <h4 style="color:#4338CA;margin-top:0;margin-bottom:12px;font-size:0.95rem;text-transform:uppercase;letter-spacing:0.05em;">AI Clinical Brief</h4>
                <p style="color:#374151;font-size:0.95rem;line-height:1.5;margin-bottom:12px;">{summary}</p>
                <div style="margin-top:8px;">{symptoms_html}</div>
            </div>
            """

        html_content = f"""
        <div style="font-family:Inter,sans-serif;max-width:550px;margin:auto;padding:32px;border:1px solid #e2e8f0;border-radius:16px;">
            <div style="text-align:center;margin-bottom:24px;">
                <h1 style="color:#4F46E5;margin:0;font-size:1.5rem;">MedAssist.ai</h1>
            </div>
            <h2 style="color:#1E293B;margin-bottom:16px;font-size:1.25rem;">{title_map.get(email_type, 'Appointment Update')}</h2>
            <p style="color:#475569;font-size:1rem;margin-bottom:24px;">Hello <strong>{appointment.patient_name}</strong>, here are the details of your appointment:</p>
            
            <div style="background:#f8fafc;border-radius:12px;padding:20px;margin-bottom:24px;border:1px solid #f1f5f9;">
                <table style="width:100%;border-collapse:collapse;">
                    <tr><td style="padding:8px 0;color:#64748B;width:120px;font-size:0.9rem;">Hospital:</td><td style="padding:8px 0;color:#1E293B;font-weight:600;">{appointment.hospital_name}</td></tr>
                    <tr><td style="padding:8px 0;color:#64748B;font-size:0.9rem;">Doctor:</td><td style="padding:8px 0;color:#1E293B;font-weight:600;">{appointment.doctor_name}</td></tr>
                    <tr><td style="padding:8px 0;color:#64748B;font-size:0.9rem;">Date:</td><td style="padding:8px 0;color:#1E293B;font-weight:600;">{appointment.appointment_date}</td></tr>
                    <tr><td style="padding:8px 0;color:#64748B;font-size:0.9rem;">Time Slot:</td><td style="padding:8px 0;color:#1E293B;font-weight:600;">{appointment.appointment_time}</td></tr>
                    <tr><td style="padding:8px 0;color:#64748B;font-size:0.9rem;">Mode:</td><td style="padding:8px 0;color:#4F46E5;font-weight:700;">{appointment.appointment_type}</td></tr>
                </table>
            </div>

            {f'<div style="margin-bottom:24px;text-align:center;"><a href="https://meet.google.com/new" style="display:inline-block;background:#4F46E5;color:white;padding:12px 24px;border-radius:10px;text-decoration:none;font-weight:600;font-size:0.95rem;">🎥 Join Online Consultation</a><p style="color:#64748B;font-size:0.8rem;margin-top:8px;">Meeting link will be active at the scheduled time.</p></div>' if appointment.appointment_type == "Online" else ""}

            {brief_html}

            <div style="margin-top:32px;padding-top:16px;border-top:1px solid #f1f5f9;text-align:center;color:#94A3B8;font-size:0.8rem;">
                <p>This is an AI-assisted diagnostic brief. Always consult with your doctor for clinical decisions.</p>
                <p>&copy; 2024 MedAssist.ai - Your Intelligent Healthcare Partner</p>
            </div>
        </div>
        """

        headers = {
            "accept": "application/json",
            "api-key": get_brevo_api_key(),
            "content-type": "application/json"
        }
        payload = {
            "sender": {"email": BREVO_SENDER_EMAIL, "name": "MedAssist.ai Appointments"},
            "to": [{"email": user_email}],
            "subject": subject_map.get(email_type, 'Appointment Update'),
            "htmlContent": html_content
        }
        response = http_requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=10)

        if response.status_code in (200, 201, 202):
            print(f"[EMAIL] Appointment {email_type} email sent to {user_email} via Brevo REST API")
            return True
        else:
            print(f"[EMAIL] Brevo API Error: {response.text}")
            return False

    except Exception as e:
        print(f"[EMAIL] Failed to send appointment email via Brevo REST API: {e}")
        return False

def parse_appointment_time(date_str, time_str):
    """
    Helper to parse appointment date (YYYY-MM-DD) and time (HH:MM AM/PM) 
    into a datetime object.
    """
    try:
        combined_str = f"{date_str} {time_str}"
        return datetime.strptime(combined_str, "%Y-%m-%d %I:%M %p")
    except Exception as e:
        print(f"[SCHEDULER] Error parsing date/time ({date_str} {time_str}): {e}")
        return None

@scheduler.task('interval', id='check_reminders', minutes=10, misfire_grace_time=900)
def check_reminders():
    """Background job to check and send appointment reminders."""
    with app.app_context():
        # Get current time in IST (User's location)
        # Server (Render) is in UTC (usually), and users are in IST (+05:30)
        now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
        
        # Find all future appointments
        appointments = Appointment.query.filter(
            (Appointment.reminder_12h_sent == False) | (Appointment.reminder_1h_sent == False)
        ).all()
        
        for appt in appointments:
            appt_time = parse_appointment_time(appt.appointment_date, appt.appointment_time)
            if not appt_time:
                continue
                
            # Both appt_time and now_ist are now effectively "local IST" naive datetimes
            time_to_appt = appt_time - now_ist

            
            # 12h Reminder: time_to_appt <= 12 hours
            if not appt.reminder_12h_sent and timedelta(hours=0) < time_to_appt <= timedelta(hours=12):
                user = db.session.get(User, appt.user_id) if appt.user_id else None
                user_email = user.email if user else None
                if send_appointment_email(appt, user_email, email_type='12h_reminder'):
                    appt.reminder_12h_sent = True
                    db.session.commit()
            
            # 1h Reminder: time_to_appt <= 1 hour
            if not appt.reminder_1h_sent and timedelta(hours=0) < time_to_appt <= timedelta(hours=1):
                user = User.query.get(appt.user_id) if appt.user_id else None
                user_email = user.email if user else None
                if send_appointment_email(appt, user_email, email_type='1h_reminder'):
                    appt.reminder_1h_sent = True
                    db.session.commit()

@app.route('/api/test/check_reminders', methods=['GET'])
def test_check_reminders():
    """Manual trigger for testing the background job. In production, use a CRON_SECRET to secure this."""
    cron_secret = os.environ.get('CRON_SECRET')
    auth_header = request.headers.get('Authorization')
    
    # If CRON_SECRET is set, require it in the Authorization header
    if cron_secret and auth_header != f"Bearer {cron_secret}":
        return jsonify({"error": "Unauthorized"}), 401
        
    check_reminders()
    return jsonify({"message": "Reminder check triggered."}), 200


@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 400

        verification_code = ''.join(random.choices(string.digits, k=6))
        new_user = User(email=email, verification_code=verification_code)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        # Send OTP via Brevo API
        email_sent = send_verification_email(app, email, verification_code)

        if email_sent:
            return jsonify({"message": "Registration successful! Check your email for the OTP code."}), 201
        else:
            # Delete the user if email failed to send, so they can try again
            db.session.delete(new_user)
            db.session.commit()
            return jsonify({
                "error": "Failed to send verification email. Please ensure BREVO_API_KEY and BREVO_SENDER_EMAIL are correctly set in Vercel."
            }), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/verify', methods=['POST'])
def verify():
    try:
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')

        user = User.query.filter_by(email=email, verification_code=code).first()
        if not user:
            return jsonify({"error": "Invalid email or verification code"}), 400

        user.is_verified = True
        user.verification_code = None
        db.session.commit()

        return jsonify({"message": "Email verified successfully. You can now login."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid email or password"}), 401

        if not user.is_verified:
            return jsonify({"error": "Please verify your email first"}), 403

        session['user_id'] = user.id
        return jsonify({"message": "Login successful", "user_id": user.id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/history')
def history():
    """Render the full prediction history page. Requires login."""
    if 'user_id' not in session:
        return redirect('/?login_required=1')
    user = db.session.get(User, session['user_id'])
    return render_template('history.html', user=user)

@app.route('/appointments-history')
def appointments_history():
    """Render the full appointments history page. Requires login."""
    if 'user_id' not in session:
        return redirect('/?login_required=1')
    user = db.session.get(User, session['user_id'])
    return render_template('appointments_history.html', user=user)

@app.route('/appointment')
def appointment():
    """Render the appointment booking UI page. Requires login."""
    if 'user_id' not in session:
        return redirect('/?login_required=1')
    hospital_name = request.args.get('hospital', '')
    return render_template('appointment.html', hospital_name=hospital_name)

@app.route('/api/book_appointment', methods=['POST'])
def book_appointment():
    """Handle appointment booking requests and save to PostgreSQL."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided."}), 400
            
        required_fields = ['hospital_name', 'doctor_name', 'appointment_date', 'appointment_time', 'patient_name', 'patient_phone']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400
                
        user_id = session.get('user_id')
        new_appointment = Appointment(
            user_id=user_id,
            hospital_name=data['hospital_name'],
            doctor_name=data['doctor_name'],
            appointment_date=data['appointment_date'],
            appointment_time=data['appointment_time'],
            patient_name=data['patient_name'],
            patient_phone=data['patient_phone'],
            appointment_type=data.get('appointment_type', 'In-Person'),
            clinical_brief=json.dumps(data.get('clinical_brief')) if data.get('clinical_brief') else None
        )
        
        db.session.add(new_appointment)
        db.session.commit()
        
        # Send confirmation email
        user = db.session.get(User, user_id) if user_id else None
        user_email = user.email if user else None
        send_appointment_email(new_appointment, user_email, email_type='confirmation', clinical_brief=data.get('clinical_brief'))
        
        return jsonify({
            "message": "Appointment booked successfully!", 
            "appointment": new_appointment.to_dict()
        }), 201
        
    except Exception as e:
        print(f"Error booking appointment: {str(e)}")
        # In case DB is not set up correctly locally during demo, we return an error 500
        return jsonify({
            "error": "Failed to save appointment to database.", 
            "details": str(e)
        }), 500

@app.route('/api/symptoms', methods=['GET'])
def get_symptoms():
    """Return the list of all available symptoms for the frontend to render dynamically."""
    try:
        with open(SYMPTOMS_PATH, 'rb') as f:
            symptoms = pickle.load(f)
        
        # Filter out age_... and gender_... from being displayed as symptoms
        filtered_symptoms = [s for s in symptoms if not (s.startswith('age_') or s.startswith('gender_'))]
            
        return jsonify({"symptoms": filtered_symptoms})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def adjust_predictions_with_llm(symptoms, top_predictions, age=None, gender=None):
    """
    Use Groq LLM to refine and re-rank the statistical ML predictions 
    based on medical common sense and clinical logic.
    Also incorporates 'Clinical Memory' for self-learning.
    """
    s_hash = get_symptom_hash(symptoms)
    historical_corrections = ClinicalMemory.query.filter_by(symptom_hash=s_hash).all()
    
    # Format corrections for the AI to consider its own past "learning"
    memory_str = ""
    if historical_corrections:
        memory_str = "HISTORICAL CLINICAL MEMORY (Past Corrections):\n"
        for c in historical_corrections:
            memory_str += f"- {c.disease_name} (Suggested {c.correction_count} times previously)\n"

    preds_str = "\n".join([f"- {p['disease']} (ML Confidence: {p['probability']}%)" for p in top_predictions])
    
    prompt = f"""
USER PROFILE:
Symptoms: {', '.join(symptoms)}
Age Group: {age if age else 'Unknown'}
Gender: {gender if gender else 'Unknown'}

ML CANDIDATES:
{preds_str}

{memory_str}

TASK:
You are a clinical diagnostic expert. Re-rank the top 3 candidates.
Consider the ML confidence AND your past clinical memory if provided.

Respond ONLY with a JSON object:
{{
  "adjusted_top_3": [
    {{"disease": "Disease Name", "probability": adjusted_percentage}},
    ...
  ],
  "adjustment_reason": "Explanation."
}}
"""

    try:
        completion = groq_insights_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        response_text = completion.choices[0].message.content.strip()
        adjustment = json.loads(response_text)
        
        # Ensure the AI-adjusted list is sorted by probability
        if adjustment and 'adjusted_top_3' in adjustment:
            adjustment['adjusted_top_3'] = sorted(adjustment['adjusted_top_3'], key=lambda x: x['probability'], reverse=True)
            
        # Self-Learning Step: Update Clinical Memory
        if adjustment and 'adjusted_top_3' in adjustment:
            top_ai_disease = adjustment['adjusted_top_3'][0]['disease']
            try:
                record = ClinicalMemory.query.filter_by(symptom_hash=s_hash, disease_name=top_ai_disease).first()
                if record:
                    record.correction_count += 1
                    record.last_updated = datetime.utcnow()
                else:
                    new_mem = ClinicalMemory(symptom_hash=s_hash, disease_name=top_ai_disease)
                    db.session.add(new_mem)
                db.session.commit()
            except Exception as mem_err:
                db.session.rollback()
                print(f"[Learning-Error] {mem_err}")

        return adjustment
    except Exception as e:
        print(f"[AI-Adjustment] Error: {e}")
        return None

@app.route('/api/predict', methods=['POST'])
def predict():
    """Handle prediction requests from the frontend."""
    try:
        data = request.get_json()
        if not data or 'symptoms' not in data:
            return jsonify({"error": "No symptoms provided. Please send a JSON with a 'symptoms' key."}), 400
            
        user_symptoms = data.get('symptoms', [])
        user_age_raw = data.get('age')
        try:
            user_age = int(user_age_raw) if user_age_raw else None
        except (ValueError, TypeError):
            user_age = None
            
        user_gender = data.get('gender')
        
        # Predict the disease
        prediction = predict_disease(user_symptoms, age=user_age, gender=user_gender, model_path=MODEL_PATH, symptoms_path=SYMPTOMS_PATH)
        
        # Step 2: Adjust predictions with AI Reasoning
        adjusted = adjust_predictions_with_llm(user_symptoms, prediction['top_predictions'], age=user_age, gender=user_gender)
        
        if adjusted and 'adjusted_top_3' in adjusted:
            print(f"[AI-Adjustment] Reasoning: {adjusted.get('adjustment_reason')}")
            prediction['top_predictions'] = adjusted['adjusted_top_3']
            prediction['prediction'] = adjusted['adjusted_top_3'][0]['disease']
            prediction['ai_verified'] = True
        else:
            prediction['ai_verified'] = False
            
        # Store prediction if user is logged in
        user_id = session.get('user_id')
        if user_id:
            print(f"[Database] Attempting to save prediction for User {user_id}...")
            try:
                record = PredictionRecord(
                    user_id=user_id,
                    symptoms=json.dumps(user_symptoms),
                    predicted_disease=prediction['prediction'],
                    top_predictions=json.dumps(prediction['top_predictions']),
                    age=user_age,
                    gender=user_gender,
                    severity=prediction.get('severity')
                )
                db.session.add(record)
                db.session.commit()
                print(f"[Database] Successfully saved prediction for User {user_id}")
            except Exception as e:
                db.session.rollback()
                print(f"[Database] FATAL ERROR saving prediction for User {user_id}: {str(e)}")
        else:
            print("[Database] Guest scan detected. Skipping history save.")

        return jsonify(prediction)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import requests

@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    """Fetch nearby hospitals using Geoapify Places API, prioritizing relevant specialties."""
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    disease = request.args.get('disease', '').lower()
    
    if not lat or not lon:
        return jsonify({"error": "Latitude and longitude are required."}), 400
        
    try:
        api_key = os.environ.get('GEOAPIFY_API_KEY')
        if not api_key:
            return jsonify({"error": "Geoapify API key not configured."}), 500

        # Geoapify Categories for medical facilities
        categories = "healthcare.hospital,healthcare.clinic_or_praxis"
        
        # Wise use of API: We fetch a broad 10km radius in ONE call 
        # and then do all the ranking and iterative logic locally in Python.
        radius = 10000 
        
        geoapify_url = "https://api.geoapify.com/v2/places"
        params = {
            "categories": categories,
            "filter": f"circle:{lon},{lat},{radius}",
            "bias": f"proximity:{lon},{lat}",
            "limit": 60, # Fetch more to allow for diverse local filtering
            "apiKey": api_key
        }
        
        response = http_requests.get(geoapify_url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        # Broad mapping for 'Discovery Mode' and sorting
        default_specialties = {
            'cardiology': ['cardiology', 'heart', 'cardiac'],
            'orthopaedics': ['orthopaedics', 'bone', 'joint', 'spine', 'fracture'],
            'dermatology': ['dermatology', 'skin', 'clinic'],
            'pediatrics': ['pediatrics', 'child', 'infant', 'neonatal'],
            'neurology': ['neurology', 'brain', 'nerve'],
            'emergency': ['emergency', 'trauma', 'icu', 'critical']
        }

        specialty_keywords = {
            'arthritis': ['orthopaedics', 'joint', 'arthritis'],
            'heart attack': ['cardiology', 'heart', 'cardiac'],
            'hypertension': ['cardiology', 'heart'],
            'diabetes': ['endocrinology', 'diabetes'],
            'migraine': ['neurology', 'brain'],
            'stroke': ['neurology', 'emergency'],
            'asthma': ['pulmonology', 'lung', 'respiratory'],
            'tuberculosis': ['pulmonology', 'chest'],
            'pneumonia': ['pulmonology', 'respiratory'],
            'psoriasis': ['dermatology', 'skin'],
            'acne': ['dermatology', 'skin'],
            'fungal infection': ['dermatology', 'skin'],
            'gastroenteritis': ['gastroenterology', 'stomach'],
            'peptic ulcer diseae': ['gastroenterology'],
            'jaundice': ['gastroenterology', 'liver'],
            'hepatitis': ['hepatology', 'liver'],
            'urinary tract infection': ['urology', 'kidney'],
            'cervical spondylosis': ['orthopaedics', 'spine'],
            'osteorthritis': ['orthopaedics', 'joint']
        }
        
        target_keywords = []
        for d_key, k_vals in specialty_keywords.items():
            if d_key in disease:
                target_keywords = k_vals
                break
            
        
        hospitals = []
        for feature in data.get('features', []):
            prop = feature.get('properties', {})
            name = prop.get('name')
            if not name: continue
                
            h_lat = prop.get('lat')
            h_lon = prop.get('lon')
            categories_text = " ".join(prop.get('categories', []))
            full_text = (name + " " + categories_text).lower()
            h_dist = prop.get('distance', 99999)
            
            # Check for specialty matching
            is_disease_specialist = False
            matched_specialty = "General Healthcare"
            
            # 1. If disease is provided, check if it's a direct match
            if disease and target_keywords:
                if any(kw in full_text for kw in target_keywords):
                    is_disease_specialist = True
                    matched_specialty = target_keywords[0].capitalize()
            
            # 2. Check against common specialties for Discovery Mode or tagging
            specialty_tag = None
            for spec, kws in default_specialties.items():
                if any(kw in full_text for kw in kws):
                    specialty_tag = spec.capitalize()
                    if matched_specialty == "General Healthcare":
                        matched_specialty = specialty_tag
                    break

            hospitals.append({
                "name": name,
                "lat": h_lat,
                "lon": h_lon,
                "address": prop.get('formatted', prop.get('address_line2', 'Address not available')),
                "phone": prop.get('contact', {}).get('phone', 'Phone not available'),
                "is_specialized": is_disease_specialist,
                "specialty": matched_specialty,
                "distance": h_dist
            })
            
        # Ranking & Filtering Logic (All local to save API quota)
        if disease:
            # Targeted Mode:
            # Rank 1: Specialized within 5km
            # Rank 2: Specialized within 10km
            # Rank 3: General within 5km
            # Rank 4: General within 10km
            def targeted_rank(h):
                if h['is_specialized'] and h['distance'] <= 5000: return 1
                if h['is_specialized']: return 2
                if h['distance'] <= 5000: return 3
                return 4
            hospitals.sort(key=lambda h: (targeted_rank(h), h['distance']))
        else:
            # Discovery Mode: Ensure we show one best of each specialty first
            seen_specs = set()
            diverse = []
            others = []
            for h in sorted(hospitals, key=lambda x: x['distance']):
                if h['specialty'] != "General Healthcare" and h['specialty'] not in seen_specs:
                    diverse.append(h)
                    seen_specs.add(h['specialty'])
                else:
                    others.append(h)
            hospitals = diverse + others
            
        seen = set()
        clean_hospitals = []
        for h in hospitals:
            if h['name'] not in seen:
                seen.add(h['name'])
                clean_hospitals.append(h)
                
        return jsonify({
            "hospitals": clean_hospitals[:15],
            "target_specialty": target_keywords[0].capitalize() if (disease and target_keywords) else None
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch hospitals: {str(e)}"}), 500

@app.route('/api/user/data', methods=['GET'])
def get_user_data():
    """Retrieve history of predictions and appointments for the logged-in user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    try:
        predictions = PredictionRecord.query.filter_by(user_id=user_id).order_by(PredictionRecord.created_at.desc()).all()
        appointments = Appointment.query.filter_by(user_id=user_id).order_by(Appointment.created_at.desc()).all()
        
        return jsonify({
            "user_id": user_id,
            "predictions": [{
                "id": p.id,
                "symptoms": json.loads(p.symptoms),
                "predicted_disease": p.predicted_disease,
                "top_predictions": json.loads(p.top_predictions),
                "created_at": p.created_at.isoformat()
            } for p in predictions],
            "appointments": [a.to_dict() for a in appointments]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chatbot queries using Groq Cloud LLM."""
    data = request.get_json()
    if not data or 'messages' not in data:
        return jsonify({"error": "Messages payload required."}), 400
        
    try:
        messages = data['messages']
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=655,
            temperature=0.7
        )
        reply = completion.choices[0].message.content
        return jsonify({"response": reply})
    except Exception as e:
        err_msg = str(e)
        print(f"[Chat] Groq error: {err_msg}")
        return jsonify({"error": f"AI error (for debugging): {err_msg}"}), 500

@app.route('/api/health-insights', methods=['POST'])
def get_health_insights():
    """Generate structured health insights based on prediction results using Groq LLM."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    symptoms = data.get('symptoms', [])
    top_predictions = data.get('top_predictions', [])
    severity = data.get('severity', 'moderate')
    medicines = data.get('medicines', 'None')

    if not top_predictions:
        return jsonify({"error": "Top predictions are required"}), 400

    # Format predictions for prompt
    preds_str = "\n".join([f"{p['disease']} ({p['probability']}%)" for p in top_predictions])

    prompt = f"""
INPUT:
Symptoms: {', '.join(symptoms)}
Top 3 Predictions:
{preds_str}
Severity: {severity}
Suggested Medicines (if any): {medicines}

TASK:
Generate a HIGHLY DETAILED, comprehensive narrative health report.

STRUCTURE:
1. Introduction & Explanation: Deeply explain the most likely condition based on the symptoms. Describe what it is, how it affects the body, and the pathological context in simple but thorough terms.
2. Reasoning: Explicitly connect the symptoms provided to the predictions.
3. Alternatives: Mention the other possibilities and why they are less likely.
4. Comprehensive Guidance: Provide in-depth advice covering:
   - Immediate precautions
   - Lifestyle adjustments
   - Detailed dietary suggestions
   - Self-care (for low/moderate) or emergency instructions (for critical).

RULES:
- DO NOT use any sub-headings (like 'Diet', 'Precautions', etc.). Use bold text for emphasis and paragraph breaks for structure.
- The tone must be professional, reassuring, and extremely thorough.
- Adapt the intensity based on the severity: {severity}.
- For CRITICAL severity, the priority is immediate medical attention.
- Do NOT prescribe specific dosages.
- Response must be a single cohesive narrative.

OUTPUT FORMAT (STRICT JSON):
{{
"summary": "1-2 sentence high-level overview.",
"explanation": "Deep pathological explanation of the condition.",
"symptom_analysis": [
  {{"symptom": "symptom name", "connection": "how it relates to the condition"}}
],
"precautions": ["step 1", "step 2", ...],
"diet": ["advice 1", "advice 2", ...],
"lifestyle": ["tip 1", "tip 2", ...],
"roadmap": ["step 1 (monitor)", "step 2 (action)", "step 3 (seek care)"],
"alternatives": "Briefly mention other 1-2 possibilities and why they are less likely.",
"severity": "{severity}",
"warning": "Safety disclaimer."
}}
"""

    try:
        completion = groq_insights_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        response_text = completion.choices[0].message.content.strip()
        return jsonify(json.loads(response_text))
    except Exception as e:
        print(f"[HealthInsights] Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/disease-info', methods=['GET'])
def get_disease_info():
    """Generate detailed information about a disease using Groq Cloud LLM."""
    disease = request.args.get('disease')
    if not disease:
        return jsonify({"error": "Disease parameter is required."}), 400
        
    if not os.environ.get('GROQ_API_KEY'):
        return jsonify({"error": "GROQ_API_KEY is not configured in environment variables."}), 500
        
    import re
    prompt = (
        f"Provide a comprehensive but concise summary of the disease '{disease}'. "
        f"Format the output carefully in JSON with exactly four keys: "
        f"'severity' (a short string like 'Low', 'Moderate', 'High', or 'Critical'), "
        f"'description' (a 2-3 sentence overview), 'precautions' (an array of 3-5 strings), "
        f"and 'diet' (an array of 3-5 strings of dietary advice). Respond with ONLY valid JSON, no markdown."
    )
    
    try:
        completion = groq_insights_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.3
        )
        response_text = completion.choices[0].message.content.strip()
        
        # Strip markdown code fences if present
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        json_str = json_match.group(1) if json_match else response_text
        
        info_data = json.loads(json_str)
        return jsonify(info_data)
    except json.JSONDecodeError as e:
        print(f"[DiseaseInfo] JSON parse error: {e} | Response: {response_text}")
        return jsonify({"error": "Failed to parse info from AI provider."}), 500
    except Exception as e:
        print(f"[DiseaseInfo] Groq error: {e}")
        return jsonify({
            "error": "Failed to fetch disease info.",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    # Run the app locally on port 5000
    app.run(debug=True, port=5000)
