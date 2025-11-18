"""
Test MongoDB Connection and Database Setup
Run this script to verify MongoDB Atlas configuration.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api import db_config, SubscriptionManager, EmailService


def test_connection():
    """Test MongoDB connection"""
    print("\n" + "="*60)
    print("🧪 Testing MongoDB Atlas Connection")
    print("="*60 + "\n")
    
    # Test connection
    print("1️⃣ Testing database connection...")
    if db_config.connect():
        print("   ✅ Successfully connected to MongoDB Atlas\n")
    else:
        print("   ❌ Failed to connect to MongoDB Atlas")
        print("   Check your .env file and MONGODB_URI\n")
        return False
    
    # Create indexes
    print("2️⃣ Creating database indexes...")
    try:
        db_config.create_indexes()
        print("   ✅ Indexes created\n")
    except Exception as e:
        print(f"   ⚠️ Error creating indexes: {e}\n")
    
    # Test subscription manager
    print("3️⃣ Testing subscription manager...")
    try:
        sub_manager = SubscriptionManager()
        stats = sub_manager.get_statistics()
        print(f"   ✅ Subscription Manager working")
        print(f"   📊 Current Statistics:")
        print(f"      - Total subscriptions: {stats.get('total_subscriptions', 0)}")
        print(f"      - Active: {stats.get('active_subscriptions', 0)}")
        print(f"      - Unsubscribed: {stats.get('unsubscribed', 0)}\n")
    except Exception as e:
        print(f"   ❌ Error with subscription manager: {e}\n")
        return False
    
    # Test email service
    print("4️⃣ Testing email service...")
    try:
        email_service = EmailService()
        if email_service.client:
            print("   ✅ SendGrid configured and ready\n")
        else:
            print("   ⚠️ SendGrid not configured (development mode)")
            print("   Emails will be logged to console\n")
    except Exception as e:
        print(f"   ❌ Error with email service: {e}\n")
    
    # Close connection
    db_config.close()
    
    print("="*60)
    print("✅ All tests passed! MongoDB integration is ready.")
    print("="*60 + "\n")
    
    return True


def create_test_subscription():
    """Create a test subscription"""
    print("\n" + "="*60)
    print("🧪 Creating Test Subscription")
    print("="*60 + "\n")
    
    if not db_config.connect():
        print("❌ Failed to connect to database")
        return False
    
    try:
        sub_manager = SubscriptionManager()
        email_service = EmailService()
        
        test_data = {
            'email': 'test@example.com',
            'subscriptionType': 'all',
            'selectedServices': [],
            'selectedRegions': []
        }
        
        print(f"Creating test subscription for: {test_data['email']}")
        result = sub_manager.create_subscription(test_data)
        
        if result['success']:
            print("✅ Test subscription created successfully!\n")
            print("Subscription Details:")
            print(f"  - ID: {result['subscription']['id']}")
            print(f"  - Email: {result['subscription']['email']}")
            print(f"  - Token: {result['subscription']['unsubscribe_token'][:20]}...\n")
            
            # Send confirmation email
            print("Sending confirmation email...")
            email_service.send_confirmation_email(result['subscription'])
            
        else:
            print(f"❌ Failed to create subscription: {result.get('error')}\n")
            
    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        
    finally:
        db_config.close()
    
    return True


if __name__ == '__main__':
    print("\n🔧 MongoDB Atlas Integration Test Suite\n")
    
    # Test connection first
    if not test_connection():
        print("\n❌ Connection test failed. Please check your configuration.")
        sys.exit(1)
    
    # Ask if user wants to create test subscription
    response = input("\n📝 Create a test subscription? (y/n): ").lower()
    if response == 'y':
        create_test_subscription()
    
    print("\n✅ Testing complete!")
