from flask import Blueprint, request, jsonify, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User
from datetime import datetime, timedelta
from flask_dance.contrib.google import make_google_blueprint, google
from flask_wtf.csrf import CSRFProtect
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

auth = Blueprint('auth', __name__)
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

def create_google_blueprint(app):
    return make_google_blueprint(
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        scope=['profile', 'email']
    )

@auth.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and user.check_password(data['password']):
        if not user.consent_given or not user.data_usage_accepted:
            return jsonify({'message': 'Please accept the terms and conditions'}), 403
        login_user(user)
        user.last_login = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Logged in successfully'}), 200
    return jsonify({'message': 'Invalid email or password'}), 401

@auth.route('/register', methods=['POST'])
@limiter.limit("3 per hour")
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400
    
    if not data.get('consent_given') or not data.get('data_usage_accepted'):
        return jsonify({'message': 'Please accept the terms and conditions'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        consent_given=data['consent_given'],
        data_usage_accepted=data['data_usage_accepted']
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

@auth.route('/login/google')
def login_google():
    if not google.authorized:
        return redirect(url_for('google.login'))
    resp = google.get('/oauth2/v2/userinfo')
    if not resp.ok:
        return jsonify({'message': 'Failed to get user info from Google'}), 400
    
    google_info = resp.json()
    email = google_info['email']
    
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            username=google_info['name'],
            email=email,
            oauth_provider='google',
            oauth_id=google_info['id'],
            consent_given=True,
            data_usage_accepted=True
        )
        db.session.add(user)
        db.session.commit()
    
    login_user(user)
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Logged in successfully via Google'}), 200

@auth.route('/gdpr/consent', methods=['POST'])
@login_required
def update_gdpr_consent():
    data = request.get_json()
    current_user.consent_given = data.get('consent_given', current_user.consent_given)
    current_user.data_usage_accepted = data.get('data_usage_accepted', current_user.data_usage_accepted)
    db.session.commit()
    return jsonify({'message': 'GDPR consent updated successfully'}), 200

@auth.route('/gdpr/data', methods=['GET'])
@login_required
def get_user_data():
    user_data = {
        'username': current_user.username,
        'email': current_user.email,
        'created_at': current_user.created_at,
        'last_login': current_user.last_login,
        'consent_given': current_user.consent_given,
        'data_usage_accepted': current_user.data_usage_accepted,
        'oauth_provider': current_user.oauth_provider
    }
    return jsonify(user_data), 200

@auth.route('/gdpr/delete', methods=['DELETE'])
@login_required
def delete_user_data():
    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    return jsonify({'message': 'User data deleted successfully'}), 200

def init_auth(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    csrf.init_app(app)
    limiter.init_app(app)

    google_blueprint = create_google_blueprint(app)
    app.register_blueprint(google_blueprint, url_prefix="/login")

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(auth)

    # Set session lifetime
    @app.before_request
    def make_session_permanent():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(days=30)  # Set session expiry to 30 days

    return app
