import os
from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_redis import FlaskRedis
from sqlalchemy.orm import DeclarativeBase
from redis.exceptions import ConnectionError as RedisConnectionError

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
redis_client = FlaskRedis()

# Create the Flask app
app = Flask(__name__)

# Load configuration
app.config.from_object('config.Config')

# Initialize extensions
db.init_app(app)

# Initialize Redis with error handling
try:
    redis_client.init_app(app)
    redis_client.ping()  # Test the connection
    app.logger.info("Redis connection successful")
except RedisConnectionError as e:
    app.logger.error(f"Redis connection failed: {str(e)}")
    redis_client = None

# Initialize API
api = Api(app)

# Initialize rate limiter with fallback strategy
def limiter_key_func():
    try:
        return get_remote_address()
    except:
        return None

limiter = Limiter(
    key_func=limiter_key_func,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=app.config['REDIS_URL'] if redis_client else "memory://",
    strategy="moving-window"
)

# Import and register API resources
from api.users import UserResource, UserListResource
from api.courses import CourseResource, CourseListResource
from api.skills import SkillResource, SkillListResource

api.add_resource(UserListResource, '/api/users')
api.add_resource(UserResource, '/api/users/<int:user_id>')
api.add_resource(CourseListResource, '/api/courses')
api.add_resource(CourseResource, '/api/courses/<int:course_id>')
api.add_resource(SkillListResource, '/api/skills')
api.add_resource(SkillResource, '/api/skills/<int:skill_id>')

# Create database tables
with app.app_context():
    import models
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.errorhandler(RedisConnectionError)
def handle_redis_connection_error(error):
    app.logger.error(f"Redis connection error: {str(error)}")
    return jsonify({"error": "Service temporarily unavailable due to Redis connection issues"}), 503

@app.errorhandler(500)
def handle_internal_server_error(error):
    app.logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
