"""
Subscription Management API
Handles CRUD operations for email subscriptions in MongoDB Atlas.
"""

import secrets
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from pymongo.errors import DuplicateKeyError
from .db_config import db_config


class SubscriptionManager:
    """Manage email subscriptions in MongoDB"""
    
    def __init__(self):
        self.collection = db_config.get_collection('subscriptions')
    
    @staticmethod
    def generate_subscription_id():
        """Generate unique subscription ID"""
        return f"sub_{secrets.token_hex(16)}"
    
    @staticmethod
    def generate_unsubscribe_token():
        """Generate secure 64-character unsubscribe token"""
        return secrets.token_hex(32)
    
    @staticmethod
    def hash_email(email: str) -> str:
        """Hash email for privacy (optional, for analytics)"""
        return hashlib.sha256(email.lower().encode()).hexdigest()
    
    def create_subscription(self, subscription_data: Dict) -> Dict:
        """
        Create new subscription in database
        
        Args:
            subscription_data: {
                'email': str,
                'subscriptionType': 'all' | 'filtered',
                'selectedServices': List[str],
                'selectedRegions': List[str]
            }
        
        Returns:
            Dict with subscription details or error
        """
        try:
            email = subscription_data.get('email', '').lower().strip()
            
            # Check if email already subscribed
            if self.is_email_subscribed(email):
                return {
                    'success': False,
                    'error': 'Email already subscribed',
                    'code': 'DUPLICATE_EMAIL'
                }
            
            # Prepare subscription document
            subscription = {
                'id': self.generate_subscription_id(),
                'email': email,
                'email_hash': self.hash_email(email),  # For analytics without exposing emails
                'subscriptionType': subscription_data.get('subscriptionType', 'all'),
                'selectedServices': subscription_data.get('selectedServices', []),
                'selectedRegions': subscription_data.get('selectedRegions', []),
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'active',
                'unsubscribe_token': self.generate_unsubscribe_token(),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Insert into database
            result = self.collection.insert_one(subscription)
            
            if result.inserted_id:
                return {
                    'success': True,
                    'subscription': {
                        'id': subscription['id'],
                        'email': subscription['email'],
                        'unsubscribe_token': subscription['unsubscribe_token'],
                        'timestamp': subscription['timestamp']
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create subscription'
                }
                
        except DuplicateKeyError:
            return {
                'success': False,
                'error': 'Subscription already exists',
                'code': 'DUPLICATE_KEY'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Database error: {str(e)}'
            }
    
    def is_email_subscribed(self, email: str) -> bool:
        """Check if email is already subscribed and active"""
        email = email.lower().strip()
        existing = self.collection.find_one({
            'email': email,
            'status': 'active'
        })
        return existing is not None
    
    def get_subscription(self, email: str = None, token: str = None) -> Optional[Dict]:
        """Get subscription by email or token"""
        query = {}
        
        if email:
            query['email'] = email.lower().strip()
        if token:
            query['unsubscribe_token'] = token
        
        if not query:
            return None
        
        return self.collection.find_one(query)
    
    def unsubscribe(self, email: str, token: str) -> Dict:
        """
        Unsubscribe user by email and token validation
        
        Args:
            email: User's email address
            token: Unsubscribe token from email link
        
        Returns:
            Dict with success status
        """
        try:
            email = email.lower().strip()
            
            # Find subscription
            subscription = self.collection.find_one({
                'email': email,
                'unsubscribe_token': token,
                'status': 'active'
            })
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Invalid unsubscribe link or subscription not found'
                }
            
            # Update status to unsubscribed
            result = self.collection.update_one(
                {'_id': subscription['_id']},
                {
                    '$set': {
                        'status': 'unsubscribed',
                        'unsubscribed_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                return {
                    'success': True,
                    'message': 'Successfully unsubscribed'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to update subscription status'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Database error: {str(e)}'
            }
    
    def get_active_subscriptions(self, filters: Dict = None) -> List[Dict]:
        """
        Get all active subscriptions with optional filtering
        
        Args:
            filters: Optional filters (e.g., {'subscriptionType': 'filtered'})
        
        Returns:
            List of active subscription documents
        """
        query = {'status': 'active'}
        
        if filters:
            query.update(filters)
        
        return list(self.collection.find(query).sort('created_at', -1))
    
    def get_filtered_subscriptions(self, service_name: str = None, region: str = None) -> List[Dict]:
        """
        Get subscriptions filtered by service or region
        
        Args:
            service_name: Azure service name to filter by
            region: Azure region to filter by
        
        Returns:
            List of matching subscriptions
        """
        query = {
            'status': 'active',
            'subscriptionType': 'filtered'
        }
        
        if service_name:
            query['selectedServices'] = service_name
        
        if region:
            query['selectedRegions'] = region
        
        return list(self.collection.find(query))
    
    def get_statistics(self) -> Dict:
        """Get subscription statistics"""
        try:
            total = self.collection.count_documents({})
            active = self.collection.count_documents({'status': 'active'})
            unsubscribed = self.collection.count_documents({'status': 'unsubscribed'})
            all_changes = self.collection.count_documents({
                'status': 'active',
                'subscriptionType': 'all'
            })
            filtered = self.collection.count_documents({
                'status': 'active',
                'subscriptionType': 'filtered'
            })
            
            return {
                'total_subscriptions': total,
                'active_subscriptions': active,
                'unsubscribed': unsubscribed,
                'all_changes_subscribers': all_changes,
                'filtered_subscribers': filtered
            }
        except Exception as e:
            return {'error': str(e)}
