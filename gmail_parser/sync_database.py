"""
Synchronous database operations for email storage
This provides a consistent interface for tests and demo scripts
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any
from config import FIELD_MAPPING
from constants import (
    EMAILS_TABLE_SCHEMA, DATABASE_INDEXES, EMAIL_INSERT_QUERY,
    EMAIL_READ_STATUS_UPDATE, EMAIL_LABELS_UPDATE, EMAIL_GET_BY_ID,
    EMAIL_GET_ALL, EMAIL_COUNT, EMAIL_DELETE, EMAIL_CLEAR_ALL,
    EMAIL_SEARCH_QUERY, EMAIL_SEARCH_ORDER
)

logger = logging.getLogger(__name__)

class EmailDatabase:
    """Synchronous email database operations for tests and demo"""
    
    def __init__(self, db_path: str = 'emails.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create emails table
                cursor.execute(EMAILS_TABLE_SCHEMA)
                
                # Add indexes for performance
                for index_query in DATABASE_INDEXES:
                    cursor.execute(index_query)
                
                conn.commit()
                logger.info("Database initialized")
                
        except Exception as e:
            logger.error(f"DB init error: {e}")
            raise
    
    def _serialize_labels(self, labels: List[str]) -> str:
        """Serialize labels list to JSON string"""
        return json.dumps(labels or [])
    
    def _deserialize_labels(self, labels_json: str) -> List[str]:
        """Deserialize JSON string to labels list"""
        try:
            return json.loads(labels_json) if labels_json else []
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Failed to deserialize labels: {labels_json}")
            return []
    
    def _prepare_email_data(self, email_data: Dict[str, Any]) -> tuple:
        """Prepare email data for database insertion"""
        return (
            email_data.get('id'),
            email_data.get('thread_id'),
            email_data.get('from_address'),
            email_data.get('to_address'),
            email_data.get('subject'),
            email_data.get('message'),
            email_data.get('received_date'),
            email_data.get('is_read', False),
            self._serialize_labels(email_data.get('labels', []))
        )
    
    def _process_email_row(self, row: tuple) -> Dict[str, Any]:
        """Process a database row into email data dictionary"""
        columns = ['id', 'thread_id', 'from_address', 'to_address', 'subject', 
                  'message', 'received_date', 'is_read', 'labels', 'created_at']
        email_data = dict(zip(columns, row))
        email_data['labels'] = self._deserialize_labels(email_data['labels'])
        # Convert SQLite integer to boolean
        email_data['is_read'] = bool(email_data['is_read'])
        return email_data
    
    def insert_email(self, email_data: Dict[str, Any]) -> bool:
        """Insert a single email"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(EMAIL_INSERT_QUERY, self._prepare_email_data(email_data))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error inserting email {email_data.get('id')}: {e}")
            return False
    
    def insert_emails_batch(self, emails: List[Dict[str, Any]]) -> int:
        """Insert multiple emails in batch"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for email in emails:
                    cursor.execute(EMAIL_INSERT_QUERY, self._prepare_email_data(email))
                
                conn.commit()
                logger.info(f"Inserted {len(emails)} emails")
                return len(emails)
                
        except Exception as e:
            logger.error(f"Batch insert error: {e}")
            return 0
    
    def get_email_by_id(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Get email by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(EMAIL_GET_BY_ID, (email_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._process_email_row(row)
                return None
                
        except Exception as e:
            logger.error(f"Error getting email {email_id}: {e}")
            return None
    
    def get_emails_by_criteria(self, criteria: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """Get emails by search criteria"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = EMAIL_SEARCH_QUERY
                params = []
                
                for field, value in criteria.items():
                    if field in FIELD_MAPPING.values():
                        query += f" AND {field} LIKE ?"
                        params.append(f"%{value}%")
                
                query += EMAIL_SEARCH_ORDER
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                emails = []
                for row in rows:
                    emails.append(self._process_email_row(row))
                
                return emails
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def get_all_emails(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all emails"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(EMAIL_GET_ALL, (limit,))
                
                rows = cursor.fetchall()
                
                emails = []
                for row in rows:
                    emails.append(self._process_email_row(row))
                
                return emails
                
        except Exception as e:
            logger.error(f"Error getting all emails: {e}")
            return []
    
    def update_email_read_status(self, email_id: str, is_read: bool) -> bool:
        """Update email read status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(EMAIL_READ_STATUS_UPDATE, (is_read, email_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating read status {email_id}: {e}")
            return False
    
    def update_email_labels(self, email_id: str, labels: List[str]) -> bool:
        """Update email labels"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(EMAIL_LABELS_UPDATE, (self._serialize_labels(labels), email_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating labels {email_id}: {e}")
            return False
    
    def delete_email(self, email_id: str) -> bool:
        """Delete an email"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(EMAIL_DELETE, (email_id,))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error deleting email {email_id}: {e}")
            return False
    
    def get_email_count(self) -> int:
        """Get total email count"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(EMAIL_COUNT)
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Error getting count: {e}")
            return 0
    
    def clear_database(self) -> bool:
        """Clear all emails"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(EMAIL_CLEAR_ALL)
                conn.commit()
                
                logger.info("Database cleared")
                return True
                
        except Exception as e:
            logger.error(f"Error clearing DB: {e}")
            return False 