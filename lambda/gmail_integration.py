import json
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def send_gmail(email_content, user_credentials):
    """Send email via Gmail API"""
    try:
        # Parse email content
        lines = email_content.split('\n')
        subject = lines[0].replace('Subject: ', '') if lines[0].startswith('Subject:') else 'Email from DocumentGPT'
        body = '\n'.join(lines[2:]) if len(lines) > 2 else email_content
        
        # Create credentials
        creds = Credentials(
            token=user_credentials['access_token'],
            refresh_token=user_credentials.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=user_credentials['client_id'],
            client_secret=user_credentials['client_secret']
        )
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=creds)
        
        # Create message
        message = {
            'raw': base64.urlsafe_b64encode(
                f"To: {user_credentials.get('to_email', 'user@example.com')}\n"
                f"Subject: {subject}\n\n{body}".encode()
            ).decode()
        }
        
        # Send email
        result = service.users().messages().send(userId='me', body=message).execute()
        return {'success': True, 'message_id': result['id']}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def create_google_sheet(data_content, user_credentials, sheet_name="DocumentGPT Export"):
    """Create Google Sheet with extracted data"""
    try:
        from googleapiclient.discovery import build
        
        creds = Credentials(
            token=user_credentials['access_token'],
            refresh_token=user_credentials.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=user_credentials['client_id'],
            client_secret=user_credentials['client_secret']
        )
        
        service = build('sheets', 'v4', credentials=creds)
        
        # Create spreadsheet
        spreadsheet = {
            'properties': {'title': sheet_name}
        }
        
        result = service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = result['spreadsheetId']
        
        # Parse CSV data and add to sheet
        rows = []
        for line in data_content.split('\n'):
            if ',' in line:
                rows.append(line.split(','))
        
        if rows:
            body = {'values': rows}
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='A1',
                valueInputOption='RAW',
                body=body
            ).execute()
        
        return {
            'success': True, 
            'spreadsheet_id': spreadsheet_id,
            'url': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}