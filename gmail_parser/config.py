"""
Config settings for the email processor
"""

import os
from pathlib import Path

# Gmail API settings
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels'
]


# Authentication methods
# Primary: Email/Password authentication (for assignment)
EMAIL_ID = os.getenv('GMAIL_EMAIL', '')  # Change this to your email
EMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD', '')  # Change this to your app password

# Fallback: OAuth 2.0 credentials (requires Google Cloud Console setup)
CREDS_FILE = 'credentials.json'

# File paths
DB_FILE = 'emails.db'
RULES_FILE = 'rules.json'

# DB config
DB_PATH = Path(DB_FILE)

# API limits
MAX_EMAILS_PER_REQUEST = 10
BATCH_SIZE = 10
RATE_LIMIT_PER_SEC = 1.0

# Rule fields mapping
FIELD_MAPPING = {
    'From': 'from_address',
    'To': 'to_address', 
    'Subject': 'subject',
    'Message': 'message',
    'Received': 'received_date'
}

# String predicates
STRING_PREDICATES = [
    'Contains',
    'Does not Contain', 
    'Equals',
    'Does not equal'
]

# Date predicates
DATE_PREDICATES = [
    'Less than',
    'Greater than'
]

# Available actions
ACTIONS = [
    "mark_unread",
    'mark_read',
    'move_message'
]

# Default labels
DEFAULT_LABELS = ['INBOX']

# Processing settings
BATCH_PROCESS_SIZE = 50
MAX_PROCESS_TIME = 300  # 5 min

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = 'email_processor.log' 