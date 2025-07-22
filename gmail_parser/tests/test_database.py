"""
Unit tests for database module
"""

import pytest
import tempfile
import os
import json
from datetime import datetime
from sync_database import EmailDatabase

class TestEmailDatabase:
    """Test cases for EmailDatabase class"""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def sample_email(self):
        """Sample email data for testing"""
        return {
            'id': 'test_email_123',
            'thread_id': 'thread_456',
            'from_address': 'test@example.com',
            'to_address': 'user@gmail.com',
            'subject': 'Test Email',
            'message': 'This is a test email message',
            'received_date': '2023-12-01T10:00:00',
            'is_read': False,
            'labels': ['INBOX', 'UNREAD']
        }
    
    def test_init_database(self, temp_db):
        """Test database initialization"""
        db = EmailDatabase(temp_db)
        
        # Check if database file was created
        assert os.path.exists(temp_db)
        
        # Check if emails table exists
        import sqlite3
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emails'")
            result = cursor.fetchone()
            assert result is not None
    
    def test_insert_email(self, temp_db, sample_email):
        """Test inserting a single email"""
        db = EmailDatabase(temp_db)
        
        # Insert email
        result = db.insert_email(sample_email)
        assert result is True
        
        # Verify email was inserted
        retrieved_email = db.get_email_by_id(sample_email['id'])
        assert retrieved_email is not None
        assert retrieved_email['id'] == sample_email['id']
        assert retrieved_email['from_address'] == sample_email['from_address']
        assert retrieved_email['subject'] == sample_email['subject']
        assert retrieved_email['labels'] == sample_email['labels']
    
    def test_insert_emails_batch(self, temp_db):
        """Test inserting multiple emails in batch"""
        db = EmailDatabase(temp_db)
        
        emails = [
            {
                'id': f'email_{i}',
                'thread_id': f'thread_{i}',
                'from_address': f'sender{i}@example.com',
                'to_address': 'user@gmail.com',
                'subject': f'Email {i}',
                'message': f'Message {i}',
                'received_date': '2023-12-01T10:00:00',
                'is_read': False,
                'labels': ['INBOX']
            }
            for i in range(5)
        ]
        
        # Insert batch
        count = db.insert_emails_batch(emails)
        assert count == 5
        
        # Verify all emails were inserted
        for email in emails:
            retrieved = db.get_email_by_id(email['id'])
            assert retrieved is not None
            assert retrieved['subject'] == email['subject']
    
    def test_get_email_by_id(self, temp_db, sample_email):
        """Test retrieving email by ID"""
        db = EmailDatabase(temp_db)
        db.insert_email(sample_email)
        
        # Get email
        retrieved = db.get_email_by_id(sample_email['id'])
        assert retrieved is not None
        assert retrieved['id'] == sample_email['id']
        
        # Test non-existent email
        non_existent = db.get_email_by_id('non_existent_id')
        assert non_existent is None
    
    def test_get_emails_by_criteria(self, temp_db):
        """Test retrieving emails by criteria"""
        db = EmailDatabase(temp_db)
        
        # Insert test emails
        emails = [
            {
                'id': 'email1',
                'thread_id': 'thread1',
                'from_address': 'sender1@example.com',
                'to_address': 'user@gmail.com',
                'subject': 'Important email',
                'message': 'This is important',
                'received_date': '2023-12-01T10:00:00',
                'is_read': False,
                'labels': ['INBOX']
            },
            {
                'id': 'email2',
                'thread_id': 'thread2',
                'from_address': 'sender2@example.com',
                'to_address': 'user@gmail.com',
                'subject': 'Regular email',
                'message': 'This is regular',
                'received_date': '2023-12-01T11:00:00',
                'is_read': True,
                'labels': ['INBOX']
            }
        ]
        
        db.insert_emails_batch(emails)
        
        # Search by from_address
        results = db.get_emails_by_criteria({'from_address': 'sender1'})
        assert len(results) == 1
        assert results[0]['id'] == 'email1'
        
        # Search by subject
        results = db.get_emails_by_criteria({'subject': 'Important'})
        assert len(results) == 1
        assert results[0]['subject'] == 'Important email'
    
    def test_update_email_read_status(self, temp_db, sample_email):
        """Test updating email read status"""
        db = EmailDatabase(temp_db)
        db.insert_email(sample_email)
        
        # Update to read
        result = db.update_email_read_status(sample_email['id'], True)
        assert result is True
        
        # Verify update
        retrieved = db.get_email_by_id(sample_email['id'])
        assert retrieved['is_read'] is True
        
        # Update to unread
        result = db.update_email_read_status(sample_email['id'], False)
        assert result is True
        
        # Verify update
        retrieved = db.get_email_by_id(sample_email['id'])
        assert retrieved['is_read'] is False
    
    def test_update_email_labels(self, temp_db, sample_email):
        """Test updating email labels"""
        db = EmailDatabase(temp_db)
        db.insert_email(sample_email)
        
        new_labels = ['INBOX', 'PROCESSED']
        
        # Update labels
        result = db.update_email_labels(sample_email['id'], new_labels)
        assert result is True
        
        # Verify update
        retrieved = db.get_email_by_id(sample_email['id'])
        assert retrieved['labels'] == new_labels
    
    def test_delete_email(self, temp_db, sample_email):
        """Test deleting an email"""
        db = EmailDatabase(temp_db)
        db.insert_email(sample_email)
        
        # Verify email exists
        retrieved = db.get_email_by_id(sample_email['id'])
        assert retrieved is not None
        
        # Delete email
        result = db.delete_email(sample_email['id'])
        assert result is True
        
        # Verify email was deleted
        retrieved = db.get_email_by_id(sample_email['id'])
        assert retrieved is None
    
    def test_get_email_count(self, temp_db):
        """Test getting email count"""
        db = EmailDatabase(temp_db)
        
        # Initially should be 0
        count = db.get_email_count()
        assert count == 0
        
        # Insert emails
        emails = [
            {
                'id': f'email_{i}',
                'thread_id': f'thread_{i}',
                'from_address': f'sender{i}@example.com',
                'to_address': 'user@gmail.com',
                'subject': f'Email {i}',
                'message': f'Message {i}',
                'received_date': '2023-12-01T10:00:00',
                'is_read': False,
                'labels': ['INBOX']
            }
            for i in range(3)
        ]
        
        db.insert_emails_batch(emails)
        
        # Should be 3
        count = db.get_email_count()
        assert count == 3
    
    def test_clear_database(self, temp_db):
        """Test clearing the database"""
        db = EmailDatabase(temp_db)
        
        # Insert some emails
        emails = [
            {
                'id': f'email_{i}',
                'thread_id': f'thread_{i}',
                'from_address': f'sender{i}@example.com',
                'to_address': 'user@gmail.com',
                'subject': f'Email {i}',
                'message': f'Message {i}',
                'received_date': '2023-12-01T10:00:00',
                'is_read': False,
                'labels': ['INBOX']
            }
            for i in range(3)
        ]
        
        db.insert_emails_batch(emails)
        
        # Verify emails exist
        assert db.get_email_count() == 3
        
        # Clear database
        result = db.clear_database()
        assert result is True
        
        # Verify database is empty
        assert db.get_email_count() == 0 