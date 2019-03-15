
from providers.base import ProviderPlugin

class TangerinePlugin(ProviderPlugin):

    def update(self, get_user_data, store_user_data, add_account=None, add_transaction=None):
        pass
        
    class meta:
        name = 'tangerine'
        description = 'Tangerine Bank (Canada)'
