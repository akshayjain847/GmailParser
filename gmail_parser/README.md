# Gmail API Email Processor

A Python application that integrates with Gmail API to fetch emails and apply rule-based processing with actions like marking as read and moving messages to labels.

## Features

- **OAuth 2.0 Authentication**: Secure authentication using Google OAuth 2.0
- **Async Operations**: Fully asynchronous implementation for better performance
- **Rule-Based Processing**: JSON-based rules with conditions and actions
- **Database Storage**: SQLite database for email storage and retrieval
- **Batch Processing**: Handles large email volumes efficiently
- **Rate Limiting**: Respects Gmail API rate limits
- **Gmail API Integration**: Real Gmail API integration for fetching and processing emails

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Authentication Setup [I will provide credentials.json file in mail for testing if needed]

**⚠️ IMPORTANT: You must set up Gmail API credentials to use this application.**

The application requires OAuth 2.0 authentication with Gmail API. Follow these steps to set up your credentials:

#### **Google Cloud Console Setup (Required)** I can share mine for demo over email

1. **Create a Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable Gmail API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it

3. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the JSON file

4. **Configure Credentials**:
   - Rename the downloaded file to `credentials.json`
   - Place it in the project root directory

**Note**: The application will not work without a valid `credentials.json` file.

### 3. Create Rules File

Create a `rules.json` file with your email processing rules:

```json
[
  {
    "predicate": "All",
    "conditions": [
      {
        "field": "From",
        "predicate": "Contains",
        "value": "newsletter"
      },
      {
        "field": "Subject",
        "predicate": "Contains",
        "value": "weekly"
      }
    ],
    "actions": [
      {
        "type": "mark_read",
        "value": true
      },
      {
        "type": "move_message",
        "value": "Newsletters"
      }
    ]
  }
]
```

## Usage

### 1. Fetch Emails

First, authenticate and fetch emails from Gmail:

```bash
python gmail_fetcher.py
```

This will:
- Authenticate using OAuth 2.0 (requires `credentials.json`)
- Fetch emails from your inbox
- Store them in the local database (`emails.db`)

### 2. Process Emails

Apply rules and execute actions:

```bash
python email_processor.py
```

This will:
- Load rules from `rules.json`
- Process stored emails against rules
- Execute actions (mark as read, move messages)


## Configuration

### Supported Fields
- `From`: Sender email address
- `To`: Recipient email address  
- `Subject`: Email subject line
- `Message`: Email body content
- `Received`: Date/time received

### Supported Predicates

**String Fields:**
- `Contains`: Text contains value
- `Does not Contain`: Text doesn't contain value
- `Equals`: Exact match
- `Does not equal`: Not exact match

**Date Fields:**
- `Less than`: Date is before specified time (e.g., "7 days")
- `Greater than`: Date is after specified time (e.g., "2 months")

### Supported Actions
- `mark_read`: Mark email as read/unread
- `mark_unread`: Mark email as unread
- `move_message`: Move email to specified label

### Rule Logic
- `All`: All conditions must match
- `Any`: At least one condition must match

## Project Structure

```
├── config.py              # Configuration settings
├── database.py            # Async database operations
├── sync_database.py       # Sync database operations for tests
├── db_utils.py            # Database utilities
├── auth_utils.py          # Authentication utilities
├── constants.py           # Common constants
├── rule_engine.py         # Rule evaluation
├── gmail_fetcher.py       # Gmail API integration
├── email_processor.py     # Main processing workflow
├── credentials.json      # Gmail API credentials (REQUIRED - not in repo)
├── rules.json            # Email processing rules
├── requirements.txt      # Python dependencies
├── emails.db             # SQLite database (auto-generated)
└── tests/               # Test suite
```

## Testing

Run the test suite:

```bash
pytest tests/
```


## Troubleshooting

### Authentication Issues
- **Ensure `credentials.json` is properly configured and present in the project root**
- Check that Gmail API is enabled in Google Cloud Console
- Verify your OAuth 2.0 credentials are for "Desktop application" type


### Rate Limiting
- The app includes built-in rate limiting (1 request/second)
- For large email volumes, processing may take time

### Database Issues
- Delete `emails.db` to start fresh
- Check file permissions for database access

### Rule Processing
- Ensure `rules.json` exists and has valid JSON format
- Check rule syntax matches supported fields and predicates
