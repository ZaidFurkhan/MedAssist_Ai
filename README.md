# MedAssist.AI (Smart Healthcare With AI)

---

## 🎯 Project Overview

**MedAssist** is an intelligent, AI‑powered clinical decision support system that helps users predict diseases based on symptoms, locate nearby specialised hospitals, and manage appointments. It combines:
- A Flask backend with a PostgreSQL (Neon) database.
- Groq LLM integration for chatbot and disease‑information generation.
- Geoapify for geo‑based hospital search.
- Secure email notifications via Brevo (Sendinblue).

The platform is built for both **desktop** and **mobile‑first** experiences, offering a premium UI with glass‑morphism, smooth micro‑animations, and dark‑mode support.

---

## ✨ Key Features

- **🧠 ML-Driven Prediction**: Uses a calibrated Random Forest model to predict diseases with probability scores.
- **💬 AI Health Chatbot**: Powered by Groq Llama-3.1 for empathetic, context-aware health guidance.
- **🏥 Specialty-Aware Hospital Routing**: Maps predicted diseases to medical specialties and finds the nearest matching hospitals using Geoapify.
- **📅 Smart Appointments**: Book slots directly and receive automated email reminders (12h and 1h before) via Brevo.
- **📋 Disease Insights**: Get detailed summaries, precautions, and dietary advice generated in real-time by AI.
- **🎙️ Voice Integration**: Built-in Speech-to-Text for chat input and Text-to-Speech for disease information.
- **🔐 Secure Authentication**: Email-based registration with OTP verification.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Web Framework** | Flask (Python) |
| **Database** | PostgreSQL (Neon) |
| **ORM** | SQLAlchemy |
| **Background Jobs** | Flask‑APScheduler |
| **AI / LLM** | Groq (Llama‑3.1‑8B‑Instant) |
| **Email Service** | Brevo (Sendinblue) |
| **Geolocation** | Geoapify Places API |
| **Frontend** | html, css, vanilla JavaScript|

---

## 📦 Getting Started

### Prerequisites
- **Python 3.11+**
- **Git**
- **Neon PostgreSQL** account (or any PostgreSQL instance)
- API keys for:
  - **GROQ_API_KEY**
  - **BREVO_API_KEY**
  - **GEOAPIFY_API_KEY**

### Clone the Repository
```bash
git clone https://github.com/ZaidFurkhan/Smart-CDSS.git
cd Smart-CDSS
```

### Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file at the repository root (copy from `.env.example`):
```dotenv
# Flask secret
SECRET_KEY=your_random_secret_key

# Database URL (Neon example)
DATABASE_URL=postgresql://username:password@db-host:5432/smartcdss

# Groq LLM
GROQ_API_KEY=your_groq_key

# Brevo (Sendinblue) email service
BREVO_API_KEY=your_brevo_key
BREVO_SENDER_EMAIL=your_verified_sender@example.com

# Geoapify for hospital lookup
GEOAPIFY_API_KEY=your_geoapify_key
```

### Initialise the Database
```bash
# First run creates tables automatically (see app.py). You may also run manually:
python - <<EOF
from app import db
db.create_all()
EOF
```

### Run the Development Server
```bash
flask run --reload
# or
python app.py
```
Open http://127.0.0.1:5000 in your browser.

---

## 🚀 Deployment (Vercel)

The project is configured for easy deployment on **Vercel**. Follow these steps:

### 1. Configure Vercel
1.  Connect your GitHub repository to Vercel.
2.  Vercel will automatically detect the Python environment.
3.  Add the following **Environment Variables** in the Vercel Dashboard:
    - `SECRET_KEY`: A random string for session security.
    - `DATABASE_URL`: Your Neon PostgreSQL connection string.
    - `GROQ_API_KEY`: Your Groq API key.
    - `BREVO_API_KEY`: Your Brevo API key.
    - `BREVO_SENDER_EMAIL`: Your verified sender email.
    - `GEOAPIFY_API_KEY`: Your Geoapify API key.
    - `CRON_SECRET`: (Optional) A secret string to secure your reminder endpoint. If set, Vercel Crons will automatically use it.

