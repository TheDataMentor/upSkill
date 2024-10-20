import time
from flask import request, jsonify, make_response
from functools import wraps
from collections import defaultdict
import threading
import logging

class RateLimiter:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.in_memory_storage = defaultdict(list)
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

    def limit(self, key_prefix, limit, period):
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                key = f"{key_prefix}:{request.remote_addr}"
                current = int(time.time())
                window_start = current - period

                try:
                    if self.redis_client:
                        # Use Redis for rate limiting
                        self.logger.info(f"Using Redis for rate limiting: {key}")
                        request_count, remaining, reset = self._redis_rate_limit(key, limit, period, current, window_start)
                    else:
                        # Use in-memory storage for rate limiting
                        self.logger.info(f"Using in-memory storage for rate limiting: {key}")
                        request_count, remaining, reset = self._memory_rate_limit(key, limit, period, current, window_start)

                    if request_count < limit:
                        response = f(*args, **kwargs)
                    else:
                        response = jsonify({"error": "Rate limit exceeded"}), 429

                    response = make_response(response)
                    response.headers["X-RateLimit-Limit"] = str(limit)
                    response.headers["X-RateLimit-Remaining"] = str(remaining)
                    response.headers["X-RateLimit-Reset"] = str(reset)

                    return response

                except Exception as e:
                    self.logger.error(f"Error in rate limiting: {str(e)}")
                    return jsonify({"error": "Internal server error"}), 500

            return wrapped
        return decorator

    def _redis_rate_limit(self, key, limit, period, current, window_start):
        pipe = self.redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(current): current})
        pipe.expire(key, period)
        results = pipe.execute()
        request_count = results[1]
        remaining = max(limit - request_count, 0)
        reset = window_start + period
        return request_count, remaining, reset

    def _memory_rate_limit(self, key, limit, period, current, window_start):
        with self.lock:
            self.in_memory_storage[key] = [t for t in self.in_memory_storage[key] if t > window_start]
            request_count = len(self.in_memory_storage[key])
            if request_count < limit:
                self.in_memory_storage[key].append(current)
            remaining = max(limit - request_count, 0)
            reset = window_start + period
        return request_count, remaining, reset

    def switch_to_redis(self, redis_client):
        self.logger.info("Switching to Redis for rate limiting")
        self.redis_client = redis_client

    def switch_to_memory(self):
        self.logger.warning("Switching to in-memory storage for rate limiting")
        self.redis_client = None
