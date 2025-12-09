import json
from http.server import BaseHTTPRequestHandler
from .user_manager import user_manager
from .auth_utils import create_token

ALLOWED_ORIGINS = [
    'https://eliaquimbrandao.github.io',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:3000',
    'http://127.0.0.1:3000'
]

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length) if length else b''
            data = json.loads(body.decode('utf-8')) if body else {}
            email = (data.get('email') or '').strip().lower()
            password = data.get('password') or ''
            result = user_manager.create_user(email, password)
            if result.get('success'):
                plan = user_manager.get_plan(email)
                token = create_token(result['user'], plan)
                return self.send_json_response(200, {"success": True, "token": token, "plan": plan})
            else:
                return self.send_json_response(400, {"success": False, "error": result.get('error'), "code": result.get('code')})
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
        if origin in ALLOWED_ORIGINS or origin == '*':
            self.send_header('Access-Control-Allow-Origin', origin)
        else:
            self.send_header('Access-Control-Allow-Origin', ALLOWED_ORIGINS[0])
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')
