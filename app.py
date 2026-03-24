from flask import Flask, render_template, request, jsonify, session, redirect
import os
from dotenv import load_dotenv
from flask_mail import Mail, Message
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

# Initialize Groq client
groq_client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

# --- Flask-Mail Configuration (Gmail) ---
# Using SSL (Port 465) instead of STARTTLS (Port 587) prevents cloud firewalls 
# from inspecting the SMTP handshake and causing indefinite hanging/timeouts.
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')       # your Gmail address
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')       # Gmail App Password (not regular password)
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME') # same as username
mail = Mail(app)

# Configure SQLAlchemy (PostgreSQL default for demo)
# Automatically handle Render/Heroku 'postgres://' database URLs
db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/smartcdss')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CRITICAL FIX for Neon DB on Render:
# Neon automatically closes idle connections after a few minutes, causing Gunicorn to hang and timeout.
# pool_pre_ping=True forces SQLAlchemy to check the connection before sending queries.
# pool_recycle=280 reconnects silently every 4.6 minutes.
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 280,
    'pool_timeout': 30,
}
db = SQLAlchemy(app)

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hospital_name = db.Column(db.String(255), nullable=False)
    doctor_name = db.Column(db.String(255), nullable=False)
    appointment_date = db.Column(db.String(50), nullable=False)
    appointment_time = db.Column(db.String(50), nullable=False)
    patient_name = db.Column(db.String(255), nullable=False)
    patient_phone = db.Column(db.String(50), nullable=False)
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
            'patient_name': self.patient_name,
            'patient_phone': self.patient_phone,
            'created_at': self.created_at.isoformat()
        }

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
    user = User.query.get(user_id) if user_id else None
    return render_template('index.html', user=user)


def _background_send_verification_email(app_instance, to_email, code):
    """Background worker to send a verification code email."""
    try:
        with app_instance.app_context():
            msg = Message(
                subject="Your Smart CDSS Verification Code",
                recipients=[to_email]
            )
            msg.html = f"""
            <div style="font-family:Inter,sans-serif;max-width:480px;margin:auto;padding:32px;">
                <h2 style="color:#4F46E5;margin-bottom:8px;">Verify Your Email</h2>
                <p style="color:#64748B;">Use the code below to complete your Smart CDSS registration:</p>
                <div style="background:#EEF2FF;border-radius:12px;padding:24px 32px;text-align:center;margin:24px 0;">
                    <span style="font-size:2.5rem;font-weight:800;letter-spacing:8px;color:#4F46E5;">{code}</span>
                </div>
                <p style="color:#94A3B8;font-size:0.85rem;">If you didn't register, please ignore this email.</p>
            </div>
            """
            mail.send(msg)
            print(f"[EMAIL] Verification code sent to {to_email}")
    except Exception as e:
        print(f"[EMAIL] Failed to send email (SMTP Block/Timeout): {e}")

def send_verification_email(app_instance, to_email, code):
    """
    Spawns a background thread attempting to send the email.
    Instantly returns False so the UI provides the Fallback Demo Code,
    preventing Render's SMTP block from crashing the main request.
    """
    thread = threading.Thread(target=_background_send_verification_email, args=(app_instance, to_email, code))
    thread.daemon = True
    thread.start()
    return False
        
def _background_send_appointment_email(app_instance, appointment, email_type):
    """Background worker to send appointment emails."""
    try:
        with app_instance.app_context():
            if not appointment.user_id:
                return
            user = User.query.get(appointment.user_id)
            if not user or not user.email:
                return
            
            subject_map = {
                'confirmation': 'Appointment Confirmation - Smart CDSS',
                '12h_reminder': 'Appointment Reminder (12 Hours) - Smart CDSS',
                '1h_reminder': 'Appointment Reminder (1 Hour) - Smart CDSS'
            }
            title_map = {
                'confirmation': 'Appointment Confirmed',
                '12h_reminder': 'Upcoming Appointment (12h)',
                '1h_reminder': 'Upcoming Appointment (1h)'
            }
            
            msg = Message(
                subject=subject_map.get(email_type, 'Appointment Update'),
                recipients=[user.email]
            )
            msg.html = f"""
            <div style="font-family:Inter,sans-serif;max-width:550px;margin:auto;padding:32px;border:1px solid #e2e8f0;border-radius:16px;">
                <h2 style="color:#4F46E5;margin-bottom:16px;">{title_map.get(email_type, 'Appointment Update')}</h2>
                <p style="color:#475569;font-size:1.1rem;margin-bottom:24px;">Hello <strong>{appointment.patient_name}</strong>, here are the details of your appointment:</p>
                
                <div style="background:#f8fafc;border-radius:12px;padding:20px;margin-bottom:24px;">
                    <table style="width:100%;border-collapse:collapse;">
                        <tr><td style="padding:8px 0;color:#64748B;width:120px;">Hospital:</td><td style="padding:8px 0;color:#1E293B;font-weight:600;">{appointment.hospital_name}</td></tr>
                        <tr><td style="padding:8px 0;color:#64748B;">Doctor:</td><td style="padding:8px 0;color:#1E293B;font-weight:600;">{appointment.doctor_name}</td></tr>
                        <tr><td style="padding:8px 0;color:#64748B;">Date:</td><td style="padding:8px 0;color:#1E293B;font-weight:600;">{appointment.appointment_date}</td></tr>
                        <tr><td style="padding:8px 0;color:#64748B;">Time Slot:</td><td style="padding:8px 0;color:#1E293B;font-weight:600;">{appointment.appointment_time}</td></tr>
                    </table>
                </div>
            </div>
            """
            mail.send(msg)
            print(f"[EMAIL] Appointment {email_type} email sent to {user.email}")
    except Exception as e:
        print(f"[EMAIL] Failed to send appointment email (SMTP Block/Timeout): {e}")

