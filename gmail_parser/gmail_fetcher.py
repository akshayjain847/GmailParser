"""
Gmail API integration with real authentication
"""

import os
import base64
import email
import logging
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from database import EmailDB
from auth_utils import GmailAuthManager
from config import (
    GMAIL_SCOPES, EMAIL_ID, EMAIL_PASSWORD,
    MAX_EMAILS_PER_REQUEST, BATCH_SIZE, RATE_LIMIT_PER_SEC
)

logger = logging.getLogger(__name__)

class GmailFetcher:
    """Handles Gmail API operations with real authentication"""
    
    def __init__(self):
        self.service = None
        self.db = EmailDB()
    
    async def authenticate(self) -> bool:
        """Authenticate with Gmail API using OAuth 2.0"""
        try:
            logger.info("Starting Gmail API authentication...")
            logger.info(f"Will authenticate as: {EMAIL_ID}")
            
            # Use common authentication manager
            self.service = await GmailAuthManager.authenticate()
            
            if self.service:
                logger.info("Gmail API authentication successful")
                return True
            else:
                logger.error("Failed to authenticate with Gmail API")
                return False
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get full message content from real Gmail API"""
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=message_id, 
                format='full'
            ).execute()
            
            return message
            
        except HttpError as e:
            logger.error(f"Error fetching message {message_id}: {e}")
            return None
    
    async def parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gmail message into our format"""
        try:
            # Extract headers
            headers = message.get('payload', {}).get('headers', [])
            header_dict = {h['name']: h['value'] for h in headers}
            
            # Get basic info
            email_id = message['id']
            thread_id = message.get('threadId', '')
            subject = header_dict.get('Subject', '')
            from_address = header_dict.get('From', '')
            to_address = header_dict.get('To', '')
            date_received = header_dict.get('Date', '')
            
            # Parse date
            try:
                if date_received:
                    parsed_date = email.utils.parsedate_to_datetime(date_received)
                    received_date = parsed_date.isoformat()
                else:
                    received_date = datetime.now().isoformat()
            except:
                received_date = datetime.now().isoformat()
            
            # Get message body
            message_body = await self._extract_body(message)
            
            # Get labels
            labels = message.get('labelIds', [])
            
            # Check read status
            is_read = 'UNREAD' not in labels
            
            return {
                'id': email_id,
                'thread_id': thread_id,
                'from_address': from_address,
                'to_address': to_address,
                'subject': subject,
                'message': message_body,
                'received_date': received_date,
                'is_read': is_read,
                'labels': labels
            }
            
        except Exception as e:
            logger.error(f"Message parsing error: {e}")
            return {}
    
    async def _extract_body(self, message: Dict[str, Any]) -> str:
        """Extract text content from message"""
        try:
            payload = message.get('payload', {})
            
            # Handle multipart messages
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain':
                        data = part.get('body', {}).get('data', '')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8')
            
            # Handle simple text messages
            if payload.get('mimeType') == 'text/plain':
                data = payload.get('body', {}).get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
            
            # Fallback to HTML
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/html':
                        data = part.get('body', {}).get('data', '')
                        if data:
                            html_content = base64.urlsafe_b64decode(data).decode('utf-8')
                            # Simple HTML to text
                            import re
                            text_content = re.sub('<[^<]+?>', '', html_content)
                            return text_content.strip()
            
            return ""
            
        except Exception as e:
            logger.error(f"Body extraction error: {e}")
            return ""
    
    async def fetch_emails(self, max_results: int = None) -> List[Dict[str, Any]]:
        """Fetch emails from inbox using real Gmail API"""
        try:
            if not self.service:
                logger.error("Gmail service not initialized")
                return []
            
            max_results = max_results or MAX_EMAILS_PER_REQUEST
            emails = []
            
            # Get message list from real Gmail API
            logger.info(f"Fetching up to {max_results} emails from your Gmail inbox...")
            
            try:
                results = self.service.users().messages().list(
                    userId='me',
                    labelIds=['INBOX'],
                    maxResults=max_results
                ).execute()
                
                messages = results.get('messages', [])
                logger.info(f"Found {len(messages)} real emails in your inbox")
                
                # Process in batches
                for i in range(0, len(messages), BATCH_SIZE):
                    batch = messages[i:i + BATCH_SIZE]
                    logger.info(f"Processing batch {i//BATCH_SIZE + 1}/{(len(messages) + BATCH_SIZE - 1)//BATCH_SIZE}")
                    
                    for message in batch:
                        try:
                            # Get full message from real Gmail API
                            full_message = await self.get_message(message['id'])
                            if full_message:
                                # Parse and add email
                                parsed_email = await self.parse_message(full_message)
                                if parsed_email:
                                    emails.append(parsed_email)
                            
                            # Rate limiting
                            await asyncio.sleep(1.0 / RATE_LIMIT_PER_SEC)
                            
                        except Exception as e:
                            logger.error(f"Error processing message {message['id']}: {e}")
                            continue
                
                logger.info(f"Processed {len(emails)} real emails from your Gmail account")
                return emails
                
            except HttpError as e:
                logger.error(f"Gmail API error: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            return []
    
    async def fetch_and_store(self, max_results: int = None) -> int:
        """Fetch emails and store in database"""
        try:
            # Initialize database
            await self.db.init_db()
            
            emails = await self.fetch_emails(max_results)
            print("emails : ", emails)
            if emails:
                stored_count = await self.db.add_emails_batch(emails)
                logger.info(f"Stored {stored_count} real emails")
                return stored_count
            return 0
            
        except Exception as e:
            logger.error(f"Fetch and store error: {e}")
            return 0
    
    async def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get user profile info from real Gmail API"""
        try:
            if not self.service:
                logger.error("Gmail service not initialized")
                return None
            
            profile = self.service.users().getProfile(userId='me').execute()
            return profile
            
        except HttpError as e:
            logger.error(f"Error getting profile: {e}")
            return None
    
    async def get_labels(self) -> List[Dict[str, Any]]:
        """Get all labels from real Gmail API"""
        try:
            if not self.service:
                logger.error("Gmail service not initialized")
                return []
            
            results = self.service.users().labels().list(userId='me').execute()
            return results.get('labels', [])
            
        except HttpError as e:
            logger.error(f"Error getting labels: {e}")
            return []

async def main():
    """Main function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    fetcher = GmailFetcher()
    
    # Authenticate
    if not await fetcher.authenticate():
        logger.error("Authentication failed")
        return
    
    # Get user info
    user_info = await fetcher.get_user_info()
    if user_info:
        logger.info(f"Authenticated as: {user_info.get('emailAddress', 'Unknown')}")
    
    # Fetch and store emails
    stored_count = await fetcher.fetch_and_store()
    logger.info(f"Done. Stored {stored_count} real emails.")

if __name__ == '__main__':
    asyncio.run(main()) 