
import os
from flask import Flask, jsonify, render_template, request, make_response, send_from_directory, session
from flask_restful import Api
from flask_migrate import Migrate
from redis.exceptions import ConnectionError as RedisConnectionError
import logging
import threading
import time
from datetime import timedelta
from extensions import db
from utils.rate_limiter_init import init_rate_limiter, redis_client
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)

def create_app():
    app = Flask(__name__, static_folder='frontend/build')

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = app.logger

    # Load configuration
    app.config.from_object('config.Config')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Initialize Redis and rate limiter
    init_rate_limiter(app)
    limiter.init_app(app)

    # Initialize API
    api = Api(app)

    # Initialize Talisman for security headers
    Talisman(app, content_security_policy=app.config['CONTENT_SECURITY_POLICY'])

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
        return jsonify({"error": "Service temporarily unavailable"}), 503

    @app.errorhandler(500)
    def handle_internal_server_error(error):
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({"error": "Internal server error"}), 500

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

    # Initialize auth
    from auth import init_auth
    init_auth(app)

    return app

app = create_app()

def check_redis_connection():
    while True:
        try:
            redis_client.ping()
            app.logger.info("Redis connection successful")
        except RedisConnectionError as e:
            app.logger.warning(f"Redis connection failed: {str(e)}. Switching to in-memory storage.")
            app.rate_limiter.switch_to_memory()
        time.sleep(60)  # Check every 60 seconds

if __name__ == '__main__':
    # Start Redis connection check thread
    redis_check_thread = threading.Thread(target=check_redis_connection, daemon=True)
    redis_check_thread.start()

    app.run(host='0.0.0.0', port=8080)
