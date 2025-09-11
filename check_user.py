from app import app, db, User
from werkzeug.security import check_password_hash

with app.app_context():
    u = User.query.filter_by(username='EMP001').first()
    print(f'User found: {u is not None}')
    if u:
        print(f'Password check for "password123": {check_password_hash(u.password_hash, "password123")}')
        # Try to reset password for testing
        u.set_password('test123')
        db.session.commit()
        print('Password reset to "test123" for testing')
