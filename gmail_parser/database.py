"""
Database operations for email storage
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
import aiosqlite
from config import DB_PATH, FIELD_MAPPING
from db_utils import DatabaseUtils, DatabaseConnection
from constants import (
    EMAILS_TABLE_SCHEMA, DATABASE_INDEXES, EMAIL_INSERT_QUERY,
    EMAIL_READ_STATUS_UPDATE, EMAIL_LABELS_UPDATE, EMAIL_GET_BY_ID,
    EMAIL_GET_ALL, EMAIL_COUNT, EMAIL_DELETE, EMAIL_CLEAR_ALL,
    EMAIL_SEARCH_QUERY, EMAIL_SEARCH_ORDER
)

logger = logging.getLogger(__name__)

class EmailDB:
    """Handles email storage and retrieval"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
    
    async def init_db(self):
        """Set up the database tables"""
        try:
            async with DatabaseConnection(self.db_path) as db:
                # Create emails table
                await db.execute(EMAILS_TABLE_SCHEMA)
                
                # Add indexes for performance
                for index_query in DATABASE_INDEXES:
                    await db.execute(index_query)
                
                await db.commit()
                logger.info("Database initialized")
                
        except Exception as e:
            logger.error(f"DB init error: {e}")
            raise
    
    async def add_email(self, email_data: Dict[str, Any]) -> bool:
        """Add a single email to the database"""
        try:
            async with DatabaseConnection(self.db_path) as db:
                await db.execute(EMAIL_INSERT_QUERY, DatabaseUtils.prepare_email_data(email_data))
                
                await db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding email {email_data.get('id')}: {e}")
            return False
    
    async def add_emails_batch(self, emails: List[Dict[str, Any]]) -> int:
        """Add multiple emails at once"""
        try:
            async with DatabaseConnection(self.db_path) as db:
                for email in emails:
                    await db.execute(EMAIL_INSERT_QUERY, DatabaseUtils.prepare_email_data(email))
                
                await db.commit()
                logger.info(f"Added {len(emails)} emails")
                return len(emails)
                
        except Exception as e:
            logger.error(f"Batch insert error: {e}")
            return 0
    
    async def get_email(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Get a single email by ID"""
        try:
            async with DatabaseConnection(self.db_path) as db:
                async with db.execute(EMAIL_GET_BY_ID, (email_id,)) as cursor:
                    row = await cursor.fetchone()
                    
                    if row:
                        return DatabaseUtils.process_email_row(row)
                    return None
                
        except Exception as e:
            logger.error(f"Error getting email {email_id}: {e}")
            return None
    
    async def search_emails(self, criteria: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """Search emails based on criteria"""
        try:
            async with DatabaseConnection(self.db_path) as db:
                query, params = DatabaseUtils.build_search_query(criteria)
                query += EMAIL_SEARCH_ORDER
                params.append(limit)
                
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    
                    emails = []
                    for row in rows:
                        emails.append(DatabaseUtils.process_email_row(row))
                    
                    return emails
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    async def get_all_emails(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all emails with limit"""
        try:
            async with DatabaseConnection(self.db_path) as db:
                async with db.execute(EMAIL_GET_ALL, (limit,)) as cursor:
                    
                    rows = await cursor.fetchall()
                    
                    emails = []
                    for row in rows:
                        emails.append(DatabaseUtils.process_email_row(row))
                    
                    return emails
                
        except Exception as e:
            logger.error(f"Error getting all emails: {e}")
            return []
    
    async def mark_as_read(self, email_id: str, is_read: bool) -> bool:
        """Mark email as read/unread"""
        try:
            async with DatabaseConnection(self.db_path) as db:
                await db.execute(EMAIL_READ_STATUS_UPDATE, (is_read, email_id))
                
                await db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error marking email {email_id}: {e}")
            return False
    
    async def update_labels(self, email_id: str, labels: List[str]) -> bool:
        """Update email labels"""
        try:
            async with DatabaseConnection(self.db_path) as db:
                await db.execute(EMAIL_LABELS_UPDATE, (DatabaseUtils.serialize_labels(labels), email_id))
                
                await db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating labels {email_id}: {e}")
            return False
    
    async def delete_email(self, email_id: str) -> bool:
        """Delete an email"""
        try:
            async with DatabaseConnection(self.db_path) as db:
                await db.execute(EMAIL_DELETE, (email_id,))
                await db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error deleting email {email_id}: {e}")
            return False
    
    async def get_count(self) -> int:
        """Get total email count"""
        try:
            async with DatabaseConnection(self.db_path) as db:
                async with db.execute(EMAIL_COUNT) as cursor:
                    result = await cursor.fetchone()
                    return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Error getting count: {e}")
            return 0
    
    async def clear_all(self) -> bool:
        """Clear all emails"""
        try:
            async with DatabaseConnection(self.db_path) as db:
                await db.execute(EMAIL_CLEAR_ALL)
                await db.commit()
                
                logger.info("Database cleared")
                return True
                
        except Exception as e:
            logger.error(f"Error clearing DB: {e}")
            return False 