"""
Serverless API endpoint for unsubscribing
Deploy on Vercel: /api/unsubscribe
"""

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from api.db_config import db_config
from api.subscription_manager import SubscriptionManager


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST request to unsubscribe"""
        try:
            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            email = data.get('email')
            token = data.get('token')
            verify_token = data.get('verify')
            verify_only = data.get('verify_only', False)
            
            if not email:
                self.send_error_response(400, "Email is required")
                return
            
            # Connect to database
            if not db_config.connect():
                self.send_error_response(500, "Database connection failed")
                return
            
            sub_manager = SubscriptionManager()
            
            # If verify_only, just check if subscription exists (requires token)
            if verify_only:
                if not token:
                    self.send_error_response(400, "Token is required for verification")
                    return
                    
                subscription = sub_manager.get_subscription(email=email, token=token)
                if subscription and subscription['status'] == 'active':
                    self.send_json_response(200, {
                        'success': True,
                        'subscription': {
                            'email': subscription['email'],
                            'subscriptionType': subscription['subscriptionType'],
                            'selectedServices': subscription.get('selectedServices', []),
                            'timestamp': subscription['timestamp']
                        }
                    })
                else:
                    self.send_json_response(404, {
                        'success': False,
                        'error': 'Subscription not found or already unsubscribed'
                    })
                return
            
            # Handle unsubscribe with verification token (from email link)
            if verify_token:
                result = sub_manager.verify_and_unsubscribe(email, verify_token)
                if result['success']:
                    self.send_json_response(200, result)
                else:
                    self.send_json_response(400, result)
                return
            
            # Handle unsubscribe with permanent token (from original confirmation email)
            if token:
                result = sub_manager.unsubscribe(email, token)
                if result['success']:
                    self.send_json_response(200, result)
                else:
                    self.send_json_response(400, result)
                return
            
            # No token provided - this shouldn't happen with new flow
            self.send_error_response(400, "Verification token is required")
            
        except json.JSONDecodeError:
            self.send_error_response(400, "Invalid JSON")
        except Exception as e:
            self.send_error_response(500, str(e))
        finally:
            db_config.close()
    
    def do_GET(self):
        """Handle GET request to verify subscription"""
        try:
            # Parse query parameters
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            
            email = params.get('email', [None])[0]
            token = params.get('token', [None])[0]
            
            if not email or not token:
                self.send_error_response(400, "Email and token are required")
                return
            
            # Connect to database
            if not db_config.connect():
                self.send_error_response(500, "Database connection failed")
                return
            
            # Get subscription details
            sub_manager = SubscriptionManager()
            subscription = sub_manager.get_subscription(email=email, token=token)
            
            if subscription:
                self.send_json_response(200, {
                    'success': True,
                    'subscription': {
                        'email': subscription['email'],
                        'subscriptionType': subscription['subscriptionType'],
                        'status': subscription['status'],
                        'timestamp': subscription['timestamp']
                    }
                })
            else:
                self.send_json_response(404, {
                    'success': False,
                    'error': 'Subscription not found'
                })
            
        except Exception as e:
            self.send_error_response(500, str(e))
        finally:
            db_config.close()
    
    def do_OPTIONS(self):
        """Handle CORS preflight request"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def send_json_response(self, status_code, data):
        """Send JSON response with CORS headers"""
        self.send_response(status_code)
        self.send_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def send_error_response(self, status_code, message):
        """Send error response"""
        self.send_json_response(status_code, {
            'success': False,
            'error': message
        })
    
    def send_cors_headers(self):
        """Send CORS headers for GitHub Pages"""
        origin = self.headers.get('Origin', '*')
        allowed_origins = [
            'https://eliaquimbrandao.github.io',
            'http://localhost:8000',
            'http://127.0.0.1:8000'
        ]
        
        if origin in allowed_origins or origin == '*':
            self.send_header('Access-Control-Allow-Origin', origin)
        else:
            self.send_header('Access-Control-Allow-Origin', allowed_origins[0])
        
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
