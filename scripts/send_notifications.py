"""
Send Email Notifications for Azure Service Tags Changes
Run this script when changes are detected to notify subscribers.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path so we can import api module
sys.path.insert(0, str(Path(__file__).parent.parent))

from api import db_config, SubscriptionManager, EmailService


def load_changes():
    """Load latest changes from JSON file"""
    changes_file = Path(__file__).parent.parent / 'docs' / 'data' / 'changes' / 'latest-changes.json'
    
    if not changes_file.exists():
        print("❌ No changes file found")
        return None
    
    with open(changes_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def send_notifications():
    """Send email notifications to all subscribers"""
    
    print("\n" + "="*60)
    print("📧 Azure Service Tags Change Notification System")
    print("="*60 + "\n")
    
    # Connect to database
    if not db_config.connect():
        print("❌ Failed to connect to database")
        return False
    
    try:
        # Load changes
        changes = load_changes()
        if not changes or not changes.get('changes'):
            print("ℹ️ No changes to notify about")
            return True
        
        print(f"📊 Found {len(changes['changes'])} service changes")
        
        # Get subscription manager
        sub_manager = SubscriptionManager()
        email_service = EmailService()
        
        # Get all active subscribers who want all changes
        all_subscribers = sub_manager.get_active_subscriptions({'subscriptionType': 'all'})
        
        # Get filtered subscribers (need to check if their services changed)
        filtered_subscribers = sub_manager.get_active_subscriptions({'subscriptionType': 'filtered'})
        
        # Collect recipients
        all_recipients = [sub['email'] for sub in all_subscribers]
        filtered_recipients = []
        
        # Check filtered subscribers
        changed_services = [change['service'] for change in changes['changes']]
        
        for sub in filtered_subscribers:
            selected_services = sub.get('selectedServices', [])
            # Check if any of their selected services changed
            if any(service in changed_services for service in selected_services):
                filtered_recipients.append(sub['email'])
        
        # Combine all recipients
        all_recipients.extend(filtered_recipients)
        all_recipients = list(set(all_recipients))  # Remove duplicates
        
        if not all_recipients:
            print("ℹ️ No active subscribers to notify")
            return True
        
        print(f"\n📬 Sending notifications to {len(all_recipients)} subscribers:")
        print(f"   - All changes: {len([sub['email'] for sub in all_subscribers])}")
        print(f"   - Filtered matches: {len(filtered_recipients)}")
        
        # Send notifications
        success = email_service.send_change_notification(all_recipients, changes)
        
        if success:
            print("\n✅ Notifications sent successfully!")
        else:
            print("\n⚠️ Notifications completed with warnings")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error sending notifications: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db_config.close()


if __name__ == '__main__':
    success = send_notifications()
    sys.exit(0 if success else 1)
