"""
Rule engine for processing emails
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dateutil import parser
from config import (
    FIELD_MAPPING, STRING_PREDICATES, DATE_PREDICATES,
    ACTIONS
)

logger = logging.getLogger(__name__)

class RuleEngine:
    """Handles email rule processing"""
    
    def __init__(self, rules_file: str = 'rules.json'):
        self.rules_file = rules_file
        self.rules = []
        self._load_rules()
    
    def _load_rules(self):
        """Load rules from JSON file"""
        try:
            with open(self.rules_file, 'r') as f:
                data = json.load(f)
                
            # Handle both single rule and list of rules
            if isinstance(data, list):
                rules = data
            elif isinstance(data, dict):
                rules = [data]
            else:
                logger.error("Invalid rules format")
                self.rules = []
                return
            
            # Validate each rule
            valid_rules = []
            for rule in rules:
                if self._validate_rule(rule):
                    valid_rules.append(rule)
                else:
                    logger.warning(f"Invalid rule skipped: {rule}")
            
            self.rules = valid_rules
            logger.info(f"Loaded {len(valid_rules)} rules")
            
        except FileNotFoundError:
            logger.warning(f"Rules file {self.rules_file} not found")
            self.rules = []
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            self.rules = []
    
    def _validate_rule(self, rule: Dict[str, Any]) -> bool:
        """Check if a rule is valid"""
        try:
            # Check required fields
            required = ['predicate', 'conditions', 'actions']
            for field in required:
                if field not in rule:
                    logger.error(f"Missing field: {field}")
                    return False
            
            # Check predicate
            if rule['predicate'] not in ['All', 'Any']:
                logger.error(f"Invalid predicate: {rule['predicate']}")
                return False
            
            # Validate conditions
            if not isinstance(rule['conditions'], list):
                logger.error("Conditions must be a list")
                return False
            
            for condition in rule['conditions']:
                if not self._validate_condition(condition):
                    return False
            
            # Validate actions
            if not isinstance(rule['actions'], list):
                logger.error("Actions must be a list")
                return False
            
            for action in rule['actions']:
                if not self._validate_action(action):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Rule validation error: {e}")
            return False
    
    def _validate_condition(self, condition: Dict[str, Any]) -> bool:
        """Validate a condition"""
        try:
            required = ['field', 'predicate', 'value']
            for field in required:
                if field not in condition:
                    logger.error(f"Missing condition field: {field}")
                    return False
            
            # Check field
            if condition['field'] not in FIELD_MAPPING:
                logger.error(f"Unknown field: {condition['field']}")
                return False
            
            # Check predicate based on field type
            field_name = condition['field']
            predicate = condition['predicate']
            
            if field_name == 'Received':
                if predicate not in DATE_PREDICATES:
                    logger.error(f"Invalid date predicate: {predicate}")
                    return False
            else:
                if predicate not in STRING_PREDICATES:
                    logger.error(f"Invalid string predicate: {predicate}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Condition validation error: {e}")
            return False
    
    def _validate_action(self, action: Dict[str, Any]) -> bool:
        """Validate an action"""
        try:
            if 'type' not in action:
                logger.error("Action missing 'type' field")
                return False
            
            if action['type'] not in ACTIONS:
                logger.error(f"Unknown action: {action['type']}")
                return False
            
            # Check action-specific requirements
            if action['type'] == 'mark_read':
                if 'value' not in action:
                    logger.error("mark_read missing 'value' field")
                    return False
                if not isinstance(action['value'], bool):
                    logger.error("mark_read value must be boolean")
                    return False
            
            elif action['type'] == 'mark_unread':
                # mark_unread doesn't need a value field, it's a simple action
                pass
            
            elif action['type'] == 'move_message':
                if 'value' not in action:
                    logger.error("move_message missing 'value' field")
                    return False
                if not isinstance(action['value'], str):
                    logger.error("move_message value must be string")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Action validation error: {e}")
            return False
    
    async def evaluate_condition(self, condition: Dict[str, Any], email: Dict[str, Any]) -> bool:
        """Check if an email matches a condition"""
        try:
            field_name = condition['field']
            predicate = condition['predicate']
            value = condition['value']
            
            # Get email field value
            db_field = FIELD_MAPPING.get(field_name)
            if not db_field:
                logger.error(f"Unknown field: {field_name}")
                return False
            
            email_value = email.get(db_field, '')
            
            # Handle date field
            if field_name == 'Received':
                return await self._check_date_condition(email_value, predicate, value)
            else:
                return await self._check_string_condition(email_value, predicate, value)
                
        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            return False
    
    async def _check_string_condition(self, email_value: str, predicate: str, value: str) -> bool:
        """Check string-based conditions"""
        try:
            email_value = str(email_value).lower()
            value = str(value).lower()
            
            if predicate == 'Contains':
                return value in email_value
            elif predicate == 'Does not Contain':
                return value not in email_value
            elif predicate == 'Equals':
                return email_value == value
            elif predicate == 'Does not equal':
                return email_value != value
            else:
                logger.error(f"Unknown string predicate: {predicate}")
                return False
                
        except Exception as e:
            logger.error(f"String condition error: {e}")
            return False
    
    async def _check_date_condition(self, email_date: str, predicate: str, value: str) -> bool:
        """Check date-based conditions"""
        try:
            # Parse email date
            if isinstance(email_date, str):
                email_datetime = parser.parse(email_date)
            else:
                email_datetime = email_date
            
            # Parse comparison value (e.g., "7 days", "2 months")
            parts = value.split()
            if len(parts) != 2:
                logger.error(f"Invalid date format: {value}")
                return False
            
            try:
                number = int(parts[0])
                unit = parts[1].lower()
            except ValueError:
                logger.error(f"Invalid number: {parts[0]}")
                return False
            
            # Calculate comparison date
            if unit in ['day', 'days']:
                comparison_date = datetime.now() - timedelta(days=number)
            elif unit in ['month', 'months']:
                # Approximate months
                comparison_date = datetime.now() - timedelta(days=number * 30)
            else:
                logger.error(f"Unknown date unit: {unit}")
                return False
            
            if predicate == 'Less than':
                return email_datetime < comparison_date
            elif predicate == 'Greater than':
                return email_datetime > comparison_date
            else:
                logger.error(f"Unknown date predicate: {predicate}")
                return False
                
        except Exception as e:
            logger.error(f"Date condition error: {e}")
            return False
    
    async def evaluate_rule(self, rule: Dict[str, Any], email: Dict[str, Any]) -> bool:
        """Check if an email matches a rule"""
        try:
            predicate = rule['predicate']
            conditions = rule['conditions']
            
            if not conditions:
                return False
            
            results = []
            for condition in conditions:
                result = await self.evaluate_condition(condition, email)
                results.append(result)
            
            # Apply overall predicate
            if predicate == 'All':
                return all(results)
            elif predicate == 'Any':
                return any(results)
            else:
                logger.error(f"Unknown predicate: {predicate}")
                return False
                
        except Exception as e:
            logger.error(f"Rule evaluation error: {e}")
            return False
    
    async def get_matching_emails(self, emails: List[Dict[str, Any]], rule: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get emails that match a rule"""
        matching = []
        
        for email in emails:
            if await self.evaluate_rule(rule, email):
                matching.append(email)
        
        return matching
    
    async def process_emails(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process emails against all rules"""
        results = {}
        
        for i, rule in enumerate(self.rules):
            rule_name = f"rule_{i+1}"
            matching = await self.get_matching_emails(emails, rule)
            results[rule_name] = {
                'rule': rule,
                'matching_emails': matching,
                'count': len(matching)
            }
        
        return results
    
    def reload_rules(self):
        """Reload rules from file"""
        self._load_rules()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of loaded rules"""
        summary = {
            'total_rules': len(self.rules),
            'rules': []
        }
        
        for i, rule in enumerate(self.rules):
            rule_info = {
                'id': i + 1,
                'predicate': rule['predicate'],
                'conditions_count': len(rule['conditions']),
                'actions_count': len(rule['actions']),
                'conditions': rule['conditions'],
                'actions': rule['actions']
            }
            summary['rules'].append(rule_info)
        
        return summary 