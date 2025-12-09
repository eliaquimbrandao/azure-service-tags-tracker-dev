"""
Plan status endpoint.
Sources plan from authenticated user (JWT) or email lookup.
"""

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from api.user_manager import user_manager
from api.auth_utils import verify_token, get_bearer_token


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            token = get_bearer_token(self.headers)
            payload = verify_token(token)

            # If authenticated, return plan from token (source of truth is users collection)
            if payload:
                plan = {
                    'plan': payload.get('plan', 'free'),
                    'plan_status': payload.get('plan_status', 'inactive'),
                    'plan_expires_at': payload.get('plan_expires_at')
                }
                return self.send_json_response(200, {'success': True, 'plan': plan, 'auth': True})

            # Fallback: email query for backward compatibility
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            email = params.get('email', [''])[0].lower().strip()
            if not email:
                return self.send_json_response(400, {'success': False, 'error': 'Email is required or login required'})

            plan = user_manager.get_plan(email)
            return self.send_json_response(200, {'success': True, 'plan': plan, 'auth': False})
        except Exception as e:
            return self.send_json_response(500, {'success': False, 'error': str(e)})

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
            'http://127.0.0.1:8000',
            'http://localhost:3000',
            'http://127.0.0.1:3000'
        ]
        if origin in allowed_origins or origin == '*':
            self.send_header('Access-Control-Allow-Origin', origin)
        else:
            self.send_header('Access-Control-Allow-Origin', allowed_origins[0])
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')
