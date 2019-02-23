
import os
import sqlite3
import random

def _cipher_from_password(password, salt):
    import base64
    from cryptography.fernet import Fernet
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
    return Fernet(key)

def _sha1hash(s):
    import hashlib
    return hashlib.sha1(s.encode('utf-8')).hexdigest()

class UserData():
    def __init__(self):
        self.conn = None
        self.cipher = None

    def _encrypt(self, text):
        if not self.cipher:
            raise Exception('No Cipher')
        return self.cipher.encrypt(text.encode('utf-8'))

    def _decrypt(self, text):
        if not self.cipher:
            raise Exception('No Cipher')
        return self.cipher.decrypt(text).decode("utf-8")

    def exists(self, username):
        return os.path.exists(os.path.join('userdata', username + '.db'))

    def create(self, username, password):

        self.conn = None
        self.cipher = None

        if len(password)<6:
            raise Exception('Password too short')

        if not os.path.exists('userdata'):
            os.makedirs('userdata')

        db_file = os.path.join('userdata', username + '.db')

        if os.path.exists(db_file):
            raise Exception('Database file already exists')

        # Generate salt and password hash
        salt1 = _sha1hash(str(random.random()))
        salt2 = _sha1hash(str(random.random()))
        password_hash = _sha1hash('%s%s' % (salt1,password))

        # Create database
        conn = sqlite3.connect(db_file)

        # Create table to store user data
        create_table_sql = '''
            CREATE TABLE IF NOT EXISTS users (
                                        id integer PRIMARY KEY,
                                        username text NOT NULL,
                                        password_hash text,
                                        salt1 text,
                                        salt2 text
                                    );
        '''
        c = conn.cursor()
        c.execute(create_table_sql)

        # Create one row in user table
        sql = ''' 
            INSERT INTO users(username,password_hash,salt1,salt2)
              VALUES(?,?,?,?) '''
        cur = conn.cursor()
        ret = cur.execute(sql, (username,password_hash,salt1,salt2))

        conn.commit()
                
        self.conn = conn
        self.cipher = _cipher_from_password(password,bytes.fromhex(salt2))

    def open(self, username, password):

        self.conn = None
        self.cipher = None

        db_file = os.path.join('userdata', username + '.db')
        conn = sqlite3.connect(db_file)

        # Validate password with salt
        cur = conn.cursor()
        cur.execute("SELECT salt1,salt2,password_hash FROM users WHERE username=?", (username,))
        row = cur.fetchone()

        salt1 = row[0]
        salt2 = row[1]

        if not row[2] == _sha1hash('%s%s' % (salt1,password)):
            raise Exception('Wrong password')

        self.conn = conn
        self.cipher = _cipher_from_password(password,bytes.fromhex(salt2))

