"""
Send Email Notifications for Azure Service Tags Changes
Run this script when changes are detected to notify subscribers.
"""

import json
import sys
from pathlib import Path
from api import db_config, SubscriptionManager, EmailService


def load_changes():
    """Load latest changes from JSON file"""
    changes_file = Path(__file__).parent.parent / 'docs' / 'data' / 'changes' / 'latest-changes.json'
    summary_file = Path(__file__).parent.parent / 'docs' / 'data' / 'summary.json'
    
    if not changes_file.exists():
        print("❌ No changes file found")
        return None
    
    with open(changes_file, 'r', encoding='utf-8') as f:
        changes = json.load(f)

    # Attach summary regional breakdown so the email can match dashboard counts
    if summary_file.exists():
        try:
            with open(summary_file, 'r', encoding='utf-8') as sf:
                summary = json.load(sf)
            if isinstance(summary, dict) and 'regional_changes' in summary:
                changes['regional_changes'] = summary['regional_changes']
        except Exception:
            pass

    return changes


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

        # Collect recipients with their subscription context
        recipients = {}
        changed_services = [change['service'] for change in changes['changes']]

        for sub in all_subscribers:
            recipients[sub['email']] = {
                'email': sub['email'],
                'subscriptionType': 'all',
                'selectedServices': []
            }

        for sub in filtered_subscribers:
            selected_services = sub.get('selectedServices', [])
            # Check if any of their selected services changed
            if any(service in changed_services for service in selected_services):
                # If the same email is in both lists, prefer the filtered context
                recipients[sub['email']] = {
                    'email': sub['email'],
                    'subscriptionType': 'filtered',
                    'selectedServices': selected_services
                }

        recipients_list = list(recipients.values())

        if not recipients_list:
            print("ℹ️ No active subscribers to notify")
            return True
        
        print(f"\n📬 Sending notifications to {len(recipients_list)} subscribers:")
        print(f"   - All changes: {len(all_subscribers)}")
        print(f"   - Filtered matches: {len([r for r in recipients_list if r['subscriptionType']=='filtered'])}")
        
        # Send notifications
        success = email_service.send_change_notification(recipients_list, changes)
        
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
