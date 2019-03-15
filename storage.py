
import os
import sqlite3
import random
import json
import datetime

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

    DB_VERSION = 1

    option_encrypt_credentials = True

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
        if isinstance(text, (bytes, bytearray)):
            return self.cipher.decrypt(text).decode("utf-8")
        else:
            return text

    def exists(self, username):
        return os.path.exists(os.path.join('userdata', username + '.db'))

    def _update_tables(self, conn):
        # Create table to store user data
        c = conn.cursor()
        sql = '''
            CREATE TABLE IF NOT EXISTS users (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        username TEXT NOT NULL,
                                        password_hash TEXT,
                                        salt1 TEXT,
                                        salt2 TEXT,
                                        db_version INTEGER NOT NULL
                                    );
        '''
        c.execute(sql)
        sql = '''
            CREATE TABLE IF NOT EXISTS providers (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        name TEXT NOT NULL,
                                        data TEXT,
                                        last_login TIMESTAMP
                                    );
        '''
        c.execute(sql)
        sql = '''
            CREATE TABLE IF NOT EXISTS accounts (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        name TEXT NOT NULL,
                                        currency TEXT NOT NULL,
                                        balance REAL,
                                        last_update TIMESTAMP,
                                        fk_provider INTEGER,
                                        FOREIGN KEY(fk_provider) REFERENCES providers(id)
                                    );
        '''
        c.execute(sql)
        sql = '''
            CREATE TABLE IF NOT EXISTS transactions (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        description TEXT NOT NULL,
                                        type TEXT NOT NULL,
                                        amount REAL,
                                        date TEXT,
                                        added TIMESTAMP,
                                        fk_account INTEGER,
                                        FOREIGN KEY(fk_account) REFERENCES accounts(id)
                                    );
        '''
        c.execute(sql)

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
        self._update_tables(conn)

        # Create one row in user table
        sql = ''' 
            INSERT INTO users(username,password_hash,salt1,salt2,db_version)
              VALUES(?,?,?,?,?) '''
        cur = conn.cursor()
        ret = cur.execute(sql, (username,password_hash,salt1,salt2,self.DB_VERSION))

        conn.commit()
                
        self.conn = conn
        self.cipher = _cipher_from_password(password,bytes.fromhex(salt2))

    def open(self, username, password):

        self.conn = None
        self.cipher = None

        db_file = os.path.join('userdata', username + '.db')
        conn = sqlite3.connect(db_file)

        # Update DB if the tables have changed
        self._update_tables(conn)

        # Validate password with salt
        cur = conn.cursor()
        cur.execute("SELECT salt1,salt2,password_hash FROM users WHERE username=?", (username,))
        row = cur.fetchone()

        if not row:
            raise Exception('Database error, user not found')

        salt1 = row[0]
        salt2 = row[1]

        if not row[2] == _sha1hash('%s%s' % (salt1,password)):
            raise Exception('Wrong password')

        self.conn = conn
        self.cipher = _cipher_from_password(password,bytes.fromhex(salt2))

    def add_provider(self, name, data):
        cur = self.conn.cursor()
        sql = ''' 
            INSERT INTO providers(name,data,last_login)
              VALUES(?,?,?) '''
        data = json.dumps(data)
        if self.option_encrypt_credentials:
            data = self._encrypt(data)
        ret = cur.execute(sql, (name,data,datetime.datetime.now()))

        self.conn.commit()

    def update_provider(self, id, data):
        cur = self.conn.cursor()
        sql = ''' 
            UPDATE providers SET data=?,last_login=? WHERE id=? '''
        encrypted_data = self._encrypt(json.dumps(data))
        ret = cur.execute(sql, (encrypted_data,datetime.datetime.now(),id))

        self.conn.commit()

    def registered_provider_list(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id,name,data FROM providers")
        rows = cur.fetchall()
        # [print(row) for row in rows] # DEBUG
        return [(row[0], row[1], json.loads(self._decrypt(row[2]))) for row in rows]

    def get_account_id(self, provider_id, uid):
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM accounts WHERE fk_provider=? AND name=?", (provider_id, uid))
        row = cur.fetchone()
        if row:
            return row[0]

    def update_account(self, account_id, data):

        # TODO Update account data ?

        cur = self.conn.cursor()
        sql = ''' 
            UPDATE accounts SET last_update=? WHERE id=? '''
        ret = cur.execute(sql, (datetime.datetime.now(),account_id))

        self.conn.commit()

    def create_account(self, provider_id, uid, data):

        currency = data.get('currency', '')
        balance = data.get('balance', 0.0)

        cur = self.conn.cursor()
        sql = ''' 
            INSERT INTO accounts(name,last_update,fk_provider,currency,balance)
              VALUES(?,?,?,?,?) '''
        ret = cur.execute(sql, (uid,datetime.datetime.now(),provider_id, currency, balance))

        self.conn.commit()

        return cur.lastrowid

    def find_transaction(self, account_id, data):

        description = data.get('description', '')
        ttype = data.get('type', 'unknown')
        amount = data.get('amount', 0.0)
        date = data.get('date', 'unknown')

        cur = self.conn.cursor()
        cur.execute("SELECT id FROM transactions WHERE fk_account=? AND description=? AND type=? AND amount=? AND date=?", 
            (account_id,description,ttype,amount,date))
        row = cur.fetchone()
        if row:
            print('DEBUG Found existing transaction %d' % row[0])
            return row[0]

    def add_transaction(self, account_id, data):

        description = data.get('description', '')
        ttype = data.get('type', 'unknown')
        amount = data.get('amount', 0.0)
        date = data.get('date', 'unknown')

        cur = self.conn.cursor()
        sql = ''' 
            INSERT INTO transactions (description,type,amount,date,added,fk_account)
              VALUES(?,?,?,?,?,?) '''
        ret = cur.execute(sql, (description,ttype,amount,date,datetime.datetime.now(),account_id))

        self.conn.commit()

        print('DEBUG Adding transaction as %d' % cur.lastrowid)

        return cur.lastrowid
