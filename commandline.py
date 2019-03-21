
import getpass
import argparse
import datetime

from engine import ChipmunkEngine
import providers 

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--accounts", action="store_true", help="List accounts for user")
    parser.add_argument("-a", "--add", action="store_true", help="Add provider")
    parser.add_argument("-u", "--update", action="store_true", help="Update all accounts")
    parser.add_argument("-t", "--transactions", nargs='?', const=10, default=None, help="Show transactions")
    parser.add_argument('--user', nargs=1)

    args = parser.parse_args()

    ## Login

    username = args.user[0] if args.user else input("Username: ")
    if not username:
        exit(1)
    password = getpass.getpass()

    cm = ChipmunkEngine()
    if not cm.user_exists(username):
        # Attempt to create new user
        print('User does not exist, creating...')
        print('Please enter password a second time:')
        if not password == getpass.getpass():
            print('Passwords do not match')
            exit(1)

        # Create new user
        cm.create(username, password)
    else:
        cm.login(username, password)

    ## Operations

    if args.accounts:
        print('Listing Accounts for user %s' % cm.username)
        for provider in cm.iter_providers():
            print('Provider %s (Last update: %s)' % (provider['name'], provider['last_login']))
            for account in cm.iter_accounts(provider['id']):
                print(' Account %s' % account['name'])
                for key in account:
                    print('  %s: %s' % (key, account[key]))
        
    if args.add:
        print('Adding Provider for user %s' % cm.username)
        provider_name_list = list(cm.get_provider_names())
        for i,name in enumerate(provider_name_list):
            print('%d: %s' % (i,name))
        index = input("Choose provider to add: ")
        if index.isdigit():
            provider_name = provider_name_list[int(index)]
            print('Adding provider ' + provider_name)

            def user_query(label, is_password=False):
                if is_password:
                    return getpass.getpass(label + ': ')
                return input(label + ': ')

            cm.add_provider(provider_name, user_query)

            print('Account Added')

    if args.update:
        print('Updating transactions for user %s' % cm.username)

        def progress_cb(message):
            print(message)

        def user_query(label, is_password=False):
            if is_password:
                return getpass.getpass(label + ': ')
            return input(label + ': ')

        cm.update_providers(progress_cb, user_query)

    if args.transactions:
        nb_transactions = int(args.transactions)
        print('Display %d Last Transactions for each account for user %s' % (nb_transactions, cm.username))
        for provider in cm.iter_providers():
            for account in cm.iter_accounts(provider['id']):
                print('Provider:%s Account:%s (%s) [Balance:%.2f]' % (provider['name'], account['name'], account['description'], account['balance']))
                for transaction in cm.iter_transactions(account['id'], nb_transactions):
                    added_today = str(datetime.datetime.now().date()) == transaction['added'][:10]
                    print('%s (%s) %s [%s] %.2f %s' % (
                        '*' if added_today else ' ',
                        transaction['date'][:10],
                        transaction['type'],
                        transaction['description'],
                        transaction['amount'],
                        account['currency'],
                    ))
