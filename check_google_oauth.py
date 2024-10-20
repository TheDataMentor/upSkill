import os

google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
google_client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')

if google_client_id and google_client_secret:
    print("Google OAuth credentials are available in the environment.")
else:
    print("Google OAuth credentials are missing from the environment.")
