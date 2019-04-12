
import os
import sqlite3
import random
import json
import datetime

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days) + 1):
        yield start_date + datetime.timedelta(n)

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
                                        base_currency TEXT NOT NULL,
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
                                        bank_id TEXT NOT NULL,
                                        description TEXT,
                                        type TEXT,
                                        base_type TEXT NOT NULL DEFAULT 'savings',
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
                                        bank_id TEXT NOT NULL,
                                        description TEXT NOT NULL,
                                        type TEXT NOT NULL,
                                        amount REAL,
                                        date TIMESTAMP,
                                        added TIMESTAMP,
                                        data TEXT,
                                        fk_account INTEGER,
                                        uncleared INTEGER DEFAULT 0,
                                        FOREIGN KEY(fk_account) REFERENCES accounts(id)
                                    );
        '''
        # Some banks may report it with the transaction, otherwise we can calculate it after each update.
        c.execute(sql)

        sql = '''
            CREATE TABLE IF NOT EXISTS historical_balance (
                                        date TIMESTAMP NOT NULL,
                                        balance REAL,
                                        fk_account INTEGER NOT NULL,
                                        PRIMARY KEY (date, fk_account),
                                        FOREIGN KEY(fk_account) REFERENCES accounts(id)
                                    );
        '''
        c.execute(sql)

        sql = '''
            CREATE TABLE IF NOT EXISTS actions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        action TEXT NOT NULL,
                        created TIMESTAMP NOT NULL,
                        modified TIMESTAMP NOT NULL,
                        progress TEXT,
                        status TEXT,
                        user_query TEXT,
                        user_response TEXT
                        );
        '''
        c.execute(sql)

        sql = '''
            CREATE TABLE IF NOT EXISTS positions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TIMESTAMP NOT NULL,
                        symbol TEXT NOT NULL,
                        currency TEXT NOT NULL,
                        reported TIMESTAMP NOT NULL,
                        openQuantity INTEGER DEFAULT 0,
                        currentPrice REAL DEFAULT 0.0,
                        averageEntryPrice REAL DEFAULT 0.0,
                        fk_account INTEGER NOT NULL,
                        FOREIGN KEY(fk_account) REFERENCES accounts(id)
                        );
        '''
        c.execute(sql)

        sql = "CREATE INDEX IF NOT EXISTS index_position_date ON positions(date)"
        c.execute(sql)

    # TODO Function to delete old actions rows

    def action_create(self, action):
        cur = self.conn.cursor()
        sql = ''' 
            INSERT INTO actions(action,created,modified,status)
              VALUES(?,?,?,?) '''
        ret = cur.execute(sql, (action, datetime.datetime.now(), datetime.datetime.now(), 'created'))
        self.conn.commit()
        return cur.lastrowid

    def action_update(self, action_id, status, progress=None, user_query=None, user_response=None):
        
        if status not in ['working','done','error','user_query','user_response']:
            raise Exception(f'Invalid status: {status}')
        
        cur = self.conn.cursor()
        if progress:
            sql = 'UPDATE actions SET status=?,progress=?,user_query=?,user_response=?,modified=? WHERE id=?'
            ret = cur.execute(sql, (status,progress,user_query,user_response,datetime.datetime.now(),action_id))
        else:
            sql = 'UPDATE actions SET status=?,user_query=?,user_response=?,modified=? WHERE id=?'
            ret = cur.execute(sql, (status,user_query,user_response,datetime.datetime.now(),action_id))
        self.conn.commit()

    def action_status(self, action_id):
        cur = self.conn.cursor()
        cur.execute("SELECT status,progress,user_query,user_response FROM actions WHERE id=?", (action_id,))
        row = cur.fetchone()
        return row

    def base_currency(self):
        return self._base_currency

    def add_positions(self, acct_id, positions):
        cur = self.conn.cursor()

        ts = datetime.datetime.now()
        date_str = ts.isoformat()[:10]

        # Delete all positions for the same day for this account
        sql = 'DELETE FROM positions WHERE fk_account=? AND date=?'
        cur.execute(sql, (acct_id,date_str))

        # Insert each entry
        rows = [(date_str, 
                 p['symbol'], 
                 ts,
                 p.get('openQuantity',0),
                 p.get('currentPrice',0),
                 p.get('averageEntryPrice',0),
                 p.get('currency'),
                 acct_id
                 ) for p in positions]

        sql = '''INSERT INTO positions(date, symbol, reported, 
                    openQuantity, currentPrice, averageEntryPrice, currency,
                    fk_account) VALUES(?,?,?,?,?,?,?,?)'''
        cur.executemany(sql, rows)

        self.conn.commit()

    def add_historical_balance(self, acct_id, date, balance):
        cur = self.conn.cursor()
        # sql = ''' 
        #     DELETE FROM historical_balance WHERE date=? AND fk_account=?
        # '''
        # ret = cur.execute(sql, (date,acct_id))
        sql = ''' 
            INSERT INTO historical_balance(date,balance,fk_account)
              VALUES(?,?,?) '''
        ret = cur.execute(sql, (date,balance,acct_id))

        self.conn.commit()

    def create(self, username, password, base_currency):

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
        conn = sqlite3.connect(db_file, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        self._update_tables(conn)

        # Create one row in user table
        sql = ''' 
            INSERT INTO users(username,password_hash,salt1,salt2,db_version,base_currency)
              VALUES(?,?,?,?,?,?) '''
        cur = conn.cursor()
        ret = cur.execute(sql, (username,password_hash,salt1,salt2,self.DB_VERSION,base_currency))

        conn.commit()
                
        self.conn = conn
        self.cipher = _cipher_from_password(password,bytes.fromhex(salt2))

    def open(self, username, password):

        self.conn = None
        self.cipher = None

        db_file = os.path.join('userdata', username + '.db')
        conn = sqlite3.connect(db_file, check_same_thread=False)
        conn.row_factory = sqlite3.Row

        # Update DB if the tables have changed
        self._update_tables(conn)

        # Validate password with salt
        cur = conn.cursor()
        cur.execute("SELECT salt1,salt2,password_hash,base_currency FROM users WHERE username=?", (username,))
        row = cur.fetchone()

        if not row:
            raise Exception('Database error, user not found')

        salt1 = row[0]
        salt2 = row[1]

        if not row[2] == _sha1hash('%s%s' % (salt1,password)):
            raise Exception('Wrong password')

        self._base_currency = row[3]
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
        return [(row[0], row[1], json.loads(self._decrypt(row[2]))) for row in rows]

    def get_account_id(self, provider_id, uid):
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM accounts WHERE fk_provider=? AND bank_id=?", (provider_id, uid))
        row = cur.fetchone()
        if row:
            return row[0]

    def update_account(self, account_id, **kwargs):

        # Store historical account balance
        balance = kwargs.get('balance', 0.0)
        self.add_historical_balance(account_id, datetime.datetime.now(), balance)

        # Update account data
        cur = self.conn.cursor()
        sql = ''' 
            UPDATE accounts SET last_update=?,balance=? WHERE id=? '''
        ret = cur.execute(sql, (datetime.datetime.now(),balance,account_id))

        self.conn.commit()

    def create_account(self, provider_id, uid, **kwargs):

        name = kwargs.get('name', uid)
        description = kwargs.get('description', '')
        atype = kwargs.get('type', '')
        currency = kwargs.get('currency', '')
        balance = kwargs.get('balance', 0.0)

        cur = self.conn.cursor()
        sql = ''' 
            INSERT INTO accounts(bank_id,name,type,description,last_update,fk_provider,currency,balance)
              VALUES(?,?,?,?,?,?,?,?) '''
        ret = cur.execute(sql, (uid,name,atype,description,datetime.datetime.now(),provider_id, currency, balance))

        self.conn.commit()

        return cur.lastrowid

    def iter_providers(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id,name,last_login FROM providers ORDER BY name")
        for id,name,last_login in cur.fetchall():
            yield {'id':id, 'name':name, 'last_login':last_login}

    def iter_accounts(self, provider_id=None):
        cur = self.conn.cursor()
        sql = 'SELECT id,bank_id,name,type,base_type,description,balance,currency,last_update,(SELECT count(*) FROM transactions WHERE fk_account=a.id) FROM accounts as a'
        if provider_id:
            cur.execute(sql + ' WHERE fk_provider=?', (provider_id,))
        else:
            cur.execute(sql)
        for id,bank_id,name,atype,base_type,description,balance,currency,last_update,nb_transactions in cur.fetchall():
            yield {'id':id, 'bank_id':bank_id, 'name':name, 'type':atype, 'base_type':base_type, 'balance':balance, 'description':description, 'currency':currency, 'transaction_count':nb_transactions, 'last_update':last_update}

    def iter_positions(self, account_id):
        # TODO Add date query option
        cur = self.conn.cursor()
        sql = """SELECT date,symbol,openQuantity,currentPrice,averageEntryPrice 
                 FROM positions
                 WHERE fk_account=? AND date=(SELECT MAX(date) FROM positions WHERE fk_account=?)
                 ORDER BY symbol ASC"""
        cur.execute(sql, (account_id,account_id))
        for date,symbol,openQuantity,currentPrice,averageEntryPrice in cur.fetchall():
            yield {'date':date, 'symbol':symbol, 'openQuantity':openQuantity, 'currentPrice':currentPrice, 'averageEntryPrice':averageEntryPrice}

    def iter_transactions(self, account_id, limit=None, offset=0):
        cur = self.conn.cursor()
        sql = "SELECT id,description,type,amount,date,added,uncleared FROM transactions as a WHERE fk_account=? ORDER BY date DESC, added DESC, id DESC"
        if limit:
            sql = sql + ' LIMIT %d OFFSET %d' % (limit,offset)
        cur.execute(sql, (account_id,))
        for id,description,ttype,amount,date,added,uncleared in cur.fetchall():
            added_today = str(datetime.datetime.now().date()) == added[:10]
            yield {'id':id, 'description':description, 'type':ttype, 'amount':amount, 'date':date, 'added':added, 'uncleared':uncleared, 'added_today':added_today}

    def iter_historical_balance(self, account_id, limit=None, offset=0):
        cur = self.conn.cursor()
        sql = "SELECT date,balance FROM historical_balance WHERE fk_account=? ORDER BY date DESC"
        if limit:
            sql = sql + ' LIMIT %d OFFSET %d' % (limit,offset)
        cur.execute(sql, (account_id,))
        for date,balance in cur.fetchall():
            yield {'date':date, 'balance':balance}

    def get_transactions_for_range(self, account_id, date_from, date_to):
        cur = self.conn.cursor()

        # Get earliest Balance value for each account
        sql = 'SELECT date,balance FROM historical_balance WHERE fk_account=? ORDER BY date ASC LIMIT 1'
        cur.execute(sql, (account_id,))
        earliest_date, earliest_balance = cur.fetchone()

        date1 = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
        date2 = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
        for d in daterange(date1, date2):

            eod_balance = 0.0

            if d < datetime.datetime.strptime(earliest_date, '%Y-%m-%d').date():
                #print('DEBUG Date is before all stored balances')
                sql = '''SELECT sum(amount) FROM transactions 
                    WHERE fk_account=? 
                    AND strftime('%s',date)>strftime('%s',?)
                    AND strftime('%s',date)<strftime('%s',?)'''
                cur.execute(sql, (account_id, d, earliest_date))
                sum_amounts = cur.fetchone()[0]
                eod_balance = earliest_balance - (0 if sum_amounts is None else sum_amounts)

            else:
                # Compute EOD Balance for this account for the specified date
                sql = """SELECT b.date,balance,
                    (SELECT sum(amount) FROM transactions as t WHERE t.fk_account=b.fk_account AND strftime('%s',t.date)>strftime('%s',b.date) AND strftime('%s',t.date)<strftime('%s',?) ) 
                    FROM historical_balance as b
                    WHERE fk_account=? AND substr(b.date,0,11)<=? 
                    ORDER BY strftime('%s',b.date) DESC 
                    LIMIT 1"""
                cur.execute(sql, (d + datetime.timedelta(1),account_id,d))
                for row in cur.fetchall():
                    eod_balance = row[1] + (row[2] if row[2] else 0.0)

            yield {'date':str(d), 'balance':eod_balance}

    def find_transaction(self, account_id, transaction_id, **kwargs):

        cur = self.conn.cursor()
        cur.execute("SELECT id FROM transactions WHERE fk_account=? AND bank_id=?", 
            (account_id,transaction_id))
        row = cur.fetchone()
        if row:
            return row[0]

    def add_transaction(self, account_id, transaction_id, **kwargs):
        # transaction_id is the unique id from the bank

        description = kwargs.get('description', '')
        ttype = kwargs.get('type', 'unknown')
        amount = kwargs.get('amount', 0.0)
        date = kwargs.get('date', 'unknown')
        added = kwargs.get('added', datetime.datetime.now())
        data = json.dumps(kwargs.get('extra', {}))
        uncleared = 1 if kwargs.get('uncleared', False) else 0

        cur = self.conn.cursor()
        sql = ''' 
            INSERT INTO transactions (bank_id,description,type,amount,date,added,uncleared,fk_account,data)
              VALUES(?,?,?,?,?,?,?,?,?) '''
        ret = cur.execute(sql, (transaction_id,description,ttype,amount,date,added,uncleared,account_id,data))

        self.conn.commit()

        return cur.lastrowid

    def remove_transaction(self, account_id, transaction_db_id):
        cur = self.conn.cursor()
        sql = ''' 
            DELETE FROM transactions WHERE fk_account=? AND id=? '''
        ret = cur.execute(sql, (account_id, transaction_db_id))
        self.conn.commit()

    def remove_transactions(self, list_of_db_ids):
        if list_of_db_ids:
            cur = self.conn.cursor()
            sql = 'DELETE FROM transactions WHERE id IN (%s)' % ','.join(['?'] * len(list_of_db_ids))
            ret = cur.execute(sql, list_of_db_ids)
            self.conn.commit()

    def get_uncleared_transactions(self, account_id):
        cur = self.conn.cursor()
        sql = ''' 
            SELECT id FROM transactions WHERE fk_account=? AND uncleared>0 '''
        ret = cur.execute(sql, (account_id,))
        return [x[0] for x in cur.fetchall()]

    def get_accounts_total_balance(self):
        cur = self.conn.cursor()
        sql = ''' 
            SELECT SUM(balance),currency FROM accounts GROUP BY currency '''
        ret = cur.execute(sql)
        return cur.fetchall()

    def get_account_info(self, account_id):
        cur = self.conn.cursor()
        sql = ''' 
            SELECT name,currency,balance,description,base_type FROM accounts WHERE id=? '''
        ret = cur.execute(sql, (account_id,))
        return cur.fetchone()
