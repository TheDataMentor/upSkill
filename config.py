import os
from datetime import timedelta

class Config:
    # Flask
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'a_secret_key'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "max_overflow": 15,
    }
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL')
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_STRATEGY = 'fixed-window'
    
    # Ensure all Redis-related configs use the same URL
    CACHE_REDIS_URL = REDIS_URL
    CACHE_TYPE = "redis"
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    # GDPR Compliance
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('CSRF_SECRET_KEY') or 'csrf_secret_key'

    # Password Hashing
    BCRYPT_LOG_ROUNDS = 12  # Increase the number of rounds for bcrypt

    # Content Security Policy
    CONTENT_SECURITY_POLICY = {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline' 'unsafe-eval'",
        'style-src': "'self' 'unsafe-inline'",
        'img-src': "'self' data:",
        'font-src': "'self'",
        'frame-src': "'self'",
        'connect-src': "'self'"
    }
