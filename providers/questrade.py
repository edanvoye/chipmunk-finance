
from providers.base import ProviderPlugin

import requests
import json
import traceback
import datetime

def split_date_range(from_date, to_date, step = datetime.timedelta(days=7)):

    it = from_date
    while it < to_date:
        yield it,it+step
        it += step

class QuestradePlugin(ProviderPlugin):

    def __init__(self):
        pass

    def update(self, get_user_data, store_user_data, add_account=None, add_transaction=None, add_positions=None, progress=None, last_updates={}):

        if progress:
            progress('Logging In...')

        # First go to Questrade's webside. In your account, go to App Hub
        # and press Register Personal App.
        # Enter name, description, press Create.
        # Press Add Device, get Token

        refresh_token = get_user_data('refresh_token')

        access = self.get_access_token(refresh_token)
        if not access:
            raise Exception('Invalid refresh_token')

        self.access_token = access['access_token']
        self.token_type = access['token_type']
        self.refresh_token = access['refresh_token']
        self.api_server = access['api_server']

        store_user_data('access_token', self.access_token)
        store_user_data('token_type', self.token_type)
        store_user_data('refresh_token', self.refresh_token)

        try:

            if add_account:

                response = self.auth_request_get('accounts')
                data = response.json()

                for account in data.get('accounts', []):

                    acc_id = account['number']

                    if account['status'] != 'Active':
                        continue

                    if progress:
                        progress('Account:'+acc_id)

                    # Also fetch CAD balance for this account
                    cad_balance = 0.0
                    response = self.auth_request_get('accounts/%s/balances' % acc_id)
                    balance_data = response.json()
                    for bal in balance_data['combinedBalances']:
                        if bal.get('currency') == 'CAD':
                            cad_balance = bal.get('totalEquity', 0.0)

                    # Add account to database
                    add_account(acc_id, 
                        name='%s (%s)' % (account['type'],acc_id),
                        description='%s %s' % (account['clientAccountType'],account['type']), 
                        type=account['type'], 
                        currency='CAD', # Balance will be converted to CAD
                        balance=cad_balance)

                    if add_transaction:
                        self._download_transactions(acc_id, add_transaction, last_updates)

                    if add_positions:
                        # Get positions in this account
                        response = self.auth_request_get('accounts/%s/positions' % acc_id)
                        positions_data = response.json()
                        positions = positions_data.get('positions', [])
                        for pos in positions:
                            response = self.auth_request_get('symbols/%s' % pos['symbolId'])
                            sym = response.json().get('symbols')[0]
                            pos['currency'] = sym.get('currency')

                        add_positions(acc_id, positions_data.get('positions', []))

        except Exception as e:
            print('Error updating from Questrade')
            traceback.print_exc()

    def _download_transactions(self, acc_id, add_transaction, last_updates):
        
        def format_datetime(when):
            dt = datetime.datetime(when.year, when.month, when.day, when.hour, when.minute, when.second).astimezone(datetime.timezone.utc)
            return dt.isoformat('T')

        # Download transactions
        if acc_id in last_updates:
            from_date = datetime.datetime.strptime(last_updates[acc_id], "%Y-%m-%d %H:%M:%S.%f") - datetime.timedelta(days=7)
        else:
            from_date = datetime.datetime.now() - datetime.timedelta(days=365*3)
        to_date = datetime.datetime.now()

        for start,end in split_date_range(from_date, to_date, datetime.timedelta(days=30)):

            response = self.auth_request_get('accounts/%s/activities?startTime=%s&endTime=%s' % 
                (acc_id, format_datetime(start), format_datetime(end)))
            tx_data = response.json()

            for transaction in tx_data.get('activities'):

                def _sha1hash(s):
                    import hashlib
                    return hashlib.sha1(s.encode('utf-8')).hexdigest()

                tx_id = _sha1hash(str(transaction))

                # Add transaction to database
                try:
                    add_transaction(acc_id, tx_id, 
                        date=transaction['transactionDate'], 
                        added=datetime.datetime.now(),
                        type=transaction['type'] + '/' + transaction['action'], 
                        amount=transaction['netAmount'], 
                        description=transaction['symbol'],
                        extra= {
                            'details':transaction['description'],
                            'currency':transaction['currency'],
                            'price':transaction['price'],
                            'quantity':transaction['quantity'],
                            'commission':transaction['commission'],
                            'settlementDate':transaction['settlementDate']
                            }
                        )
                except:
                    print('Error with transaction: %s' % transaction)
                    traceback.print_exc()
                
    def get_access_token(self, refresh_token):
        url = 'https://login.questrade.com/oauth2/token?grant_type=refresh_token&refresh_token=%s' % refresh_token
        response = requests.get(url)
        if response.status_code==200:
            return response.json()
        else:
            print('Error: %s' % response.status_code)
            return None
            
    def auth_request_get(self, path, raise_on_error=True):
        headers = {'Authorization': '%s %s' % (self.token_type, self.access_token)}
        url = self.api_server + 'v1/' + path
        response = requests.get(url, headers=headers)
        if raise_on_error and response.status_code!=200:
            print(response.text)
            raise Exception('Response code %s for URL:%s' % (response.status_code, url))
        return response

    class meta:
        name = 'questrade'
        description = 'Questrade (Canada)'
