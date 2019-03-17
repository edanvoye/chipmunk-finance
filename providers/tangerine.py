
from providers.base import ProviderPlugin
import time
import json
import datetime

class TangerinePlugin(ProviderPlugin):

    def __init__(self, webdriver):
        self.webdriver = webdriver

    def update(self, get_user_data, store_user_data, add_account=None, add_transaction=None, last_updates={}):

        self.webdriver.get('https://www.tangerine.ca/app/#/?locale=en_US')
        time.sleep(5) # TODO Wait for new page to appear

        clientId = self.webdriver.find_element_by_name('login_clientId')
        user_account = get_user_data('Client Number, Card Number or Username')
        clientId.send_keys( user_account )
        time.sleep(2) # TODO Wait for AngularJS to validate

        self.webdriver.find_element_by_id('login_logMeIn').click()
        time.sleep(3) # TODO Wait for new page to appear

        secretQuestionText = self.webdriver.find_element_by_id('login_secretQuestion_label').text
        secretQuestionAnswer = self.webdriver.find_element_by_id('login_secretQuestion')
        user_secret = get_user_data(secretQuestionText)
        secretQuestionAnswer.send_keys( user_secret )
        time.sleep(2) # TODO Wait for AngularJS to validate
        self.webdriver.find_element_by_id('login_Next').click()
        time.sleep(3) # TODO Wait for new page to appear

        pin = self.webdriver.find_element_by_id('login_pin')
        user_pin = get_user_data('PIN', is_password=True)
        pin.send_keys( user_pin )
        time.sleep(2) # TODO Wait for AngularJS to validate
        self.webdriver.find_element_by_id('login_signIn').click()
        time.sleep(3) # TODO Wait for new page to appear

        # If we get here, we can save the credentials
        store_user_data('Client Number, Card Number or Username', user_account)
        store_user_data(secretQuestionText, user_secret)
        store_user_data('PIN', user_pin)

        if add_account:

            # Download Account list
            self.webdriver.get('https://secure.tangerine.ca/web/rest/pfm/v1/accounts')
            time.sleep(2) # TODO Wait for new page to appear
            json_accounts = self.webdriver.find_element_by_xpath("/html/body/pre").text
            account_data = json.loads(json_accounts).get('accounts', [])

            for account in account_data:

                # Add account to database
                add_account(account['number'], 
                    name=account.get('nickname', account['description']), 
                    description=account['description'], 
                    type=account['type'], 
                    currency=account['currency_type'], 
                    balance=account['account_balance'])

                if add_transaction:

                    # Download transactions
                    from_date = '2019-02-14T00:00:00.000' # TODO Dates for transactions
                    to_date = '2019-03-16T03:59:59.999'

                    url = 'https://secure.tangerine.ca/web/rest/pfm/v1/transactions?accountIdentifiers=%s&periodFrom=%s&periodTo=%s&skip=0' % (account['number'], from_date, to_date)

                    while url:

                        self.webdriver.get(url)
                        time.sleep(2) # TODO Wait for new page to appear
                        url = None

                        json_transactions = self.webdriver.find_element_by_xpath("/html/body/pre").text
                        transactions_data = json.loads(json_transactions)

                        transactions = transactions_data.get('transactions', [])
                        for transaction in transactions:

                            print('DEBUG transaction bank_id=%s desc=%s' % (transaction.get('id'),transaction.get('description')))

                            # Example:
                            # {"transaction_date":"2019-03-13T17:50:35",
                            #  "has_uncertain_categorization":false,
                            #  "confirmation_number":"xxxxxxx",
                            #  "amount":-5062.39,
                            #  "comments":[],
                            #  "balance_after":487.24,
                            #  "is_split_child":null,
                            #  "description":"Paiement - Carte de crédit Remises TNG",
                            #  "type":"WITHDRAWAL",
                            #  "is_uncleared":false,
                            #  "detected_categories":[{"score":1,"categoryId":211}],
                            #  "is_read":false,"account_id":"xxxxx",
                            #  "originalAmount":-5062.39,
                            #  "category_id":211,
                            #  "id":xxxxx,
                            #  "parent_transaction_id":"xxxxx-942a",
                            #  "posted_date":"2019-03-13T00:00:00",
                            #  "is_flagged":null,
                            #  "status":"POSTED"}

                            # Add transaction to database
                            try:
                                add_transaction(account['number'], transaction['id'], 
                                    date=transaction['transaction_date'], 
                                    added=datetime.datetime.now(),
                                    type=transaction['type'], 
                                    amount=transaction['amount'], 
                                    description=transaction['description'])
                            except:
                                print('Error with transaction: %s' % transaction)

                        # Follow link if there are more transactions for this date range
                        if transactions:
                            links = transactions_data.get('links')
                            if links:
                                for link in links:
                                    if link.get('rel') == 'next':
                                        url = 'https://secure.tangerine.ca/web/rest' + link.get('href')

        # Example data recieved
        # https://secure.tangerine.ca/web/rest/pfm/v1/accounts
        # {"response_status":{"status_code":"SUCCESS"},
        #  "restrictions":[],
        #  "exchangeRates":[{"buy":1.355,"sell":1.31,"currency":"USD"}],
        #  "accounts":[{"number":"xxxxxxxxxx","account_balance":487.24,"currency_type":"CAD","nickname":"ChequeE,"description":"Compte-chèques Tangerine","goal_account":false,"display_name":"XXXXX","type":"CHEQUING","product_code":"4000"},...]}
        
        # https://secure.tangerine.ca/web/rest/pfm/v1/transactions?accountIdentifiers=xxxxxx&periodFrom=2019-02-14T00:00:00.000&periodTo=2019-03-16T03:59:59.999&skip=0
        # {"response_status":{"status_code":"SUCCESS"},"restrictions":[],"links":[{"rel":"next","href":"/pfm/v1/transactions?skip=50&accountIdentifiers=xxxxxxxxx&periodTo=2014-11-08"}],
        #  "transactions":[{"transaction_date":"2019-03-13T17:50:35","has_uncertain_categorization":false,"confirmation_number":"xxxxxxx","amount":-5062.39,"comments":[],"balance_after":487.24,"is_split_child":null,"description":"Paiement - Carte de crédit Remises TNG","type":"WITHDRAWAL","is_uncleared":false,"detected_categories":[{"score":1,"categoryId":211}],"is_read":false,"account_id":"xxxxx","originalAmount":-5062.39,"category_id":211,"id":xxxxx,"parent_transaction_id":"xxxxx-942a","posted_date":"2019-03-13T00:00:00","is_flagged":null,"status":"POSTED"},......]}

    class meta:
        name = 'tangerine'
        description = 'Tangerine Bank (Canada)'
