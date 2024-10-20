from functools import wraps
from flask import jsonify, request
from app import redis_client
import json

def cache_response(timeout=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate a unique cache key based on the function name, arguments, and request data
            cache_key = f"{f.__name__}:{request.path}:{json.dumps(request.args)}:{request.data.decode('utf-8')}"
            
            # Check if the response is in the cache
            cached_response = redis_client.get(cache_key)
            if cached_response:
                return json.loads(cached_response)
            
            # If not in cache, call the original function
            response = f(*args, **kwargs)
            
            # Cache the response
            redis_client.setex(cache_key, timeout, json.dumps(response))
            
            return response
        return decorated_function
    return decorator

def invalidate_cache(pattern):
    """
    Invalidate cache entries matching the given pattern
    """
    for key in redis_client.scan_iter(pattern):
        redis_client.delete(key)

def get_cache_key(resource_type, resource_id=None):
    """
    Generate a cache key pattern for a specific resource or resource type
    """
    if resource_id:
        return f"{resource_type}:{resource_id}:*"
    return f"{resource_type}:*"
