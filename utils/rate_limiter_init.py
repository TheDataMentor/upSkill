from utils.rate_limiter import RateLimiter
from flask_redis import FlaskRedis

redis_client = FlaskRedis()
rate_limiter = RateLimiter(redis_client)

def init_rate_limiter(app):
    global redis_client, rate_limiter
    redis_client.init_app(app)
    app.rate_limiter = rate_limiter
