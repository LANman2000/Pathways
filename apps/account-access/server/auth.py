"""Loopback-only development auth service. Not a production deployment server."""
import hashlib, hmac, json, os, re, secrets, sqlite3, time, sys, mimetypes
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from pathlib import Path
from contextlib import contextmanager
DB = Path(os.environ.get('PATHWAYS_DB', Path(__file__).parent / 'data' / 'accounts.sqlite'))
DB.parent.mkdir(parents=True, exist_ok=True)
os.chmod(DB.parent, 0o700)
@contextmanager
def connect():
    db = sqlite3.connect(DB)
    db.execute('CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, salt TEXT NOT NULL, hash TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS attempts (ip TEXT NOT NULL, at INTEGER NOT NULL)')
    try:
        with db: yield db
    finally:
        db.close()
with connect(): pass
os.chmod(DB, 0o600)
def derive(password, salt):
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=131072, r=8, p=1, maxmem=256*1024*1024).hex()
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def reply(self, status, data, cookie=None):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(body)))
        if cookie: self.send_header('Set-Cookie', cookie)
        self.end_headers(); self.wfile.write(body)
    def token(self):
        cookie = SimpleCookie()
        try: cookie.load(self.headers.get('Cookie', ''))
        except Exception: return ''
        token = cookie.get('pathways_session')
        return hashlib.sha256(token.value.encode()).hexdigest() if token else ''
    def proxy_analysis(self):
        content_type = self.headers.get('Content-Type', '')
        if not content_type.startswith('multipart/form-data;'):
            return self.reply(415, {'error':'Multipart form data required.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 20 * 1024 * 1024: raise ValueError()
        except ValueError:
            return self.reply(400, {'error':'Invalid request size.'})
        body = self.rfile.read(length)
        if len(body) != length:
            return self.reply(400, {'error':'Incomplete request body.'})
        connection = http.client.HTTPConnection(
            '127.0.0.1',
            int(os.environ.get('PATHWAYS_ANALYSIS_PORT', '5000')),
            timeout=120
        )
        try:
            connection.request(
                'POST',
                '/api/analyze',
                body=body,
                headers={
                    'Content-Type': content_type,
                    'Content-Length': str(length),
                    'Cookie': self.headers.get('Cookie', ''),
                }
            )
            response = connection.getresponse()
            response_body = response.read()
        except (OSError, http.client.HTTPException):
            return self.reply(503, {'error':'Analysis service is unavailable.'})
        finally:
            connection.close()
        if not response.getheader('Content-Type', '').startswith('application/json'):
            return self.reply(502, {'error':'Analysis service returned an invalid response.'})
        self.send_response(response.status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)
    def do_GET(self):
        if self.path != '/api/session':
            if '--serve' not in sys.argv or self.path.startswith('/api/'):
                return self.reply(404, {'error':'Not found.'})
            root = (Path(__file__).parent.parent / 'dist').resolve()
            path = (root / self.path.split('?')[0].lstrip('/')).resolve()
            if self.path == '/': path = root / 'index.html'
            if not path.is_relative_to(root) or not path.is_file():
                return self.reply(404, {'error':'Not found.'})
            content = path.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', mimetypes.guess_type(path)[0] or 'application/octet-stream')
            self.send_header('Content-Length', str(len(content)))
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers(); self.wfile.write(content)
            return
        with connect() as db:
            row = db.execute('SELECT u.name,u.email FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token=? AND s.expires>?', (self.token(), time.time())).fetchone()
        self.reply(200, {'user': {'name':row[0], 'email':row[1]} if row else None})
    def do_POST(self):
        if self.headers.get('Origin') not in ('http://localhost:5173', 'http://127.0.0.1:5173'):
            return self.reply(403, {'error':'Request not allowed.'})
        if self.path == '/api/analyze':
            return self.proxy_analysis()
        if self.headers.get('Content-Type') != 'application/json': return self.reply(415, {'error':'JSON required.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 4096: raise ValueError()
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict): raise ValueError()
        except (ValueError, json.JSONDecodeError): return self.reply(400, {'error':'Invalid request.'})
        if self.path == '/api/logout':
            with connect() as db: db.execute('DELETE FROM sessions WHERE token=?', (self.token(),))
            return self.reply(200, {}, 'pathways_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
        if self.path not in ('/api/signup','/api/login'): return self.reply(404, {'error':'Not found.'})
        email, password, name = data.get('email'), data.get('password'), data.get('name', '')
        if not isinstance(email, str) or not isinstance(password, str) or not isinstance(name, str): return self.reply(400, {'error':'Invalid fields.'})
        email, name = email.strip().lower(), name.strip()
        if len(email)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email) or not 1<=len(password)<=128:
            return self.reply(400, {'error':'Enter a valid email and password.'})
        if self.path == '/api/signup' and (not 1<=len(name)<=100 or len(password)<8): return self.reply(400, {'error':'Enter your name and a password with at least 8 characters.'})
        now = int(time.time())
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM attempts WHERE at<?', (now-600,))
            count = db.execute('SELECT count(*) FROM attempts WHERE ip=?', (self.client_address[0],)).fetchone()[0]
            if count >= 15: return self.reply(429, {'error':'Too many attempts. Please try again in 10 minutes.'})
            db.execute('INSERT INTO attempts VALUES (?,?)', (self.client_address[0], now))
        with connect() as db:
            if self.path == '/api/signup':
                salt, uid = secrets.token_hex(16), secrets.token_hex(16)
                hashed = derive(password, salt)
                try: db.execute('INSERT INTO users VALUES (?,?,?,?,?)', (uid,name,email,salt,hashed))
                except sqlite3.IntegrityError: return self.reply(409, {'error':'Unable to create this account. Try signing in instead.'})
            else:
                row = db.execute('SELECT id,name,salt,hash FROM users WHERE email=?', (email,)).fetchone()
                hashed = derive(password, row[2] if row else '0'*32)
                if not row or not hmac.compare_digest(hashed,row[3]): return self.reply(401, {'error':'Email or password is incorrect.'})
                uid, name = row[:2]
            token = secrets.token_urlsafe(32)
            db.execute('DELETE FROM sessions WHERE token=? OR expires<?', (self.token(), now))
            db.execute('INSERT INTO sessions VALUES (?,?,?)', (hashlib.sha256(token.encode()).hexdigest(),uid,now+28800))
        self.reply(200, {'user':{'name':name,'email':email}}, f'pathways_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800')
if __name__ == '__main__':
    port = 5173 if '--serve' in sys.argv else 5174
    print(f'Pathways local app: http://127.0.0.1:{port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
