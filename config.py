import os

class Config:
    # Flask
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'a_secret_key'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_STRATEGY = 'fixed-window'
    
    # Ensure all Redis-related configs use the same URL
    CACHE_REDIS_URL = REDIS_URL
    CACHE_TYPE = "redis"
