from functools import wraps
from flask import jsonify
from app import redis_client

def cache_response(timeout=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f.__name__ + str(args) + str(kwargs)
            cached_response = redis_client.get(cache_key)
            if cached_response:
                return jsonify(eval(cached_response))
            
            response = f(*args, **kwargs)
            redis_client.setex(cache_key, timeout, str(response))
            return response
        return decorated_function
    return decorator
