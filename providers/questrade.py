
from providers.base import ProviderPlugin

class QuestradePlugin(ProviderPlugin):

    def update(self, get_user_data, store_user_data, add_account=None, add_transaction=None):
        pass

    class meta:
        name = 'questrade'
        description = 'Questrade (Canada)'