def send_appointment_email(app_instance, appointment, email_type='confirmation'):
    """Spawns a background thread to send the appointment email, preventing web timeouts."""
    thread = threading.Thread(target=_background_send_appointment_email, args=(app_instance, appointment, email_type))
    thread.daemon = True
    thread.start()
    return True

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
        now = datetime.utcnow()
        # Find all future appointments
        appointments = Appointment.query.filter(
            (Appointment.reminder_12h_sent == False) | (Appointment.reminder_1h_sent == False)
        ).all()
        
        for appt in appointments:
            appt_time = parse_appointment_time(appt.appointment_date, appt.appointment_time)
            if not appt_time:
                continue
                
            time_to_appt = appt_time - now
            
            # 12h Reminder: time_to_appt <= 12 hours
            if not appt.reminder_12h_sent and timedelta(hours=0) < time_to_appt <= timedelta(hours=12):
                if send_appointment_email(app, appt, email_type='12h_reminder'):
                    appt.reminder_12h_sent = True
                    db.session.commit()
            
            # 1h Reminder: time_to_appt <= 1 hour
            if not appt.reminder_1h_sent and timedelta(hours=0) < time_to_appt <= timedelta(hours=1):
                if send_appointment_email(app, appt, email_type='1h_reminder'):
                    appt.reminder_1h_sent = True
                    db.session.commit()

@app.route('/api/test/check_reminders', methods=['GET'])
def test_check_reminders():
    """Manual trigger for testing the background job."""
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

        # Send OTP via Gmail
        email_sent = send_verification_email(app, email, verification_code)

        if email_sent:
            return jsonify({"message": "Registration successful! Check your email for the OTP code."}), 201
        else:
            # Fallback demo mode
            return jsonify({
                "message": "Registration successful! (Email unavailable - use code to verify)",
                "demo_code": verification_code
            }), 201

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
    user = User.query.get(session['user_id'])
    return render_template('history.html', user=user)

@app.route('/appointments-history')
def appointments_history():
    """Render the full appointments history page. Requires login."""
    if 'user_id' not in session:
        return redirect('/?login_required=1')
    user = User.query.get(session['user_id'])
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
            patient_phone=data['patient_phone']
        )
        
        db.session.add(new_appointment)
        db.session.commit()
        
        # Send confirmation email
        send_appointment_email(app, new_appointment, email_type='confirmation')
        
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
        return jsonify({"symptoms": symptoms})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def predict():
    """Handle prediction requests from the frontend."""
    try:
        data = request.get_json()
        if not data or 'symptoms' not in data:
            return jsonify({"error": "No symptoms provided. Please send a JSON with a 'symptoms' key."}), 400
            
        user_symptoms = data['symptoms']
        user_age = data.get('age')
        user_gender = data.get('gender')
        
        # Predict the disease
        prediction = predict_disease(user_symptoms, age=user_age, gender=user_gender, model_path=MODEL_PATH, symptoms_path=SYMPTOMS_PATH)
        
        if "error" in prediction:
            return jsonify(prediction), 500
            
        # Store prediction if user is logged in
        user_id = session.get('user_id')
        if user_id:
            try:
                record = PredictionRecord(
                    user_id=user_id,
                    symptoms=json.dumps(user_symptoms),
                    predicted_disease=prediction['prediction'],
                    top_predictions=json.dumps(prediction['top_predictions'])
                )
                db.session.add(record)
                db.session.commit()
            except Exception as e:
                print(f"Error saving prediction record: {e}")

        return jsonify(prediction)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import requests

