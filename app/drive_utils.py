import os
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    """Shows basic usage of the Drive v3 API.
    Returns the service object.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token_path = os.path.join(os.getcwd(), 'token.json')
    credentials_path = os.path.join(os.getcwd(), 'credentials.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"credentials.json not found at {credentials_path}")
                
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)
    return service

def upload_to_drive(file_path, file_name=None):
    """Uploads a file to Google Drive and returns the webViewLink."""
    try:
        service = get_drive_service()
        
        if not file_name:
            file_name = os.path.basename(file_path)

        file_metadata = {'name': file_name}
        media = MediaFileUpload(file_path, resumable=True)
        
        print(f"Uploading {file_name} to Google Drive...")
        file = service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id, webViewLink').execute()
        
        file_id = file.get('id')
        print(f"File ID: {file_id}")
        
        # Make the file public (anyone with link can view)
        # For WhatsApp, this is usually strictly necessary if the receiver doesn't have specific access
        # Permission: type=anyone, role=reader
        # Note: If confidentiality is key, we might want to rethink this, but for "sending link", this is standard.
        permission = {
            'type': 'anyone',
            'role': 'reader',
        }
        service.permissions().create(fileId=file_id, body=permission).execute()
        
        # Retrieve the link again just to be sure (though create returned it)
        # webViewLink is the viewable link.
        link = file.get('webViewLink')
        print(f"Upload successful. Link: {link}")
        return link

    except Exception as e:
        print(f"An error occurred during Drive Upload: {e}")
        raise e
