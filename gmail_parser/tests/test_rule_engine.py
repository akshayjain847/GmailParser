"""
Unit tests for rule engine module
"""

import pytest
import tempfile
import json
import os
import asyncio
from datetime import datetime, timedelta
from rule_engine import RuleEngine

class TestRuleEngine:
    """Test cases for RuleEngine class"""
    
    @pytest.fixture
    def temp_rules_file(self):
        """Create a temporary rules file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            rules = [
                {
                    "predicate": "All",
                    "conditions": [
                        {
                            "field": "From",
                            "predicate": "Contains",
                            "value": "test@example.com"
                        },
                        {
                            "field": "Subject",
                            "predicate": "Contains",
                            "value": "important"
                        }
                    ],
                    "actions": [
                        {
                            "type": "mark_read",
                            "value": True
                        }
                    ]
                }
            ]
            json.dump(rules, f)
        
        yield f.name
        
        # Cleanup
        if os.path.exists(f.name):
            os.unlink(f.name)
    
    @pytest.fixture
    def sample_email(self):
        """Sample email for testing"""
        return {
            'id': 'test_email_123',
            'thread_id': 'thread_456',
            'from_address': 'test@example.com',
            'to_address': 'user@gmail.com',
            'subject': 'Important test email',
            'message': 'This is an important test message',
            'received_date': datetime.now().isoformat(),
            'is_read': False,
            'labels': ['INBOX', 'UNREAD']
        }
    
    def test_load_rules(self, temp_rules_file):
        """Test loading rules from file"""
        engine = RuleEngine(temp_rules_file)
        
        assert len(engine.rules) == 1
        rule = engine.rules[0]
        assert rule['predicate'] == 'All'
        assert len(rule['conditions']) == 2
        assert len(rule['actions']) == 1
    
    def test_load_rules_file_not_found(self):
        """Test loading rules when file doesn't exist"""
        engine = RuleEngine('non_existent_file.json')
        assert len(engine.rules) == 0
    
    def test_load_rules_invalid_json(self):
        """Test loading rules with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json content')
        
        try:
            engine = RuleEngine(f.name)
            assert len(engine.rules) == 0
        finally:
            os.unlink(f.name)
    
    def test_validate_rule_valid(self, temp_rules_file):
        """Test validating a valid rule"""
        engine = RuleEngine(temp_rules_file)
        rule = engine.rules[0]
        
        assert engine._validate_rule(rule) is True
    
    def test_validate_rule_missing_fields(self):
        """Test validating rule with missing required fields"""
        engine = RuleEngine()
        
        invalid_rule = {
            "predicate": "All",
            "conditions": []
            # Missing 'actions' field
        }
        
        assert engine._validate_rule(invalid_rule) is False
    
    def test_validate_rule_invalid_predicate(self):
        """Test validating rule with invalid predicate"""
        engine = RuleEngine()
        
        invalid_rule = {
            "predicate": "Invalid",
            "conditions": [],
            "actions": []
        }
        
        assert engine._validate_rule(invalid_rule) is False
    
    def test_validate_condition_valid(self):
        """Test validating a valid condition"""
        engine = RuleEngine()
        
        valid_condition = {
            "field": "From",
            "predicate": "Contains",
            "value": "test@example.com"
        }
        
        assert engine._validate_condition(valid_condition) is True
    
    def test_validate_condition_invalid_field(self):
        """Test validating condition with invalid field"""
        engine = RuleEngine()
        
        invalid_condition = {
            "field": "InvalidField",
            "predicate": "Contains",
            "value": "test"
        }
        
        assert engine._validate_condition(invalid_condition) is False
    
    def test_validate_condition_invalid_predicate(self):
        """Test validating condition with invalid predicate"""
        engine = RuleEngine()
        
        invalid_condition = {
            "field": "From",
            "predicate": "InvalidPredicate",
            "value": "test"
        }
        
        assert engine._validate_condition(invalid_condition) is False
    
    def test_validate_action_valid(self):
        """Test validating a valid action"""
        engine = RuleEngine()
        
        valid_action = {
            "type": "mark_read",
            "value": True
        }
        
        assert engine._validate_action(valid_action) is True
    
    def test_validate_action_invalid_type(self):
        """Test validating action with invalid type"""
        engine = RuleEngine()
        
        invalid_action = {
            "type": "invalid_action",
            "value": True
        }
        
        assert engine._validate_action(invalid_action) is False
    
    def test_validate_action_missing_value(self):
        """Test validating action with missing value"""
        engine = RuleEngine()
        
        invalid_action = {
            "type": "mark_read"
            # Missing 'value' field
        }
        
        assert engine._validate_action(invalid_action) is False
    
    @pytest.mark.asyncio
    async def test_evaluate_string_condition_contains(self, sample_email):
        """Test evaluating string condition with 'Contains' predicate"""
        engine = RuleEngine()
        
        condition = {
            "field": "From",
            "predicate": "Contains",
            "value": "test"
        }
        
        result = await engine.evaluate_condition(condition, sample_email)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_evaluate_string_condition_does_not_contain(self, sample_email):
        """Test evaluating string condition with 'Does not Contain' predicate"""
        engine = RuleEngine()
        
        condition = {
            "field": "From",
            "predicate": "Does not Contain",
            "value": "spam"
        }
        
        result = await engine.evaluate_condition(condition, sample_email)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_evaluate_string_condition_equals(self, sample_email):
        """Test evaluating string condition with 'Equals' predicate"""
        engine = RuleEngine()
        
        condition = {
            "field": "From",
            "predicate": "Equals",
            "value": "test@example.com"
        }
        
        result = await engine.evaluate_condition(condition, sample_email)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_evaluate_string_condition_does_not_equal(self, sample_email):
        """Test evaluating string condition with 'Does not equal' predicate"""
        engine = RuleEngine()
        
        condition = {
            "field": "From",
            "predicate": "Does not equal",
            "value": "other@example.com"
        }
        
        result = await engine.evaluate_condition(condition, sample_email)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_evaluate_date_condition_less_than(self):
        """Test evaluating date condition with 'Less than' predicate"""
        engine = RuleEngine()
        
        # Create email with old date
        old_email = {
            'id': 'old_email',
            'from_address': 'test@example.com',
            'subject': 'Old email',
            'message': 'Old message',
            'received_date': (datetime.now() - timedelta(days=10)).isoformat(),
            'is_read': False,
            'labels': ['INBOX']
        }
        
        condition = {
            "field": "Received",
            "predicate": "Less than",
            "value": "7 days"
        }
        
        result = await engine.evaluate_condition(condition, old_email)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_evaluate_date_condition_greater_than(self):
        """Test evaluating date condition with 'Greater than' predicate"""
        engine = RuleEngine()
        
        # Create email with recent date
        recent_email = {
            'id': 'recent_email',
            'from_address': 'test@example.com',
            'subject': 'Recent email',
            'message': 'Recent message',
            'received_date': (datetime.now() - timedelta(days=2)).isoformat(),
            'is_read': False,
            'labels': ['INBOX']
        }
        
        condition = {
            "field": "Received",
            "predicate": "Greater than",
            "value": "7 days"
        }
        
        result = await engine.evaluate_condition(condition, recent_email)
        assert result is True  # Should be true because email is 2 days old, which is more recent than 7 days ago
    
    @pytest.mark.asyncio
    async def test_evaluate_rule_all_predicate(self, sample_email):
        """Test evaluating rule with 'All' predicate"""
        engine = RuleEngine()
        
        rule = {
            "predicate": "All",
            "conditions": [
                {
                    "field": "From",
                    "predicate": "Contains",
                    "value": "test"
                },
                {
                    "field": "Subject",
                    "predicate": "Contains",
                    "value": "important"
                }
            ],
            "actions": []
        }
        
        result = await engine.evaluate_rule(rule, sample_email)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_evaluate_rule_any_predicate(self, sample_email):
        """Test evaluating rule with 'Any' predicate"""
        engine = RuleEngine()
        
        rule = {
            "predicate": "Any",
            "conditions": [
                {
                    "field": "From",
                    "predicate": "Contains",
                    "value": "nonexistent"
                },
                {
                    "field": "Subject",
                    "predicate": "Contains",
                    "value": "important"
                }
            ],
            "actions": []
        }
        
        result = await engine.evaluate_rule(rule, sample_email)
        assert result is True  # Should be true because second condition matches
    
    @pytest.mark.asyncio
    async def test_evaluate_rule_no_conditions(self, sample_email):
        """Test evaluating rule with no conditions"""
        engine = RuleEngine()
        
        rule = {
            "predicate": "All",
            "conditions": [],
            "actions": []
        }
        
        result = await engine.evaluate_rule(rule, sample_email)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_matching_emails(self, sample_email):
        """Test getting matching emails for a rule"""
        engine = RuleEngine()
        
        rule = {
            "predicate": "All",
            "conditions": [
                {
                    "field": "From",
                    "predicate": "Contains",
                    "value": "test"
                }
            ],
            "actions": []
        }
        
        emails = [sample_email]
        matching = await engine.get_matching_emails(emails, rule)
        
        assert len(matching) == 1
        assert matching[0]['id'] == sample_email['id']
    
    @pytest.mark.asyncio
    async def test_process_emails(self, sample_email):
        """Test processing multiple emails with rules"""
        engine = RuleEngine()
        
        # Add a rule to the engine
        engine.rules = [
            {
                "predicate": "All",
                "conditions": [
                    {
                        "field": "From",
                        "predicate": "Contains",
                        "value": "test"
                    }
                ],
                "actions": []
            }
        ]
        
        emails = [sample_email]
        results = await engine.process_emails(emails)
        
        assert 'rule_1' in results
        assert results['rule_1']['count'] == 1
        assert len(results['rule_1']['matching_emails']) == 1
    
    def test_get_summary(self):
        """Test getting rule summary"""
        engine = RuleEngine()
        
        # Add rules to the engine
        engine.rules = [
            {
                "predicate": "All",
                "conditions": [
                    {
                        "field": "From",
                        "predicate": "Contains",
                        "value": "test"
                    }
                ],
                "actions": [
                    {
                        "type": "mark_read",
                        "value": True
                    }
                ]
            }
        ]
        
        summary = engine.get_summary()
        
        assert summary['total_rules'] == 1 