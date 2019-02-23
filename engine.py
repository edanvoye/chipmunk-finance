
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
        # TODO 
        from providers.tangerine import TangerinePlugin
        self.provider_classes[TangerinePlugin.meta.name] = TangerinePlugin

    # List available providers
    # Add provider
    # List added providers + status
    # Update provider
    # List accounts
    # List account transations