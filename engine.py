
import os
from storage import UserData
from currency import currency_current_rate
import time
import datetime

class Provider():
    def __init__(self):
        pass

class Account():
    def __init__(self):
        pass

class Transaction():
    def __init__(self):
        pass

class ChipmunkEngine():
    def __init__(self, data=None):
        self.data = data
        self.provider_classes = {}
        self.load_providers_plugins()

    def user_exists(self, username):
        data = UserData()
        return data.exists(username)

    def create(self, username, password, base_currency):
        self.data = None
        data = UserData()
        data.create(username,password,base_currency)
        self.data = data
        self.username = username

    def login(self, username, password):
        self.data = None

        data = UserData()
        if not data.exists(username):
            raise Exception('User does not exist')
        data.open(username,password)

        self.data = data
        self.username = username

    def load_providers_plugins(self):

        # TODO Make this dynamic, look for every class inheriting from ProviderPlugin
        import providers
        plugins = [providers.DemoBankPlugin, providers.TangerinePlugin, providers.QuestradePlugin]

        for plugin in plugins:
            self.provider_classes[plugin.meta.name] = plugin

    def get_provider_names(self):
        return self.provider_classes.keys()

    def add_provider(self, provider_name, user_query):

        # Instanciate provider
        if not provider_name in self.provider_classes:
            raise Exception('Provider name does not exist')

        provider = self.provider_classes[provider_name](driver)

        temp_user_data = {}

        def get_user_data(label, is_password=False):
            # Look for previously entered data
            return temp_user_data.get(label, user_query('[%s] %s' % (provider_name, label), is_password))

        def store_user_data(label, value):
            # Store user data in temporary dict, will be saved to DB if the login is success
            temp_user_data[label] = value

        provider.update(get_user_data, store_user_data)

        # Login is a success, store provider and user data in DB
        self.data.add_provider(provider_name, temp_user_data)

    def _add_account(self, provider_id, uid, **kwargs):
        account_id = self.find_account(provider_id, uid)
        if account_id:
            # Update last_update
            self.data.update_account(account_id, **kwargs)
        else:
            # Create Account
            account_id = self.data.create_account(provider_id, uid, **kwargs)
        return account_id

    def _add_transaction(self, account_id, transaction_id, **kwargs):
        transaction_db_id = self.data.find_transaction(account_id, transaction_id, **kwargs)
        if not transaction_db_id:
            return self.data.add_transaction(account_id, transaction_id, **kwargs),True
        return transaction_db_id,False

    def find_account(self, provider_id, uid):
        # Given a provider DB id, and an account uid, find account DB id
        return self.data.get_account_id(provider_id, uid)

    def iter_providers(self):
        return self.data.iter_providers()

    def iter_accounts(self, provider_id):
        return self.data.iter_accounts(provider_id)

    def iter_transactions(self, account_id, limit=None):
        return self.data.iter_transactions(account_id, limit)

    def iter_historical_balance(self, account_id, limit=None):
        return self.data.iter_historical_balance(account_id, limit)

    def update_providers(self, progress_cb, user_query):

        total_added = 0

        progress_cb('Updating All Providers')

        # List all registered providers from database
        providers = self.data.registered_provider_list()

        # For each registered provider
        for id,name,data in providers:

            added_transactions = []

            progress_cb('Updating Provider #%d %s' % (id,name))

            # Instanciate provider
            if not name in self.provider_classes:
                raise Exception('Provider plugin does not exist: ' + name)
            provider = self.provider_classes[name]()

            uncleared_transactions = []
            uncleared_accounts = []

            def get_user_data(label, is_password=False):
                return data[label] if label in data else user_query('[%s] %s' % (name, label), is_password)
            def store_user_data(label, value):
                if data.get(label) != value:
                    data[label] = value
            def add_account(uid, **kwargs):
                return self._add_account(id, uid, **kwargs)
            def add_transaction(account_uid, transaction_id, **kwargs):
                account_id = self.find_account(id, account_uid)
                if account_id:
                    if account_id not in uncleared_accounts:
                        # make a list of uncleared transactions, these will be deleted after update if 
                        # they are not seen again.
                        uncleared_transactions.extend(self.data.get_uncleared_transactions(account_id))
                        uncleared_accounts.append(account_id)
                    db_tr_id,added = self._add_transaction(account_id, transaction_id, **kwargs)
                    if added:
                        # transaction db_tr_id added
                        nonlocal added_transactions
                        added_transactions.append(db_tr_id)
                    else:
                        # transaction db_tr_id already exists
                        if db_tr_id in uncleared_transactions:
                            uncleared_transactions.remove(db_tr_id)
            def add_positions(account_uid, data):
                account_id = self.find_account(id, account_uid)
                if account_id:
                    self.data.add_positions(account_id, data)
                
            # create dict of last update date for each known account
            last_account_update = {account['bank_id']: account['last_update'] for account in self.data.iter_accounts(id)}

            def progress_fct(msg):
                progress_cb('Updating Provider #%d %s: %s' % (id,name,msg))

            # Call plugin to update provider via web scraping
            provider.update(get_user_data, store_user_data, add_account, add_transaction, add_positions, progress=progress_fct, last_updates=last_account_update)

            # Update database
            if uncleared_transactions:
                print('Removing %d uncleared transactions' % len(uncleared_transactions))
                self.data.remove_transactions(uncleared_transactions)
            self.data.update_provider(id, data)

            print('Added %d transactions from %s (#%d)' % (len(added_transactions),name,id))

            total_added = total_added + len(added_transactions)

        return total_added

    def to_base_currency(self, currency, amount):
        return amount * currency_current_rate(currency, self.data.base_currency())

    def create_account_update_async_action(self):
        action_id = self.data.action_create('account_update')

        # Launch Worker Thread for this async action
        from threading import Thread 
        t = Thread(target=ChipmunkEngine.account_update_thread, args=(self,action_id))
        t.start()
        
        return action_id

    def account_update_thread(self,action_id):
        # Worker thread to process one async action

        # # TEMPORARY TEST
        # for i in range(5):
        #     self.data.action_update(action_id, status='working', progress=f'test{i}')
        #     time.sleep(3)
        # self.data.action_update(action_id, status='user_query', user_query='Username?')
        # status = 'working'
        # while status != 'user_response':
        #     status,_,_,user_response = self.data.action_status(action_id)
        #     time.sleep(1)
        # print(user_response)
        # for i in range(5):
        #     self.data.action_update(action_id, status='working', progress=f'after{i}')
        #     time.sleep(3)
        # self.data.action_update(action_id, status='done')
        # return

        print(f'Run thread to process action {action_id}')

        def progress_cb(message):
            self.data.action_update(action_id, status='working', progress=message)

        def user_query(label, is_password=False):
            status = 'user_password' if is_password else 'user_query'
            self.data.action_update(action_id, status=status, user_query=label)
            while status != 'user_response':
                status,_,_,user_response = self.data.action_status(action_id)
                # TODO Check timeout, and return None if too long
                time.sleep(1)
            self.data.action_update(action_id, status='working')
            return user_response

        total_added = self.update_providers(progress_cb, user_query)

        self.data.action_update(action_id, status='done', progress=f'Added {total_added} transactions')
