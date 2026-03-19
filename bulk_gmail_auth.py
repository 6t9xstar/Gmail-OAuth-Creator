"""
Bulk Gmail API Credential Generator
Processes multiple Gmail accounts and generates JSON credential files.
"""
import os
import json
import csv
import pickle
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Gmail API Scopes - Modify based on your needs
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

class BulkGmailCredentialGenerator:
    def __init__(self, client_secrets_file, accounts_csv, output_dir='credentials'):
        self.client_secrets_file = client_secrets_file
        self.accounts_csv = accounts_csv
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.accounts = []
        
    def load_accounts(self):
        """Load accounts from CSV file"""
        with open(self.accounts_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.accounts = list(reader)
        print(f"Loaded {len(self.accounts)} accounts from {self.accounts_csv}")
        return self.accounts
    
    def authenticate_account(self, email, account_id):
        """Authenticate a single Gmail account"""
        creds = None
        token_file = self.output_dir / f"{account_id}_token.pickle"
        
        # Load existing token if available
        if token_file.exists():
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print(f"\n{'='*50}")
                print(f"Authenticating: {email}")
                print(f"{'='*50}")
                print("A browser window will open. Please login and authorize.")
                print("After authorization, you can close the browser.")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save token
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        return creds
    
    def save_credentials_json(self, creds, email, account_id):
        """Save credentials as JSON file"""
        # Extract token info
        creds_info = {
            'account_email': email,
            'account_id': account_id,
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        
        json_file = self.output_dir / f"{account_id}_credentials.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(creds_info, f, indent=2)
        
        return json_file
    
    def verify_credentials(self, creds):
        """Verify that credentials work by making a test API call"""
        try:
            service = build('gmail', 'v1', credentials=creds)
            profile = service.users().getProfile(userId='me').execute()
            return profile.get('emailAddress')
        except Exception as e:
            print(f"Verification failed: {e}")
            return None
    
    def process_all_accounts(self):
        """Process all accounts in the CSV"""
        self.load_accounts()
        
        results = []
        for idx, account in enumerate(self.accounts, 1):
            email = account.get('email', '').strip()
            account_id = account.get('account_id', '').strip()
            
            # Generate account_id from email if not provided
            if not account_id and email:
                account_id = email.replace('@', '_').replace('.', '_')
            elif not account_id:
                account_id = f"account_{idx:03d}"
            
            if not email:
                print(f"Skipping row {idx}: No email provided")
                continue
            
            try:
                print(f"\n[{idx}/{len(self.accounts)}] Processing {email}...")
                
                # Authenticate
                creds = self.authenticate_account(email, account_id)
                
                # Verify
                verified_email = self.verify_credentials(creds)
                
                # Save as JSON
                json_file = self.save_credentials_json(creds, email, account_id)
                
                result = {
                    'account_id': account_id,
                    'email': email,
                    'status': 'success',
                    'verified_email': verified_email,
                    'credentials_file': str(json_file)
                }
                print(f"✓ Success: {email} -> {json_file.name}")
                
            except Exception as e:
                result = {
                    'account_id': account_id,
                    'email': email,
                    'status': 'failed',
                    'error': str(e)
                }
                print(f"✗ Failed: {email} - {e}")
            
            results.append(result)
        
        # Save summary
        self.save_summary(results)
        return results
    
    def save_summary(self, results):
        """Save processing summary"""
        summary_file = self.output_dir / '_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        success = sum(1 for r in results if r['status'] == 'success')
        failed = sum(1 for r in results if r['status'] == 'failed')
        
        print(f"\n{'='*50}")
        print("PROCESSING COMPLETE")
        print(f"{'='*50}")
        print(f"Total accounts: {len(results)}")
        print(f"Successful: {success}")
        print(f"Failed: {failed}")
        print(f"Output directory: {self.output_dir.absolute()}")
        print(f"Summary saved to: {summary_file}")
        
        return results


def main():
    """Main entry point"""
    import sys
    
    # Check for required files
    client_secrets = 'client_secrets.json'
    accounts_csv = 'accounts.csv'
    
    if not os.path.exists(client_secrets):
        print(f"ERROR: {client_secrets} not found!")
        print("Please download your OAuth 2.0 credentials from Google Cloud Console")
        print("and save them as 'client_secrets.json' in this directory.")
        sys.exit(1)
    
    if not os.path.exists(accounts_csv):
        print(f"ERROR: {accounts_csv} not found!")
        print("Please create an accounts.csv file with your Gmail accounts.")
        print("Format: email,account_id")
        sys.exit(1)
    
    # Run generator
    generator = BulkGmailCredentialGenerator(client_secrets, accounts_csv)
    generator.process_all_accounts()


if __name__ == '__main__':
    main()
