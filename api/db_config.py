"""
MongoDB Atlas Configuration
Handles secure database connections with error handling and retries.
"""

import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseConfig:
    """MongoDB Atlas database configuration and connection management"""
    
    def __init__(self):
        self.uri = os.getenv('MONGODB_URI')
        self.db_name = 'azure_tracker'
        self.collection_name = 'subscriptions'
        self.client = None
        self.db = None
        
        if not self.uri:
            raise ValueError("MONGODB_URI environment variable is not set")
    
    def connect(self):
        """Establish connection to MongoDB Atlas"""
        try:
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,
                retryWrites=True,
                w='majority',
                tls=True,
                tlsAllowInvalidCertificates=True  # For development only
            )
            
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            
            print(f"✅ Connected to MongoDB Atlas: {self.db_name}")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error connecting to MongoDB: {e}")
            return False
    
    def get_collection(self, collection_name=None):
        """Get collection reference"""
        if self.db is None:
            if not self.connect():
                raise ConnectionError("Cannot connect to database")
        
        col_name = collection_name or self.collection_name
        return self.db[col_name]
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print("🔌 Closed MongoDB connection")
    
    def create_indexes(self):
        """Create database indexes for performance"""
        try:
            collection = self.get_collection()
            
            # Index on email for fast lookups (unique for active subscriptions)
            collection.create_index([("email", 1), ("status", 1)])
            
            # Index on unsubscribe token for fast validation
            collection.create_index("unsubscribe_token", unique=True)
            
            # Index on timestamp for sorting
            collection.create_index("timestamp", -1)
            
            # Index on status for filtering
            collection.create_index("status")
            
            print("✅ Database indexes created")
            
        except Exception as e:
            print(f"⚠️ Error creating indexes: {e}")

# Global database instance
db_config = DatabaseConfig()
