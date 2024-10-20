import os
from flask import Flask, jsonify, send_from_directory
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
from werkzeug.middleware.profiler import ProfilerMiddleware
from flask_caching import Cache
from flask_compress import Compress
from celery_worker import init_celery

migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)
cache = Cache()
compress = Compress()

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
    cache.init_app(app)
    compress.init_app(app)

    # Initialize Redis and rate limiter
    init_rate_limiter(app)
    limiter.init_app(app)

    # Initialize API
    api = Api(app)

    # Initialize Talisman for security headers
    Talisman(app, content_security_policy=app.config['CONTENT_SECURITY_POLICY'])

    # Enable profiling in debug mode
    if app.debug:
        app.config['PROFILE'] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

    # Initialize Celery
    celery = init_celery(app)

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
    with app.app_context():
        from api import users, courses, skills
        api.add_resource(users.UserListResource, '/api/users')
        api.add_resource(users.UserResource, '/api/users/<int:user_id>')
        api.add_resource(users.UserCoursesResource, '/api/users/<int:user_id>/courses')
        api.add_resource(users.UserSkillsResource, '/api/users/<int:user_id>/skills')
        api.add_resource(users.UsersWithCourseCountResource, '/api/users/course_count')
        api.add_resource(courses.CourseListResource, '/api/courses')
        api.add_resource(courses.CourseResource, '/api/courses/<int:course_id>')
        api.add_resource(skills.SkillListResource, '/api/skills')
        api.add_resource(skills.SkillResource, '/api/skills/<int:skill_id>')

    # Initialize auth
    from auth import init_auth
    init_auth(app)

    @app.after_request
    def add_header(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    # Add a simple health check endpoint
    @app.route('/health')
    @cache.cached(timeout=60)  # Cache for 1 minute
    def health_check():
        return jsonify({"status": "healthy"}), 200

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
