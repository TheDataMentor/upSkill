import os
from flask import Flask, jsonify, render_template, request, make_response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_redis import FlaskRedis
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase
from redis.exceptions import ConnectionError as RedisConnectionError
from utils.rate_limiter import RateLimiter
import logging
import threading
import time

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
redis_client = FlaskRedis()
migrate = Migrate()

# Create the Flask app
app = Flask(__name__, static_folder='frontend/build')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = app.logger

# Load configuration
app.config.from_object('config.Config')

# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)

# Initialize Redis with error handling
try:
    redis_client.init_app(app)
    redis_client.ping()
    logger.info(f"Redis connection successful: {app.config['REDIS_URL']}")
except RedisConnectionError as e:
    logger.warning(f"Redis connection failed: {str(e)}. Falling back to in-memory storage.")
    redis_client = None

# Initialize API
api = Api(app)

# Initialize rate limiter
rate_limiter = RateLimiter(redis_client)

# Import and register API resources
from api.users import UserResource, UserListResource, UserCoursesResource, UserSkillsResource
from api.courses import CourseResource, CourseListResource
from api.skills import SkillResource, SkillListResource

api.add_resource(UserListResource, '/api/users')
api.add_resource(UserResource, '/api/users/<int:user_id>')
api.add_resource(UserCoursesResource, '/api/users/<int:user_id>/courses')
api.add_resource(UserSkillsResource, '/api/users/<int:user_id>/skills')
api.add_resource(CourseListResource, '/api/courses')
api.add_resource(CourseResource, '/api/courses/<int:course_id>')
api.add_resource(SkillListResource, '/api/skills')
api.add_resource(SkillResource, '/api/skills/<int:skill_id>')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(RedisConnectionError)
def handle_redis_connection_error(error):
    logger.error(f"Redis connection error: {str(error)}")
    return jsonify({"error": "Service temporarily using in-memory rate limiting due to Redis connection issues"}), 503

@app.errorhandler(500)
def handle_internal_server_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

def check_redis_connection():
    global redis_client
    while True:
        try:
            if redis_client is None:
                redis_client = FlaskRedis()
                redis_client.init_app(app)
            redis_client.ping()
            if rate_limiter.redis_client is None:
                rate_limiter.switch_to_redis(redis_client)
            logger.info("Redis connection successful")
        except RedisConnectionError as e:
            logger.warning(f"Redis connection failed: {str(e)}. Switching to in-memory storage.")
            redis_client = None
            rate_limiter.switch_to_memory()
        time.sleep(60)  # Check every 60 seconds

if __name__ == '__main__':
    # Start Redis connection check thread
    redis_check_thread = threading.Thread(target=check_redis_connection, daemon=True)
    redis_check_thread.start()

    app.run(host='0.0.0.0', port=5000)
