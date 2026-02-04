try:
    print("Checking imports...")
    import google.auth
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    print("Imports success.")
except ImportError as e:
    print(f"ImportError: {e}")

import os
if os.path.exists("credentials.json"):
    print("credentials.json found.")
else:
    print("credentials.json MISSING.")
