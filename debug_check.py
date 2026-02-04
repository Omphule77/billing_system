import sys
import os

print("Checking imports...")
try:
    print("Importing app.utils...")
    from app.utils import generate_pdf
    print("Success app.utils")

    print("Importing app.whatsapp_utils...")
    from app.whatsapp_utils import send_whatsapp_file
    print("Success app.whatsapp_utils")
    
    print("Importing app.routes...")
    from app import routes
    print("Success app.routes")

except Exception as e:
    print(f"\nCRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
