from app.drive_utils import get_drive_service

print("Starting Drive Auth Test...")
try:
    service = get_drive_service()
    print("Service created successfully!")
    
    # Try to list files to prove it works
    results = service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    print(f"Found {len(items)} files.")
    
except Exception as e:
    print(f"Auth Failed: {e}")
