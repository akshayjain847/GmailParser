"""
Email processor for applying rules and actions with real Gmail API
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from database import EmailDB
from rule_engine import RuleEngine
from auth_utils import GmailAuthManager
from config import (
    GMAIL_SCOPES, EMAIL_ID, EMAIL_PASSWORD, BATCH_PROCESS_SIZE,
    MAX_PROCESS_TIME, RATE_LIMIT_PER_SEC
)

logger = logging.getLogger(__name__)

class EmailProcessor:
    """Handles email processing with rules using real Gmail API"""
    
    def __init__(self):
        self.service = None
        self.db = EmailDB()
        self.rule_engine = RuleEngine()
    
    async def authenticate(self) -> bool:
        """Authenticate with Gmail API using OAuth 2.0"""
        try:
            logger.info("Starting Gmail API authentication for email processing...")
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
    
    async def mark_as_read(self, email_id: str, is_read: bool) -> bool:
        """Mark email as read/unread using real Gmail API"""
        try:
            if not self.service:
                logger.error("Gmail service not initialized")
                return False
            
            # Prepare modification
            if is_read:
                modification = {'removeLabelIds': ['UNREAD']}
            else:
                modification = {'addLabelIds': ['UNREAD']}
            
            # Apply modification using real Gmail API
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body=modification
            ).execute()
            
            # Update database
            await self.db.mark_as_read(email_id, is_read)
            
            logger.info(f"Marked email {email_id} as {'read' if is_read else 'unread'}")
            return True
            
        except HttpError as e:
            logger.error(f"Error marking email {email_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error marking email {email_id}: {e}")
            return False
    
    async def move_message(self, email_id: str, destination: str) -> bool:
        """Move email to different folder using real Gmail API"""
        try:
            if not self.service:
                logger.error("Gmail service not initialized")
                return False
            
            # Get current labels using real Gmail API
            message = self.service.users().messages().get(
                userId='me', 
                id=email_id, 
                format='metadata',
                metadataHeaders=['Subject']
            ).execute()
            
            current_labels = message.get('labelIds', [])
            
            # Remove from INBOX
            if 'INBOX' in current_labels:
                modification = {'removeLabelIds': ['INBOX']}
                self.service.users().messages().modify(
                    userId='me',
                    id=email_id,
                    body=modification
                ).execute()
            
            # Add to destination label
            label_id = await self._get_or_create_label(destination)
            if label_id:
                modification = {'addLabelIds': [label_id]}
                self.service.users().messages().modify(
                    userId='me',
                    id=email_id,
                    body=modification
                ).execute()
                
                # Update database
                new_labels = [l for l in current_labels if l != 'INBOX'] + [label_id]
                await self.db.update_labels(email_id, new_labels)
                
                logger.info(f"Moved email {email_id} to {destination}")
                return True
            else:
                logger.error(f"Could not create/find label: {destination}")
                return False
                
        except HttpError as e:
            logger.error(f"Error moving email {email_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error moving email {email_id}: {e}")
            return False
    
    async def _get_or_create_label(self, label_name: str) -> Optional[str]:
        """Get existing label or create new one using real Gmail API"""
        try:
            # Get all labels using real Gmail API
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            # Check if label exists (including system labels)
            for label in labels:
                if label.get('name') == label_name:
                    return label['id']
            
            # For system labels, we should not try to create them
            system_labels = ['INBOX', 'SENT', 'DRAFT', 'SPAM', 'TRASH', 'STARRED', 'UNREAD', 'IMPORTANT']
            if label_name in system_labels:
                logger.warning(f"System label '{label_name}' not found. This may indicate an issue with Gmail API access.")
                return None
            
            # Create new label using real Gmail API (only for user-created labels)
            label_object = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            
            created_label = self.service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()
            
            logger.info(f"Created label: {label_name}")
            return created_label['id']
            
        except HttpError as e:
            logger.error(f"Error creating label {label_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error with label {label_name}: {e}")
            return None
    
    async def execute_actions(self, email_id: str, actions: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Execute multiple actions on an email using real Gmail API"""
        results = {}
        
        for action in actions:
            action_type = action.get('type')
            action_value = action.get('value')
            
            if action_type == 'mark_read':
                success = await self.mark_as_read(email_id, action_value)
                results[f"mark_read_{action_value}"] = success
                
            elif action_type == 'mark_unread':
                success = await self.mark_as_read(email_id, False)  # False = mark as unread
                results["mark_unread"] = success
                
            elif action_type == 'move_message':
                success = await self.move_message(email_id, action_value)
                results[f"move_to_{action_value}"] = success
                
            else:
                logger.warning(f"Unknown action: {action_type}")
                results[action_type] = False
            
            # Rate limiting
            await asyncio.sleep(1.0 / RATE_LIMIT_PER_SEC)
        
        return results
    
    async def process_with_rules(self) -> Dict[str, Any]:
        """Process all emails with rules using real Gmail API"""
        try:
            # Get all emails
            emails = await self.db.get_all_emails()
            if not emails:
                logger.info("No emails found")
                return {'processed': 0, 'matched': 0, 'actions_executed': 0}
            
            logger.info(f"Processing {len(emails)} real emails")
            
            # Get rule summary
            rule_summary = self.rule_engine.get_summary()
            logger.info(f"Loaded {rule_summary['total_rules']} rules")
            
            # Process emails against rules
            results = await self.rule_engine.process_emails(emails)
            
            total_matched = 0
            total_actions = 0
            
            # Execute actions for matching emails
            for rule_name, rule_result in results.items():
                rule = rule_result['rule']
                matching_emails = rule_result['matching_emails']
                count = rule_result['count']
                
                if count > 0:
                    logger.info(f"Rule '{rule_name}' matched {count} emails")
                    total_matched += count
                    
                    # Execute actions for each matching email
                    for email in matching_emails:
                        email_id = email['id']
                        actions = rule['actions']
                        
                        logger.info(f"Executing {len(actions)} actions on email {email_id}")
                        action_results = await self.execute_actions(email_id, actions)
                        
                        # Count successful actions
                        successful_actions = sum(1 for success in action_results.values() if success)
                        total_actions += successful_actions
                        
                        logger.info(f"Email {email_id}: {successful_actions}/{len(actions)} actions successful")
                        
                        # Rate limiting
                        await asyncio.sleep(1.0 / RATE_LIMIT_PER_SEC)
                else:
                    logger.info(f"Rule '{rule_name}' matched 0 emails")
            
            return {
                'processed': len(emails),
                'matched': total_matched,
                'actions_executed': total_actions,
                'rules_processed': len(results)
            }
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return {'processed': 0, 'matched': 0, 'actions_executed': 0, 'error': str(e)}
    
    async def process_in_batches(self) -> Dict[str, Any]:
        """Process emails in batches for large datasets"""
        try:
            total_emails = await self.db.get_count()
            if total_emails == 0:
                logger.info("No emails found")
                return {'processed': 0, 'matched': 0, 'actions_executed': 0}
            
            logger.info(f"Processing {total_emails} real emails in batches")
            
            total_matched = 0
            total_actions = 0
            processed_count = 0
            
            # Process in batches
            offset = 0
            while offset < total_emails:
                batch_emails = await self.db.get_all_emails(BATCH_PROCESS_SIZE)
                if not batch_emails:
                    break
                
                logger.info(f"Processing batch: {offset + 1} to {offset + len(batch_emails)}")
                
                # Process batch with rules
                batch_results = await self.rule_engine.process_emails(batch_emails)
                
                # Execute actions for matching emails
                for rule_name, rule_result in batch_results.items():
                    rule = rule_result['rule']
                    matching_emails = rule_result['matching_emails']
                    
                    for email in matching_emails:
                        email_id = email['id']
                        actions = rule['actions']
                        
                        action_results = await self.execute_actions(email_id, actions)
                        successful_actions = sum(1 for success in action_results.values() if success)
                        total_actions += successful_actions
                        total_matched += 1
                
                processed_count += len(batch_emails)
                offset += BATCH_PROCESS_SIZE
                
                logger.info(f"Batch completed. Processed: {processed_count}/{total_emails}")
                
                # Rate limiting between batches
                await asyncio.sleep(2.0 / RATE_LIMIT_PER_SEC)
            
            return {
                'processed': processed_count,
                'matched': total_matched,
                'actions_executed': total_actions
            }
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            return {'processed': 0, 'matched': 0, 'actions_executed': 0, 'error': str(e)}
    
    def reload_rules(self):
        """Reload rules from file"""
        self.rule_engine.reload_rules()
        logger.info("Rules reloaded")

async def main():
    """Main function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    processor = EmailProcessor()
    
    # Authenticate
    if not await processor.authenticate():
        logger.error("Authentication failed")
        return
    
    # Check if rules file exists
    if not os.path.exists('rules.json'):
        logger.error("rules.json file not found. Create it with your email rules.")
        return
    
    # Process emails
    logger.info("Starting email processing with real Gmail API...")
    results = await processor.process_with_rules()
    
    # Print results
    logger.info("Processing completed!")
    logger.info(f"Emails processed: {results.get('processed', 0)}")
    logger.info(f"Emails matched: {results.get('matched', 0)}")
    logger.info(f"Actions executed: {results.get('actions_executed', 0)}")
    
    if 'error' in results:
        logger.error(f"Error occurred: {results['error']}")

if __name__ == '__main__':
    asyncio.run(main()) 