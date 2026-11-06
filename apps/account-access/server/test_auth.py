import http.client, importlib.util, json, os, tempfile, threading, unittest
from pathlib import Path
from http.server import ThreadingHTTPServer

class AuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        os.environ['PATHWAYS_DB'] = str(Path(cls.temp.name) / 'auth.sqlite')
        spec = importlib.util.spec_from_file_location('pathways_auth', Path(__file__).with_name('auth.py'))
        cls.auth = importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.auth)
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), cls.auth.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.temp.cleanup()
    def setUp(self):
        with self.auth.connect() as db:
            for table in ('users','sessions','attempts'): db.execute('DELETE FROM '+table)
    def request(self, path, data=None, cookie='', origin='http://localhost:5173'):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        headers = {'Origin':origin,'Cookie':cookie}
        if data is not None: headers['Content-Type']='application/json'
        conn.request('POST' if data is not None else 'GET', '/api/'+path, json.dumps(data) if data is not None else None, headers)
        response=conn.getresponse(); result=(response.status,json.loads(response.read()),response.getheader('Set-Cookie')); conn.close(); return result
    def signup(self):
        return self.request('signup', {'name':'Test Student','email':'Student@Example.edu','password':'test-password-927!'})
    def test_account_persistence_and_hashed_storage(self):
        status, body, cookie=self.signup(); self.assertEqual(status,200); self.assertEqual(body['user']['email'],'student@example.edu')
        with self.auth.connect() as db:
            row=db.execute('SELECT hash,salt FROM users').fetchone()
        self.assertNotIn('test-password',row[0]); self.assertEqual(len(row[1]),32)
        self.assertIn('HttpOnly',cookie); self.assertIn('SameSite=Strict',cookie)
        self.assertEqual(self.request('session',cookie=cookie)[1],body)
    def test_login_logout_and_session_revocation(self):
        self.signup()
        status, body, cookie=self.request('login',{'email':'student@example.edu','password':'test-password-927!'})
        self.assertEqual(status,200); self.assertEqual(body['user']['name'],'Test Student')
        self.assertEqual(self.request('logout',{},cookie)[0],200)
        self.assertIsNone(self.request('session',cookie=cookie)[1]['user'])
    def test_wrong_and_unknown_credentials(self):
        self.signup()
        wrong=self.request('login',{'email':'student@example.edu','password':'wrong'})
        unknown=self.request('login',{'email':'nobody@example.edu','password':'wrong'})
        self.assertEqual(wrong[:2],unknown[:2]); self.assertEqual(wrong[0],401)
    def test_validation_and_duplicate(self):
        self.assertEqual(self.request('signup',{'name':'Test','email':'bad','password':'short'})[0],400)
        self.signup(); self.assertEqual(self.signup()[0],409)
    def test_cross_origin_rejected(self):
        self.assertEqual(self.request('signup',{},origin='https://other.example')[0],403)
    def test_expired_session(self):
        _,_,cookie=self.signup()
        with self.auth.connect() as db: db.execute('UPDATE sessions SET expires=0')
        self.assertIsNone(self.request('session',cookie=cookie)[1]['user'])
    def test_rate_limit(self):
        with self.auth.connect() as db:
            db.executemany('INSERT INTO attempts VALUES (?,?)',[('127.0.0.1',int(self.auth.time.time()))]*15)
        self.assertEqual(self.request('login',{'email':'a@example.edu','password':'wrong'})[0],429)
if __name__ == '__main__': unittest.main()
