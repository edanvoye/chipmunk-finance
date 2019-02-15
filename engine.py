
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

    def login(self, username, password):

        try:
            self.data = UserData()
            if not data.exists(username):
                self.data.create(username,password)
            else:
                self.data.open(username,password)
        except:
            self.data = None

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