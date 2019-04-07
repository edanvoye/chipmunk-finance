
from providers.base import ProviderPlugin, selenium_webdriver
import time
import json
import datetime
import traceback

class TangerinePlugin(ProviderPlugin):

    def __init__(self):
        pass

    def update(self, get_user_data, store_user_data, add_account=None, add_transaction=None, progress=None, last_updates={}):

        with selenium_webdriver() as webdriver:

            if progress:
                progress('Logging In...')

            webdriver.get('https://www.tangerine.ca/app/#/?locale=en_US')
            time.sleep(5) # TODO Wait for new page to appear

            clientId = webdriver.find_element_by_name('login_clientId')
            user_account = get_user_data('Client Number, Card Number or Username')
            clientId.send_keys( user_account )
            time.sleep(2) # TODO Wait for AngularJS to validate

            webdriver.find_element_by_id('login_logMeIn').click()
            time.sleep(3) # TODO Wait for new page to appear

            secretQuestionText = webdriver.find_element_by_id('login_secretQuestion_label').text
            secretQuestionAnswer = webdriver.find_element_by_id('login_secretQuestion')
            user_secret = get_user_data(secretQuestionText)
            secretQuestionAnswer.send_keys( user_secret )
            time.sleep(2) # TODO Wait for AngularJS to validate
            webdriver.find_element_by_id('login_Next').click()
            time.sleep(3) # TODO Wait for new page to appear

            pin = webdriver.find_element_by_id('login_pin')
            user_pin = get_user_data('PIN', is_password=True)
            pin.send_keys( user_pin )
            time.sleep(2) # TODO Wait for AngularJS to validate
            webdriver.find_element_by_id('login_signIn').click()
            time.sleep(3) # TODO Wait for new page to appear

            # If we get here, we can save the credentials
            store_user_data('Client Number, Card Number or Username', user_account)
            store_user_data(secretQuestionText, user_secret)
            store_user_data('PIN', user_pin)

            if add_account:

                # Download Account list
                webdriver.get('https://secure.tangerine.ca/web/rest/pfm/v1/accounts')
                time.sleep(2) # TODO Wait for new page to appear
                json_accounts = webdriver.find_element_by_xpath("/html/body/pre").text
                account_data = json.loads(json_accounts).get('accounts', [])

                for i,account in enumerate(account_data):

                    acc_id = account['number']

                    if progress:
                        progress(f'Account:{i+1}/{len(account_data)}')

                    if account['type']=='CREDIT_CARD' or account['type']=='LOAN':
                        account['account_balance'] = -account['account_balance'] # negative balance for debt

                    # Add account to database
                    add_account(acc_id, 
                        name=account.get('nickname', account['description']), 
                        description=account['description'], 
                        type=account['type'], 
                        currency=account['currency_type'], 
                        balance=account['account_balance']) 

                    if add_transaction:

                        # Download transactions
                        if acc_id in last_updates:
                            from_date = datetime.datetime.strptime(last_updates[acc_id], "%Y-%m-%d %H:%M:%S.%f") - datetime.timedelta(days=7)
                        else:
                            from_date = datetime.datetime.now() - datetime.timedelta(days=365*3)
                        to_date = datetime.datetime.now()

                        skip = 0

                        while 1:
        
                            url = 'https://secure.tangerine.ca/web/rest/pfm/v1/transactions?accountIdentifiers=%s&periodFrom=%s&periodTo=%s&skip=%d' % (acc_id, from_date.isoformat()[:10], to_date.isoformat()[:10], skip)

                            webdriver.get(url)
                            time.sleep(2) # TODO Wait for new page to appear
                            url = None

                            json_transactions = webdriver.find_element_by_xpath("/html/body/pre").text
                            transactions_data = json.loads(json_transactions)

                            transactions = transactions_data.get('transactions', [])
                            if not transactions:
                                break
                            skip = skip + len(transactions)

                            for transaction in transactions:

                                #print('DEBUG transaction bank_id=%s desc=%s' % (transaction.get('id'),transaction.get('description')))

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
                                    if 'transaction_date' in transaction:
                                        add_transaction(acc_id, transaction['id'], 
                                            date=transaction['transaction_date'], 
                                            added=datetime.datetime.now(),
                                            type=transaction['type'], 
                                            amount=transaction['amount'], 
                                            description=transaction['description'],
                                            uncleared=transaction.get('is_uncleared'))
                                except:
                                    print('Error with transaction: %s' % transaction)
                                    traceback.print_exc()

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
