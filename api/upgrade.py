"""
Serverless API endpoint to start an upgrade flow.
For now, this is a stub that returns an error until Stripe is configured.
"""

import json
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8')) if body else {}
            email = (data.get('email') or '').strip().lower()
            if not email:
                return self.send_json_response(400, {'success': False, 'error': 'Email is required'})

            # Stub: Stripe not configured yet
            return self.send_json_response(200, {
                'success': False,
                'error': 'Upgrade is not yet configured. Stripe checkout URL unavailable.'
            })
        except Exception as e:
            return self.send_json_response(500, {'success': False, 'error': str(e)})

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
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
