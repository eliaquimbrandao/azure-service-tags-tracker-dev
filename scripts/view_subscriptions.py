"""
View all subscriptions in MongoDB
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api import db_config, SubscriptionManager

if __name__ == '__main__':
    print("\n" + "="*60)
    print("📊 Current Subscriptions in MongoDB")
    print("="*60 + "\n")
    
    if not db_config.connect():
        print("❌ Failed to connect to database")
        sys.exit(1)
    
    try:
        sm = SubscriptionManager()
        subs = sm.get_active_subscriptions()
        
        if not subs:
            print("No subscriptions found.\n")
        else:
            print(f"Found {len(subs)} subscription(s):\n")
            
            for i, sub in enumerate(subs, 1):
                print(f"{i}. Email: {sub['email']}")
                print(f"   Type: {sub['subscriptionType']}")
                print(f"   Status: {sub['status']}")
                print(f"   Created: {sub['timestamp']}")
                if sub.get('selectedServices'):
                    print(f"   Services: {len(sub['selectedServices'])} selected")
                if sub.get('selectedRegions'):
                    print(f"   Regions: {', '.join(sub['selectedRegions'][:3])}{'...' if len(sub['selectedRegions']) > 3 else ''}")
                print()
        
        # Show statistics
        stats = sm.get_statistics()
        print("-"*60)
        print(f"📈 Statistics:")
        print(f"   Total: {stats['total_subscriptions']}")
        print(f"   Active: {stats['active_subscriptions']}")
        print(f"   Unsubscribed: {stats['unsubscribed']}")
        print(f"   All changes: {stats['all_changes_subscribers']}")
        print(f"   Filtered: {stats['filtered_subscribers']}")
        print("="*60 + "\n")
        
    finally:
        db_config.close()
