import json
from http.server import BaseHTTPRequestHandler
from .auth_utils import verify_token, get_bearer_token

ALLOWED_ORIGINS = [
    'https://eliaquimbrandao.github.io',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:3000',
    'http://127.0.0.1:3000'
]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        token = get_bearer_token(self.headers)
        payload = verify_token(token)
        if not payload:
            return self.send_json_response(401, {"success": False, "error": "Unauthorized"})
        plan = {
            "plan": payload.get('plan', 'free'),
            "plan_status": payload.get('plan_status', 'inactive'),
            "plan_expires_at": payload.get('plan_expires_at')
        }
        user = {"email": payload.get('email'), "user_id": payload.get('sub')}
        return self.send_json_response(200, {"success": True, "user": user, "plan": plan})

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
        if origin in ALLOWED_ORIGINS or origin == '*':
            self.send_header('Access-Control-Allow-Origin', origin)
        else:
            self.send_header('Access-Control-Allow-Origin', ALLOWED_ORIGINS[0])
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')
