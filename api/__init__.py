"""
API module for Azure Service Tags Tracker
Handles subscription management and email notifications.
"""

from .db_config import db_config, DatabaseConfig
from .subscription_manager import SubscriptionManager
from .email_service import EmailService

__all__ = ['db_config', 'DatabaseConfig', 'SubscriptionManager', 'EmailService']
