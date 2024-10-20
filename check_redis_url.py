import os

redis_url_present = 'REDIS_URL' in os.environ
print(f"REDIS_URL present: {redis_url_present}")

if redis_url_present:
    print("REDIS_URL is set in the environment.")
else:
    print("REDIS_URL is not set in the environment.")
