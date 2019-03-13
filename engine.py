
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
        # TODO temp_user_data
        print('TODO Saving user data in database')
        print(temp_user_data)

    # List added providers + status
    # Update provider
    # List accounts
    # List account transations