"""
User management for authentication and plan tracking.
"""
from datetime import datetime
from typing import Optional, Dict
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError

from .db_config import db_config
from .auth_utils import hash_password, verify_password


class UserManager:
    def __init__(self):
        self.collection = db_config.get_collection('users')
        self.premium_collection = db_config.get_collection('premium_accounts')
        self.ensure_indexes()

    def ensure_indexes(self):
        try:
            self.collection.create_index('email', unique=True)
            self.premium_collection.create_index('email', unique=True)
        except Exception:
            pass

    def create_user(self, email: str, password: str) -> Dict:
        email_norm = (email or '').strip().lower()
        if not email_norm:
            return {"success": False, "error": "Email is required"}
        if not password:
            return {"success": False, "error": "Password is required"}
        try:
            user = {
                "email": email_norm,
                "password_hash": hash_password(password),
                "plan": "free",
                "plan_status": "inactive",
                "plan_expires_at": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            res = self.collection.insert_one(user)
            user["_id"] = res.inserted_id
            return {"success": True, "user": user}
        except DuplicateKeyError:
            return {"success": False, "error": "Email already exists", "code": "DUPLICATE"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def authenticate(self, email: str, password: str) -> Dict:
        email_norm = (email or '').strip().lower()
        if not email_norm or not password:
            return {"success": False, "error": "Email and password are required"}
        user = self.collection.find_one({"email": email_norm})
        if not user:
            return {"success": False, "error": "Invalid credentials"}
        if not verify_password(password, user.get("password_hash", "")):
            return {"success": False, "error": "Invalid credentials"}
        return {"success": True, "user": user}

    def get_user(self, user_id: str) -> Optional[Dict]:
        try:
            return self.collection.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None

    def get_by_email(self, email: str) -> Optional[Dict]:
        return self.collection.find_one({"email": (email or '').strip().lower()})

    def get_plan(self, email: str) -> Dict:
        email_norm = (email or '').strip().lower()
        premium = self.premium_collection.find_one({"email": email_norm})
        if premium and premium.get("status", "inactive") == "active":
            return {
                "plan": premium.get("plan", "premium"),
                "plan_status": premium.get("status", "active"),
                "plan_expires_at": premium.get("plan_expires_at"),
            }
        user = self.get_by_email(email_norm)
        if not user:
            return {"plan": "free", "plan_status": "inactive", "plan_expires_at": None}
        return {
            "plan": user.get("plan", "free"),
            "plan_status": user.get("plan_status", "inactive"),
            "plan_expires_at": user.get("plan_expires_at"),
        }

    def upsert_premium_with_password(self, email: str, password: str) -> Dict:
        """
        Ensure a user exists, set password, and upgrade to premium.
        Returns dict with success and user/error.
        """
        email_norm = (email or '').strip().lower()
        if not email_norm:
            return {"success": False, "error": "Email is required"}
        if not password:
            return {"success": False, "error": "Password is required"}
        try:
            hashed = hash_password(password)
            now = datetime.utcnow()
            user = self.collection.find_one_and_update(
                {"email": email_norm},
                {
                    "$set": {
                        "password_hash": hashed,
                        "plan": "premium",
                        "plan_status": "active",
                        "plan_expires_at": None,
                        "updated_at": now,
                    },
                    "$setOnInsert": {
                        "created_at": now,
                    },
                },
                upsert=True,
                return_document=True,
            )
            # Mirror premium in dedicated collection
            self.premium_collection.find_one_and_update(
                {"email": email_norm},
                {
                    "$set": {
                        "plan": "premium",
                        "status": "active",
                        "plan_expires_at": None,
                        "updated_at": now,
                    },
                    "$setOnInsert": {
                        "created_at": now,
                    },
                },
                upsert=True,
                return_document=True,
            )
            return {"success": True, "user": user}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_premium_active(self, email: str, status: str = "active", expires_at=None) -> Dict:
        email_norm = (email or '').strip().lower()
        if not email_norm:
            return {"success": False, "error": "Email is required"}
        now = datetime.utcnow()
        try:
            doc = self.premium_collection.find_one_and_update(
                {"email": email_norm},
                {
                    "$set": {
                        "plan": "premium",
                        "status": status,
                        "plan_expires_at": expires_at,
                        "updated_at": now,
                    },
                    "$setOnInsert": {"created_at": now},
                },
                upsert=True,
                return_document=True,
            )
            return {"success": True, "premium": doc}
        except Exception as e:
            return {"success": False, "error": str(e)}


user_manager = UserManager()
