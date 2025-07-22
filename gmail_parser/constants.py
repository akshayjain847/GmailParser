"""
Common constants and configuration values
"""

# OAuth 2.0 Configuration
OAUTH_CLIENT_CONFIG = {
    "installed": {
        "client_id": "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com",
        "project_id": "gmail-api-quickstart",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "d-FL95Q19q7MQmFpd7hHD0Ty",
        "redirect_uris": ["http://localhost:8080"]
    }
}

# OAuth flow settings
OAUTH_REDIRECT_URI = 'http://localhost:8080'
OAUTH_PORT = 8080

# Database table schema
EMAILS_TABLE_SCHEMA = '''
    CREATE TABLE IF NOT EXISTS emails (
        id TEXT PRIMARY KEY,
        thread_id TEXT,
        from_address TEXT,
        to_address TEXT,
        subject TEXT,
        message TEXT,
        received_date DATETIME,
        is_read BOOLEAN,
        labels TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
'''

# Database indexes
DATABASE_INDEXES = [
    'CREATE INDEX IF NOT EXISTS idx_from ON emails(from_address)',
    'CREATE INDEX IF NOT EXISTS idx_subject ON emails(subject)',
    'CREATE INDEX IF NOT EXISTS idx_date ON emails(received_date)',
    'CREATE INDEX IF NOT EXISTS idx_read ON emails(is_read)'
]

# Email insertion query
EMAIL_INSERT_QUERY = '''
    INSERT OR REPLACE INTO emails 
    (id, thread_id, from_address, to_address, subject, message, 
     received_date, is_read, labels)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
'''

# Email update queries
EMAIL_READ_STATUS_UPDATE = '''
    UPDATE emails 
    SET is_read = ? 
    WHERE id = ?
'''

EMAIL_LABELS_UPDATE = '''
    UPDATE emails 
    SET labels = ? 
    WHERE id = ?
'''

# Email search query template
EMAIL_SEARCH_QUERY = "SELECT * FROM emails WHERE 1=1"
EMAIL_SEARCH_ORDER = " ORDER BY received_date DESC LIMIT ?"

# Email retrieval queries
EMAIL_GET_BY_ID = 'SELECT * FROM emails WHERE id = ?'
EMAIL_GET_ALL = 'SELECT * FROM emails ORDER BY received_date DESC LIMIT ?'
EMAIL_COUNT = 'SELECT COUNT(*) FROM emails'
EMAIL_DELETE = 'DELETE FROM emails WHERE id = ?'
EMAIL_CLEAR_ALL = 'DELETE FROM emails' 