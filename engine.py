
from storage import UserData

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
    def __init__(self):
        self.data = None
        self.provider_classes = {}
        self.load_providers_plugins()

    def user_exists(self, username):
        data = UserData()
        return data.exists(username)

    def create(self, username, password):
        self.data = None
        data = UserData()
        data.create(username,password)
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
        plugins = [providers.DemoBankPlugin]

        for plugin in plugins:
            self.provider_classes[plugin.meta.name] = plugin

    def get_provider_names(self):
        return self.provider_classes.keys()

    def add_provider(self, provider_name, user_query):
        
        # Instanciate provider
        if not provider_name in self.provider_classes:
            raise Exception('Provider name does not exist')
        provider = self.provider_classes[provider_name]()

        temp_user_data = {}

        def get_user_data(label):
            # Look for previously entered data
            return temp_user_data.get(label, user_query(label))

        def store_user_data(label, value):
            # Store user data in temporary dict, will be saved to DB if the login is success
            temp_user_data[label] = value

        provider.update(get_user_data, store_user_data)

        # Login is a success, store provider and user data in DB
        self.data.add_provider(provider_name, temp_user_data)

    def _add_account(self, provider_id, uid, data):
        account_id = self.find_account(provider_id, uid)
        if account_id:
            # Update last_update
            self.data.update_account(account_id, data)
        else:
            # Create Account
            account_id = self.data.create_account(provider_id, uid, data)
        return account_id

    def _add_transaction(self, account_id, data):
        # TODO check if transaction already exists
        # TODO add transaction to db
        return 0 # return DB id for this transaction

    def find_account(self, provider_id, uid):
        # Given a provider DB id, and an account uid, find account DB id
        return self.data.get_account_id(provider_id, uid)

    def update_providers(self, progress_cb, user_query):

        progress_cb('Updating All Providers')

        # List all registered providers from database
        providers = self.data.registered_provider_list()

        # For each registered provider
        for id,name,data in providers:
            progress_cb('Updating Provider #%d: %s' % (id,name))

            # Instanciate provider
            if not name in self.provider_classes:
                raise Exception('Provider plugin does not exist: ' + name)
            provider = self.provider_classes[name]()

            def get_user_data(label):
                return data[label] if label in data else user_query(label)
            def store_user_data(label, value):
                if data.get(label) != value:
                    data[label] = value
            def add_account(uid, data):
                return self._add_account(id, uid, data)
            def add_transaction(account_uid, data):
                account_id = self.find_account(id, account_uid)
                if account_id:
                    return self._add_transaction(account_id, data)
                
            # Call plugin to update provider via web scraping
            provider.update(get_user_data, store_user_data, add_account, add_transaction)

            # Update provider in database
            self.data.update_provider(id, data)
