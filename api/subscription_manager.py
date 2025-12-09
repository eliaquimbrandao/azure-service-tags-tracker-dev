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
from .user_manager import user_manager


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
    def generate_verification_token():
        """Generate temporary verification token for email confirmation"""
        return secrets.token_hex(32)
    
    @staticmethod
    def hash_email(email: str) -> str:
        """Hash email for privacy (optional, for analytics)"""
        return hashlib.sha256(email.lower().encode()).hexdigest()
    
    def create_subscription(self, subscription_data: Dict, auth_user: Dict = None) -> Dict:
        """
        Create new subscription or reactivate existing unsubscribed one
        
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
            
            # Determine requested type
            requested_type = subscription_data.get('subscriptionType', 'all')

            user_id = (subscription_data.get('user_id') or '').strip()

            # Check if email already has an active subscription
            if self.is_email_subscribed(email):
                return {
                    'success': False,
                    'error': 'Email already subscribed',
                    'code': 'DUPLICATE_EMAIL'
                }

            # Enforce premium for filtered subscriptions
            if requested_type == 'filtered':
                # Require authenticated user
                if not auth_user:
                    return {
                        'success': False,
                        'error': 'Login required for premium subscriptions',
                        'code': 'AUTH_REQUIRED'
                    }
                # Ensure email matches authenticated user
                auth_email = (auth_user.get('email') or '').lower().strip()
                if auth_email and auth_email != email:
                    return {
                        'success': False,
                        'error': 'Email must match logged-in user',
                        'code': 'EMAIL_MISMATCH'
                    }

                plan = self.get_plan(email)
                if not self._plan_allows_filtered(plan):
                    return {
                        'success': False,
                        'error': 'Premium required for filtered subscriptions',
                        'code': 'PREMIUM_REQUIRED'
                    }
                if not user_id:
                    # default to auth user id if provided
                    user_id = auth_user.get('sub') or auth_user.get('user_id')
                if not user_id:
                    return {
                        'success': False,
                        'error': 'User ID is required for premium subscriptions',
                        'code': 'MISSING_USER_ID'
                    }
            
            # Check if there's an unsubscribed record to reactivate
            existing = self.collection.find_one({
                'email': email,
                'status': 'unsubscribed'
            })
            
            if existing:
                # Reactivate existing subscription with updated preferences
                result = self.collection.update_one(
                    {'_id': existing['_id']},
                    {
                        '$set': {
                            'status': 'active',
                            'subscriptionType': requested_type,
                            'selectedServices': subscription_data.get('selectedServices', []),
                            'selectedRegions': subscription_data.get('selectedRegions', []),
                            'ip_queries': subscription_data.get('ip_queries', []),
                            'user_id': user_id or existing.get('user_id'),
                            'updated_at': datetime.utcnow(),
                            'resubscribed_at': datetime.utcnow()
                        },
                        '$unset': {
                            'unsubscribed_at': '',
                            'unsubscribe_method': ''
                        }
                    }
                )
                
                if result.modified_count > 0:
                    return {
                        'success': True,
                        'subscription': {
                            'id': existing['id'],
                            'email': existing['email'],
                            'unsubscribe_token': existing['unsubscribe_token'],
                            'timestamp': datetime.utcnow().isoformat(),
                            'reactivated': True
                        }
                    }
            
            # Create new subscription if no existing record
            subscription = {
                'id': self.generate_subscription_id(),
                'email': email,
                'email_hash': self.hash_email(email),  # For analytics without exposing emails
                'subscriptionType': requested_type,
                'selectedServices': subscription_data.get('selectedServices', []),
                'selectedRegions': subscription_data.get('selectedRegions', []),
                'ip_queries': subscription_data.get('ip_queries', []),
                'user_id': subscription_data.get('user_id'),
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'active',
                'unsubscribe_token': self.generate_unsubscribe_token(),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'plan': 'free',
                'plan_status': 'inactive',
                'plan_expires_at': None,
                'plan_source': None,
                'provider_customer_id': None,
                'provider_subscription_id': None
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

    def get_plan(self, email: str) -> Dict:
        """Return plan info for an email (defaults to free)."""
        email = email.lower().strip()
        # Plan of record now stored on users collection
        plan = user_manager.get_plan(email)
        if plan:
            return plan
        # Fallback for legacy data
        doc = self.collection.find_one({'email': email})
        if not doc:
            return {'plan': 'free', 'plan_status': 'inactive', 'plan_expires_at': None}
        return {
            'plan': doc.get('plan', 'free'),
            'plan_status': doc.get('plan_status', 'inactive'),
            'plan_expires_at': doc.get('plan_expires_at')
        }

    def _plan_allows_filtered(self, plan: Dict) -> bool:
        if not plan:
            return False
        return plan.get('plan') == 'premium' and plan.get('plan_status') == 'active'
    
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
    
    def create_unsubscribe_verification(self, email: str) -> Dict:
        """
        Create temporary verification token for unsubscribe request
        Token expires in 15 minutes
        
        Args:
            email: User's email address
        
        Returns:
            Dict with verification token and expiry time
        """
        try:
            email = email.lower().strip()
            
            # Check if subscription exists
            subscription = self.collection.find_one({
                'email': email,
                'status': 'active'
            })
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'No active subscription found for this email'
                }
            
            # Generate verification token with 15-minute expiry
            verification_token = self.generate_verification_token()
            expiry_time = datetime.utcnow()
            from datetime import timedelta
            expiry_time = expiry_time + timedelta(minutes=15)
            
            # Store verification token temporarily in subscription
            result = self.collection.update_one(
                {'_id': subscription['_id']},
                {
                    '$set': {
                        'unsubscribe_verification_token': verification_token,
                        'verification_token_expiry': expiry_time,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                return {
                    'success': True,
                    'email': email,
                    'verification_token': verification_token,
                    'expiry_time': expiry_time.isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create verification token'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Database error: {str(e)}'
            }
    
    def verify_and_unsubscribe(self, email: str, verification_token: str) -> Dict:
        """
        Verify token and unsubscribe user
        
        Args:
            email: User's email address
            verification_token: Temporary verification token
        
        Returns:
            Dict with success status
        """
        try:
            email = email.lower().strip()
            
            # Find subscription with valid verification token
            subscription = self.collection.find_one({
                'email': email,
                'unsubscribe_verification_token': verification_token,
                'status': 'active'
            })
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Invalid or expired verification link'
                }
            
            # Check if token has expired
            expiry_time = subscription.get('verification_token_expiry')
            if expiry_time and datetime.utcnow() > expiry_time:
                return {
                    'success': False,
                    'error': 'Verification link has expired. Please request a new one.'
                }
            
            # Unsubscribe user
            result = self.collection.update_one(
                {'_id': subscription['_id']},
                {
                    '$set': {
                        'status': 'unsubscribed',
                        'unsubscribed_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow(),
                        'unsubscribe_method': 'email_verification'
                    },
                    '$unset': {
                        'unsubscribe_verification_token': '',
                        'verification_token_expiry': ''
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
                    'error': 'Failed to unsubscribe'
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
        # Deprecated: filtered subscription lookups are handled client-side using
        # change payloads; keeping this signature documented for future API work.
        raise NotImplementedError("Filtered subscription lookup is no longer in use.")
    
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
