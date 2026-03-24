from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Check if test user exists
    test_user = User.query.filter_by(email='test@example.com').first()
    if test_user:
        db.session.delete(test_user)
        db.session.commit()
    
    # Create test user
    new_user = User(email='test@example.com', is_verified=True)
    new_user.set_password('password123')
    db.session.add(new_user)
    db.session.commit()
    print("Test user 'test@example.com' with password 'password123' created and verified.")
