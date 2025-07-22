"""
Common authentication utilities for Gmail API
"""

import os
import json
import logging
from typing import Optional
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import GMAIL_SCOPES
from constants import OAUTH_CLIENT_CONFIG, OAUTH_REDIRECT_URI, OAUTH_PORT

logger = logging.getLogger(__name__)

class GmailAuthManager:
    """Handles Gmail API authentication with OAuth 2.0"""
    
    @staticmethod
    async def create_oauth_flow() -> Optional[InstalledAppFlow]:
        """Create OAuth flow for Gmail API access"""
        try:
            # Check if credentials.json exists (proper Google Cloud Console setup)
            if os.path.exists('credentials.json'):
                logger.info("Using credentials.json for OAuth flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json',
                    GMAIL_SCOPES,
                    redirect_uri=OAUTH_REDIRECT_URI
                )
                return flow
            
            # If no credentials.json, create a simple OAuth flow
            logger.info("Creating OAuth flow without Google Cloud Console setup...")
            
            # Save the client secret to a temporary file
            client_secret_file = 'temp_client_secret.json'
            with open(client_secret_file, 'w') as f:
                json.dump(OAUTH_CLIENT_CONFIG, f)
            
            try:
                # Create OAuth flow
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secret_file, 
                    GMAIL_SCOPES,
                    redirect_uri=OAUTH_REDIRECT_URI
                )
                
                return flow
                
            finally:
                # Clean up temporary file
                if os.path.exists(client_secret_file):
                    os.remove(client_secret_file)
                    
        except Exception as e:
            logger.error(f"Error creating OAuth flow: {e}")
            return None
    
    @staticmethod
    async def authenticate() -> Optional[object]:
        """Authenticate with Gmail API using OAuth 2.0"""
        try:
            logger.info("Starting Gmail API authentication...")
            
            # Create OAuth flow
            flow = await GmailAuthManager.create_oauth_flow()
            
            if flow:
                # Run the OAuth flow - this will open browser for Google sign-in
                creds = flow.run_local_server(port=OAUTH_PORT)
                
                # Build service using Google's official client
                service = build('gmail', 'v1', credentials=creds)
                
                logger.info("Gmail API authentication successful")
                return service
            else:
                logger.error("Failed to create OAuth flow")
                return None
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None 