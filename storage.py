
import os
import sqlite3
import random

def sha1hash(s):
    import hashlib
    return hashlib.sha1(s.encode('utf-8')).hexdigest()

class UserData():
    def __init__(self):
        self.conn = None
        self.raw_pwd_hash = None

    def exists(self, username):
        return os.path.exists(os.path.join('userdata', username + '.db'))

    def create(self, username, password):

        if len(password)<6:
            raise Exception('Password too short')

        if not os.path.exists('userdata'):
            os.makedirs('userdata')

        db_file = os.path.join('userdata', username + '.db')

        if os.path.exists(db_file):
            raise Exception('Database file already exists')

        # Generate salt and password hash
        salt = sha1hash(str(random.random()))
        password_hash = sha1hash('%s%s' % (salt,password))

        # Create database
        conn = sqlite3.connect(db_file)

        # Create table to store user data
        create_table_sql = '''
            CREATE TABLE IF NOT EXISTS users (
                                        id integer PRIMARY KEY,
                                        username text NOT NULL,
                                        password_hash text,
                                        salt text
                                    );
        '''
        c = conn.cursor()
        c.execute(create_table_sql)

        # Create one row in user table
        sql = ''' 
            INSERT INTO users(username,password_hash,salt)
              VALUES(?,?,?) '''
        cur = conn.cursor()
        ret = cur.execute(sql, (username,password_hash,salt))

        conn.commit()
                
        self.conn = conn
        self.raw_pwd_hash = sha1hash(password)

    def open(self, username, password):

        db_file = os.path.join('userdata', username + '.db')
        conn = sqlite3.connect(db_file)

        # Validate password with salt
        cur = conn.cursor()
        cur.execute("SELECT salt,password_hash FROM users WHERE username=?", (username,))
        row = cur.fetchone()

        salt = row[0]

        if not row[1] == sha1hash('%s%s' % (salt,password)):
            raise Exception('Wrong password')

        self.conn = conn
        self.raw_pwd_hash = sha1hash(password)
