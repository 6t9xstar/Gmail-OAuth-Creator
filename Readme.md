# Fastest Gmail API Setup - Instructions

## Overview
This tool automates Gmail API credential generation for multiple accounts.

## Prerequisites
1. Python 3.7+ installed
2. Google Cloud Console account
3. List of Gmail accounts to authenticate

## Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Up Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

### Step 3: Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Desktop app" as Application type
4. Name it "Gmail Bulk Auth"
5. Click "Create"
6. Download the JSON file
7. **Rename it to `client_secrets.json` and place in this folder**

### Step 4: Configure Your Accounts
1. Open `accounts.csv`
2. Replace the example emails with your 50 Gmail addresses
3. Keep the `account_id` format or customize as needed

Example:
```csv
email,account_id
myfirstaccount@gmail.com,account_001
mysecondaccount@gmail.com,account_002
...
```

### Step 5: Run the Script
```bash
python bulk_gmail_auth.py
```

### Step 6: Authenticate Each Account
The script will:
1. Open a browser window for each account
2. Ask you to login and authorize
3. Save credentials automatically
4. Move to the next account

**Tip:** Keep your browser open. After each authorization, the script will automatically continue to the next account.

## Output Files

After completion, the `credentials/` folder will contain:
- `{account_id}_credentials.json` - JSON credentials for each account
- `{account_id}_token.pickle` - Cached tokens (for reuse)
- `_summary.json` - Report of all processed accounts

## Using the Credentials

Example code to use the generated credentials:

```python
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load credentials
with open('credentials/account_001_credentials.json') as f:
    creds_info = json.load(f)

creds = Credentials(
    token=creds_info['token'],
    refresh_token=creds_info['refresh_token'],
    token_uri=creds_info['token_uri'],
    client_id=creds_info['client_id'],
    client_secret=creds_info['client_secret'],
    scopes=creds_info['scopes']
)

# Use Gmail API
service = build('gmail', 'v1', credentials=creds)
results = service.users().labels().list(userId='me').execute()
print(results)
```

## Troubleshooting

### "Access blocked" Error
If you see "This app is blocked" during authentication:
1. Go to Google Cloud Console > OAuth consent screen
2. Set Publishing status to "In production" (requires verification for some scopes)
3. Or add your Google account as a test user

### Token Expired
Credentials auto-refresh. If issues occur, delete the `.pickle` file for that account and re-run.

### Rate Limits
Google has quotas. Space out authentications if hitting limits.

## Security Notes
- Keep `client_secrets.json` and credential files secure
- Never commit credentials to version control
- Use `.gitignore` to exclude credential files

## File Structure
```
Fastest Gmail API Setup/
├── bulk_gmail_auth.py      # Main script
├── requirements.txt        # Python dependencies
├── accounts.csv           # Your account list
├── client_secrets.json    # Google OAuth credentials
├── credentials/           # Generated output folder
│   ├── account_001_credentials.json
│   ├── account_002_credentials.json
│   └── ...
└── INSTRUCTIONS.md        # This file