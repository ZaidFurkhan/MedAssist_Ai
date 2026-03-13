from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
import pickle
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from ml.predict import predict_disease

# Initialize Flask app
app = Flask(__name__)

# Configure SQLAlchemy (PostgreSQL default for demo)
# Automatically handle Render/Heroku 'postgres://' database URLs
db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/smartcdss')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model for Appointments
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hospital_name = db.Column(db.String(255), nullable=False)
    doctor_name = db.Column(db.String(255), nullable=False)
    appointment_date = db.Column(db.String(50), nullable=False)
    appointment_time = db.Column(db.String(50), nullable=False)
    patient_name = db.Column(db.String(255), nullable=False)
    patient_phone = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
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
    return render_template('index.html')

@app.route('/appointment')
def appointment():
    """Render the appointment booking UI page."""
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
                
        new_appointment = Appointment(
            hospital_name=data['hospital_name'],
            doctor_name=data['doctor_name'],
            appointment_date=data['appointment_date'],
            appointment_time=data['appointment_time'],
            patient_name=data['patient_name'],
            patient_phone=data['patient_phone']
        )
        
        db.session.add(new_appointment)
        db.session.commit()
        
        return jsonify({
            "message": "Appointment booked successfully!", 
            "appointment": new_appointment.to_dict()
        }), 201
        
    except Exception as e:
        print(f"Error booking appointment: {str(e)}")
        # In case DB is not set up correctly locally during demo, we fallback to a fake success message
        return jsonify({
            "message": "Appointment booked successfully (Demo Mode - DB Warning)", 
            "error_log": str(e),
            "appointment": data
        }), 201

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
            
        return jsonify(prediction)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import requests
import g4f

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

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chatbot queries using g4f."""
    data = request.get_json()
    if not data or 'messages' not in data:
        return jsonify({"error": "Messages payload required."}), 400
        
    try:
        # Expected format: [{"role": "user"/"assistant", "content": "..."}]
        messages = data['messages']
        
        # Call g4f free provider
        response = g4f.ChatCompletion.create(
            model="openai",
            messages=messages,
            provider=g4f.Provider.PollinationsAI
        )
        
        return jsonify({"response": response})
        
    except Exception as e:
        # Fallback if preferred provider fails
        try:
            print(f"Fallback due to {e}")
            response = g4f.ChatCompletion.create(
                model="openai",
                messages=messages,
                provider=g4f.Provider.PollinationsAI
            )
            return jsonify({"response": response})
        except Exception as fallback_e:
            return jsonify({"error": str(fallback_e)}), 500

@app.route('/api/disease-info', methods=['GET'])
def get_disease_info():
    """Generate detailed information about a disease using g4f."""
    disease = request.args.get('disease')
    if not disease:
        return jsonify({"error": "Disease parameter is required."}), 400
        
    try:
        prompt = (
            f"Provide a comprehensive but concise summary of the disease '{disease}'. "
            f"Format the output carefully in JSON with exactly four keys: "
            f"'severity' (a short string like 'Low', 'Moderate', 'High', or 'Critical'), "
            f"'description' (a 2-3 sentence overview), 'precautions' (an array of 3-5 strings), "
            f"and 'diet' (an array of 3-5 strings of dietary advice). Ensure the response is valid JSON."
        )
        
        response = g4f.ChatCompletion.create(
            model="openai",
            messages=[{"role": "user", "content": prompt}],
            provider=g4f.Provider.PollinationsAI
        )
        
        import json
        import re
        
        # Try to extract JSON from markdown formatting if present
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response
            
        try:
            info_data = json.loads(json_str)
            return jsonify(info_data)
        except json.JSONDecodeError:
            print(f"Failed to parse LLM JSON output: {response}")
            return jsonify({"error": "Failed to parse info from AI provider."}), 500

    except Exception as e:
        print(f"Primary fetch failed: {e}")
        # Fallback if preferred provider fails
        try:
            response = g4f.ChatCompletion.create(
                model="openai",
                messages=[{"role": "user", "content": prompt}],
                provider=g4f.Provider.PollinationsAI
            )
            # Basic parsing assumption
            import json
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            json_str = json_match.group(1) if json_match else response
            info_data = json.loads(json_str)
            return jsonify(info_data)
        except Exception as fallback_e:
            return jsonify({"error": f"Failed to fetch disease info: {str(fallback_e)}"}), 500

if __name__ == '__main__':
    # Run the app locally on port 5000
    app.run(debug=True, port=5000)
