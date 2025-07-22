"""
Common database utilities and operations
"""

import json
import logging
from typing import List, Dict, Any, Optional
import aiosqlite
from config import FIELD_MAPPING

logger = logging.getLogger(__name__)

class DatabaseUtils:
    """Common database utility functions"""
    
    @staticmethod
    def serialize_labels(labels: List[str]) -> str:
        """Serialize labels list to JSON string"""
        return json.dumps(labels or [])
    
    @staticmethod
    def deserialize_labels(labels_json: str) -> List[str]:
        """Deserialize JSON string to labels list"""
        try:
            return json.loads(labels_json) if labels_json else []
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Failed to deserialize labels: {labels_json}")
            return []
    
    @staticmethod
    def prepare_email_data(email_data: Dict[str, Any]) -> tuple:
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
            DatabaseUtils.serialize_labels(email_data.get('labels', []))
        )
    
    @staticmethod
    def process_email_row(row: aiosqlite.Row) -> Dict[str, Any]:
        """Process a database row into email data dictionary"""
        email_data = dict(row)
        email_data['labels'] = DatabaseUtils.deserialize_labels(email_data['labels'])
        # Convert SQLite integer to boolean
        email_data['is_read'] = bool(email_data['is_read'])
        return email_data
    
    @staticmethod
    def build_search_query(criteria: Dict[str, Any]) -> tuple:
        """Build search query and parameters from criteria"""
        query = "SELECT * FROM emails WHERE 1=1"
        params = []
        
        for field, value in criteria.items():
            if field in FIELD_MAPPING.values():
                query += f" AND {field} LIKE ?"
                params.append(f"%{value}%")
        
        return query, params

class DatabaseConnection:
    """Database connection context manager"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    async def __aenter__(self):
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        return self.db
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.close() 