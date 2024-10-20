import os
from flask import Flask, jsonify, render_template, request, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_redis import FlaskRedis
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase
from redis.exceptions import ConnectionError as RedisConnectionError
from utils.rate_limiter import RateLimiter
import logging

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
redis_client = FlaskRedis()
migrate = Migrate()

# Create the Flask app
app = Flask(__name__)

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
from api.users import UserResource, UserListResource
from api.courses import CourseResource, CourseListResource
from api.skills import SkillResource, SkillListResource

api.add_resource(UserListResource, '/api/users')
api.add_resource(UserResource, '/api/users/<int:user_id>')
api.add_resource(CourseListResource, '/api/courses')
api.add_resource(CourseResource, '/api/courses/<int:course_id>')
api.add_resource(SkillListResource, '/api/skills')
api.add_resource(SkillResource, '/api/skills/<int:skill_id>')

@app.route('/')
@rate_limiter.limit("home", limit=100, period=60)
def index():
    return render_template('index.html')

@app.errorhandler(RedisConnectionError)
def handle_redis_connection_error(error):
    logger.error(f"Redis connection error: {str(error)}")
    return jsonify({"error": "Service temporarily using in-memory rate limiting due to Redis connection issues"}), 503

@app.errorhandler(500)
def handle_internal_server_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