### 2. Reminders & Background Jobs
> [!IMPORTANT]
> Since Vercel uses serverless functions, the built-in `Flask-APScheduler` will not run persistently in the background. To enable automated reminders on Vercel:
> 1. Go to your project settings in Vercel.
> 2. Set up a **Vercel Cron Job** (available in `vercel.json`).
> 3. Point the cron job to `/api/test/check_reminders` to run every 10 minutes.

### 3. Deploy
Push your changes to GitHub, and Vercel will build and deploy the application using the provided `vercel.json`.

---

## 🚀 Usage Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/register` | POST | Register a new user (sends OTP via Brevo) |
| `/api/verify` | POST | Verify email with OTP code |
| `/api/login` | POST | Authenticate user & create session |
| `/api/symptoms` | GET | Fetch all available symptoms for the UI |
| `/api/predict` | POST | Analyze symptoms → Disease prediction (Top 3) |
| `/api/disease-info`| GET | Generate AI summary (Severity, Diet, Precautions) |
| `/api/hospitals` | GET | Geolocation-based hospital search (Specialty-aware) |
| `/api/book_appointment`| POST | Book slot & send email confirmation |
| `/api/user/data` | GET | Retrieve user’s prediction & appointment history |
| `/api/chat` | POST | Interactive health chatbot (Groq Llama-3.1) |
| `/api/logout` | POST | Terminate user session |

All endpoints return JSON and use standard HTTP status codes.

---

## 🎨 UI/UX Design Principles
- **Premium look**: glass‑morphism cards, vibrant gradients, and subtle hover animations.
- **Responsive & mobile‑first**: layout collapses gracefully, navigation header hides global UI when the chatbot is active.
- **Dark mode**: automatically follows system preference; CSS variables control colour palette.
- **Accessibility**: proper ARIA labels, focus management, and colour contrast.

---

## 🔄 System Workflow

1.  **Auth**: User registers with email; receives a 6-digit OTP via **Brevo API**.
2.  **Input**: User selects symptoms from a searchable grid and provides demographics.
3.  **Analysis**: **Random Forest** model predicts the condition with confidence scores.
4.  **Insights**: **Groq LLM** generates real-time advice (Precautions, Diet, Severity).
5.  **Discovery**: **Geoapify** finds nearby hospitals matching the predicted specialty.
6.  **Booking**: User schedules an appointment; stored in **PostgreSQL**.
7.  **Reminders**: **Flask-APScheduler** triggers automated email reminders 12h and 1h before.

---

## 📂 Project Structure

```text
Smart-CDSS/
├── app.py              # Main Flask application & API routes
├── ml/                 # Machine Learning logic & prediction scripts
│   └── predict.py      # Disease prediction engine
├── model/              # Serialized ML models (.pkl)
├── static/             # CSS, JS, and image assets
├── templates/          # Jinja2 HTML templates
├── dataset/            # Training data for the ML model
├── diagrams/           # System architecture and workflow diagrams
├── generate_report.py  # Script to generate professional project reports
└── requirements.txt    # Project dependencies
```

---

## 🤖 ML Methodology

The prediction engine utilizes a **Random Forest Classifier** trained on a medical symptoms dataset.
- **Optimization**: GridSearchCV for hyperparameter tuning.
- **Calibration**: `CalibratedClassifierCV` ensures prediction probabilities are realistic.
- **Fuzzy Matching**: Handles user input variations using fuzzy string matching for symptoms.

---

## 📊 Database Schema

The system uses **PostgreSQL (Neon DB)** with the following core entities:
- **User**: Authentication and verification status.
- **PredictionRecord**: History of symptom analysis and results.
- **Appointment**: Booking details with automated reminder tracking.

---

*Happy coding! 🎉*
