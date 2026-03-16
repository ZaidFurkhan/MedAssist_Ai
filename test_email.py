"""Quick test to verify Gmail SMTP works with current .env credentials."""
from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

mail = Mail(app)

print(f"Using Gmail account: {os.environ.get('MAIL_USERNAME')}")

with app.app_context():
    try:
        msg = Message(
            subject="Smart CDSS - Test Email",
            recipients=[os.environ.get('MAIL_USERNAME')]  # send to self
        )
        msg.body = "Test email from Smart CDSS Flask-Mail. If you see this, email is working!"
        mail.send(msg)
        print("✅ SUCCESS! Email sent. Check your Gmail inbox.")
    except Exception as e:
        print(f"❌ FAILED: {e}")
