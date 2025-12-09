"""
Finalize premium upgrade via emailed magic link.
Requires token from /api/upgrade email and a password to set.
"""
import json
from http.server import BaseHTTPRequestHandler
from .auth_utils import verify_action_token, create_token
from .user_manager import user_manager


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length) if length else b''
            data = json.loads(body.decode('utf-8')) if body else {}
            token = data.get('token') or ''
            password = data.get('password') or ''

            payload = verify_action_token(token, 'upgrade')
            if not payload:
                return self.send_json_response(400, {"success": False, "error": "Invalid or expired link"})

            email = (payload.get('email') or '').strip().lower()
            result = user_manager.upsert_premium_with_password(email, password)
            if not result.get('success'):
                return self.send_json_response(400, {"success": False, "error": result.get('error', 'Unable to complete upgrade')})

            user = result['user']
            plan = user_manager.get_plan(email)
            session_token = create_token(user, plan)
            return self.send_json_response(200, {"success": True, "token": session_token, "plan": plan})
        except Exception as e:
            return self.send_json_response(500, {"success": False, "error": str(e)})

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
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