@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    """Fetch nearby hospitals using Overpass API, prioritizing relevant specialties."""
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    disease = request.args.get('disease', '').lower()
    
    if not lat or not lon:
        return jsonify({"error": "Latitude and longitude are required."}), 400
        
    try:
        lat = float(lat)
        lon = float(lon)
        radius = 10000 # 10km search
        
        # Map common predicted diseases to OpenStreetMap healthcare specialties
        specialty_map = {
            'arthritis': 'orthopaedics',
            'heart attack': 'cardiology',
            'hypertension': 'cardiology',
            'diabetes': 'endocrinology',
            'migraine': 'neurology',
            'stroke': 'neurology',
            'asthma': 'pulmonology',
            'tuberculosis': 'pulmonology',
            'pneumonia': 'pulmonology',
            'allergy': 'allergology',
            'psoriasis': 'dermatology',
            'acne': 'dermatology',
            'fungal infection': 'dermatology',
            'gastroenteritis': 'gastroenterology',
            'peptic ulcer diseae': 'gastroenterology',
            'jaundice': 'gastroenterology',
            'hepatitis': 'hepatology',
            'urinary tract infection': 'urology',
            'cervical spondylosis': 'orthopaedics',
            'osteorthritis': 'orthopaedics'
        }
        
        # Determine if we should search for a specific tag
        tag_filter = ""
        specialty = None
        for d_key, s_val in specialty_map.items():
            if d_key in disease:
                specialty = s_val
                break
                
        if specialty:
            # Query explicitly for the specialty, or generic hospitals as fallback
            overpass_query = f"""
            [out:json];
            (
              node["healthcare:speciality"="{specialty}"](around:{radius},{lat},{lon});
              way["healthcare:speciality"="{specialty}"](around:{radius},{lat},{lon});
              relation["healthcare:speciality"="{specialty}"](around:{radius},{lat},{lon});
              
              node["amenity"="hospital"](around:{radius},{lat},{lon});
              way["amenity"="hospital"](around:{radius},{lat},{lon});
              relation["amenity"="hospital"](around:{radius},{lat},{lon});
            );
            out center;
            """
        else:
            # Generic hospital query
            overpass_query = f"""
            [out:json];
            (
              node["amenity"="hospital"](around:{radius},{lat},{lon});
              way["amenity"="hospital"](around:{radius},{lat},{lon});
              relation["amenity"="hospital"](around:{radius},{lat},{lon});
              
              node["amenity"="clinic"](around:{radius},{lat},{lon});
              way["amenity"="clinic"](around:{radius},{lat},{lon});
              relation["amenity"="clinic"](around:{radius},{lat},{lon});
            );
            out center;
            """
            
        overpass_url = "http://overpass-api.de/api/interpreter"
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        hospitals = []
        for element in data.get('elements', []):
            tags = element.get('tags', {})
            name = tags.get('name')
            
            if not name:
                continue
                
            h_lat = element.get('lat', element.get('center', {}).get('lat'))
            h_lon = element.get('lon', element.get('center', {}).get('lon'))
            
            h_specialty = tags.get('healthcare:speciality', '').lower()
            
            # Prioritize sorting: If it matches our specialty, flag it
            is_specialized = bool(specialty and specialty in h_specialty)
            
            hospitals.append({
                "name": name,
                "lat": h_lat,
                "lon": h_lon,
                "address": tags.get('addr:full', tags.get('addr:street', 'Address not available')),
                "phone": tags.get('phone', 'Phone not available'),
                "is_specialized": is_specialized,
                "specialty_tag": tags.get('healthcare:speciality', 'General')
            })
            
        # Sort: Specialized facilities first
        hospitals.sort(key=lambda x: str(x['is_specialized']), reverse=True)
            
        # Return top 10 unique names
        seen = set()
        clean_hospitals = []
        for h in hospitals:
            if h['name'] not in seen:
                seen.add(h['name'])
                clean_hospitals.append(h)
                
        return jsonify({"hospitals": clean_hospitals[:10], "target_specialty": specialty})
        
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
            max_tokens=512,
            temperature=0.7
        )
        reply = completion.choices[0].message.content
        return jsonify({"response": reply})
    except Exception as e:
        err_msg = str(e)
        print(f"[Chat] Groq error: {err_msg}")
        return jsonify({"error": f"AI error (for debugging): {err_msg}"}), 500

@app.route('/api/disease-info', methods=['GET'])
def get_disease_info():
    """Generate detailed information about a disease using Groq Cloud LLM."""
    disease = request.args.get('disease')
    if not disease:
        return jsonify({"error": "Disease parameter is required."}), 400
        
    import re
    prompt = (
        f"Provide a comprehensive but concise summary of the disease '{disease}'. "
        f"Format the output carefully in JSON with exactly four keys: "
        f"'severity' (a short string like 'Low', 'Moderate', 'High', or 'Critical'), "
        f"'description' (a 2-3 sentence overview), 'precautions' (an array of 3-5 strings), "
        f"and 'diet' (an array of 3-5 strings of dietary advice). Respond with ONLY valid JSON, no markdown."
    )
    
    try:
        completion = groq_client.chat.completions.create(
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
        return jsonify({"error": f"Failed to fetch disease info."}), 500

if __name__ == '__main__':
    # Run the app locally on port 5000
    app.run(debug=True, port=5000)
