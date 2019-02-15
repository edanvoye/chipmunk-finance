
from providers.base import ProviderPlugin

class DemoBankPlugin(ProviderPlugin):

    def update(self, get_user_data, store_user_data, add_account, add_transaction):
        pass

    class meta:
        name = 'demo'
        description = 'Demo'
