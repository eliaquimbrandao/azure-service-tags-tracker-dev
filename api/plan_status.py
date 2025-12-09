"""
Serverless API endpoint to return plan status for an email.
Deploy on Vercel: /api/plan_status
"""

import json
from http.server import BaseHTTPRequestHandler
from api.db_config import db_config
from api.subscription_manager import SubscriptionManager


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse query
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            email = params.get('email', [''])[0].lower().strip()

            if not email:
                return self.send_json_response(400, {'success': False, 'error': 'Email is required'})

            if not db_config.connect():
                return self.send_json_response(500, {'success': False, 'error': 'Database connection failed'})

            sub_manager = SubscriptionManager()
            plan = sub_manager.get_plan(email)

            return self.send_json_response(200, {
                'success': True,
                'plan': plan
            })
        except Exception as e:
            return self.send_json_response(500, {'success': False, 'error': str(e)})
        finally:
            db_config.close()

    # CORS preflight support
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def send_cors_headers(self):
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
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
