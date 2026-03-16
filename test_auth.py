import requests
import json
import uuid

BASE_URL = "http://localhost:5000/api"
EMAIL = f"test_{uuid.uuid4().hex[:6]}@example.com"
PASSWORD = "testpassword123"

def test_auth_flow():
    print(f"Testing with email: {EMAIL}")
    
    # 1. Register
    print("\n1. Registering user...")
    resp = requests.post(f"{BASE_URL}/register", json={"email": EMAIL, "password": PASSWORD})
    print(resp.json())
    if resp.status_code != 201:
        print("Registration failed!")
        return

    # Extract demo code if mail failed (likely in local env)
    data = resp.json()
    code = data.get('demo_code')
    if not code:
        print("Verification code not found in response (check server logs or email if SMTP configured)")
        return

    # 2. Verify
    print("\n2. Verifying user...")
    resp = requests.post(f"{BASE_URL}/verify", json={"email": EMAIL, "code": code})
    print(resp.json())
    if resp.status_code != 200:
        print("Verification failed!")
        return

    # 3. Login
    print("\n3. Logging in...")
    session = requests.Session() # Use session to keep cookies
    resp = session.post(f"{BASE_URL}/login", json={"email": EMAIL, "password": PASSWORD})
    print(resp.json())
    if resp.status_code != 200:
        print("Login failed!")
        return

    # 4. Predict (linked to user)
    print("\n4. Performing prediction...")
    resp = session.post(f"{BASE_URL}/predict", json={
        "symptoms": ["itching", "skin_rash", "nodal_skin_eruptions"],
        "age": "Adult",
        "gender": "Male"
    })
    print(resp.json())
    if resp.status_code != 200:
        print("Prediction failed!")
        return

    # 5. Book Appointment (linked to user)
    print("\n5. Booking appointment...")
    resp = session.post(f"{BASE_URL}/book_appointment", json={
        "hospital_name": "Test Hospital",
        "doctor_name": "Dr. Test",
        "appointment_date": "2026-03-20",
        "appointment_time": "10:00 AM",
        "patient_name": "Test Patient",
        "patient_phone": "1234567890"
    })
    print(resp.json())
    if resp.status_code != 201:
        print("Booking failed!")
        return

    # 6. Check User Data
    print("\n6. Retrieving user history...")
    resp = session.get(f"{BASE_URL}/user/data")
    user_data = resp.json()
    print(json.dumps(user_data, indent=2))
    
    if len(user_data.get('predictions', [])) > 0 and len(user_data.get('appointments', [])) > 0:
        print("\nSUCCESS: User history correctly retrieved!")
    else:
        print("\nFAILURE: User history missing records!")

if __name__ == "__main__":
    try:
        test_auth_flow()
    except Exception as e:
        print(f"Error during test: {e}")
