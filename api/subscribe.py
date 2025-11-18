"""
Serverless API endpoint for creating subscriptions
Deploy on Vercel: /api/subscribe
"""

import json
import os
from http.server import BaseHTTPRequestHandler
from api.db_config import db_config
from api.subscription_manager import SubscriptionManager
from api.email_service import EmailService


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST request to create subscription"""
        try:
            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            # Connect to database
            if not db_config.connect():
                self.send_error_response(500, "Database connection failed")
                return
            
            # Create subscription
            sub_manager = SubscriptionManager()
            result = sub_manager.create_subscription(data)
            
            if result['success']:
                # Send confirmation email
                email_service = EmailService()
                email_service.send_confirmation_email(result['subscription'])
                
                # Return success response (without sensitive data)
                self.send_json_response(200, {
                    'success': True,
                    'message': 'Subscription created successfully',
                    'subscription': {
                        'email': result['subscription']['email'],
                        'timestamp': result['subscription']['timestamp']
                    }
                })
            else:
                self.send_json_response(400, result)
            
        except json.JSONDecodeError:
            self.send_error_response(400, "Invalid JSON")
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
        
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
