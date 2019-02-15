
from providers.base import ProviderPlugin

class DemoBankPlugin(ProviderPlugin):

    def update(self, get_user_data, store_user_data, add_account, add_transaction=None):
        pass
        # ask user for demo bank username
        # ask user for demo bank password
        # check if credentials are ok
        # fake login to website
        # report 3 accounts found
        # report transactions

    class meta:
        name = 'demo'
        description = 'Demo'
