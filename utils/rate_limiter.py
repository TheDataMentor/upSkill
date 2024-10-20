import time
from flask import request, jsonify, make_response
from functools import wraps
from collections import defaultdict
import threading

class RateLimiter:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.in_memory_storage = defaultdict(list)
        self.lock = threading.Lock()

    def limit(self, key_prefix, limit, period):
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                key = f"{key_prefix}:{request.remote_addr}"
                current = int(time.time())
                window_start = current - period

                if self.redis_client:
                    # Use Redis for rate limiting
                    self.redis_client.zremrangebyscore(key, 0, window_start)
                    request_count = self.redis_client.zcard(key)

                    if request_count < limit:
                        self.redis_client.zadd(key, {str(current): current})
                        self.redis_client.expire(key, period)
                        response = f(*args, **kwargs)
                    else:
                        response = jsonify({"error": "Rate limit exceeded"}), 429

                    remaining = max(limit - request_count, 0)
                    reset = window_start + period
                else:
                    # Use in-memory storage for rate limiting
                    with self.lock:
                        self.in_memory_storage[key] = [t for t in self.in_memory_storage[key] if t > window_start]
                        request_count = len(self.in_memory_storage[key])

                        if request_count < limit:
                            self.in_memory_storage[key].append(current)
                            response = f(*args, **kwargs)
                        else:
                            response = jsonify({"error": "Rate limit exceeded"}), 429

                    remaining = max(limit - request_count, 0)
                    reset = window_start + period

                response = make_response(response)
                response.headers["X-RateLimit-Limit"] = str(limit)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Reset"] = str(reset)

                return response
            return wrapped
        return decorator
