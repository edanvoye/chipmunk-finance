
from providers.base import ProviderPlugin

class TangerinePlugin(ProviderPlugin):

    def __init__(self, webdriver):
        self.webdriver = webdriver

    def update(self, get_user_data, store_user_data, add_account=None, add_transaction=None):
        
        # Example call to WebDriver
        import time
        self.webdriver.get('http://www.google.com/xhtml');
        time.sleep(5) # Let the user actually see something!
        search_box = self.webdriver.find_element_by_name('q')
        search_box.send_keys('ChromeDriver')
        search_box.submit()
        time.sleep(5) # Let the user actually see something!

        # # Load main webpage, need username and password
        # username = get_user_data('Username')
        # password = get_user_data('Password')

        # # If we get 403 from the form
        # if password != '1234':
        #     raise Exception('Invalid password')

        # # Page load success, store data
        # store_user_data('Username', username)
        # store_user_data('Password', password)

        # # Fill form and load next page
        # security = get_user_data('Name of your first pet?')

        # # If we get 403 from the form
        # if security != 'fido':
        #     # We could also try a few times, and repeat the call to get_user_data
        #     raise Exception('Invalid security question')

        # store_user_data('Name of your first pet?', security)

        # if add_account:
        #     # Ready to load accounts
        #     add_account('1001', {'name':'Saving','currency':'USD','balance':34.12})
        #     add_account('1002', {'name':'Checking','currency':'USD','balance':123.45})

        # if add_transaction:
        #     # Ready to load transactions
        #     add_transaction('1001', {'date':'2018-12-31','type':'DEPOSIT','amount':3.45,'description':'EFT to savings'})


    class meta:
        name = 'tangerine'
        description = 'Tangerine Bank (Canada)'
