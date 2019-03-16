
from providers.base import ProviderPlugin

class TangerinePlugin(ProviderPlugin):

    def __init__(self, webdriver):
        self.webdriver = webdriver

    def update(self, get_user_data, store_user_data, add_account=None, add_transaction=None):
        
        # Go to https://www.tangerine.ca/en/index.html
        # find id=mainnav_login (find_element_by_id)
        # click it
        # Find name="login_clientId"
        # send keys "Client Number, Card Number or Username"
        # submit form
        # if we find id="login_secretQuestion"
        # question is id="login_secretQuestion_label"
        # if find id-login_pin
        # enter pin, submit
        # https://secure.tangerine.ca/web/rest/pfm/v1/accounts
        # {"response_status":{"status_code":"SUCCESS"},"restrictions":[],"exchangeRates":[{"buy":1.355,"sell":1.31,"currency":"USD"}],"accounts":[{"number":"xxxxxxxxxx","account_balance":487.24,"currency_type":"CAD","nickname":"ChequeE,"description":"Compte-chèques Tangerine","goal_account":false,"display_name":"XXXXX","type":"CHEQUING","product_code":"4000"},...]}
        # https://secure.tangerine.ca/web/rest/pfm/v1/transactions?accountIdentifiers=xxxxxx&periodFrom=2019-02-14T00:00:00.000&periodTo=2019-03-16T03:59:59.999&skip=0
        # {"response_status":{"status_code":"SUCCESS"},"restrictions":[],"links":[{"rel":"next","href":"/pfm/v1/transactions?skip=50&accountIdentifiers=xxxxxxxxx&periodTo=2014-11-08"}],"transactions":[{"transaction_date":"2019-03-13T17:50:35","has_uncertain_categorization":false,"confirmation_number":"xxxxxxx","amount":-5062.39,"comments":[],"balance_after":487.24,"is_split_child":null,"description":"Paiement - Carte de crédit Remises TNG","type":"WITHDRAWAL","is_uncleared":false,"detected_categories":[{"score":1,"categoryId":211}],"is_read":false,"account_id":"xxxxx","originalAmount":-5062.39,"category_id":211,"id":xxxxx,"parent_transaction_id":"xxxxx-942a","posted_date":"2019-03-13T00:00:00","is_flagged":null,"status":"POSTED"},......]}
        # goto next pages

        # Example call to WebDriver
        import time
        self.webdriver.get('http://www.google.com/xhtml')
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
        #     add_transaction('1001', 345, {'date':'2018-12-31','type':'DEPOSIT','amount':3.45,'description':'EFT to savings'})


    class meta:
        name = 'tangerine'
        description = 'Tangerine Bank (Canada)'
