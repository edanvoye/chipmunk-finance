
import getpass
import argparse

from engine import ChipmunkEngine
import providers 

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list", action="store_true", help="List accounts for user")
    parser.add_argument("-a", "--add", action="store_true", help="Add provider")
    parser.add_argument("-u", "--update", action="store_true", help="Update all accounts")
    parser.add_argument("-t", "--transactions", action="store_true", help="Show transactions")

    args = parser.parse_args()

    ## Login

    username = input("Username: ")
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

    if args.list:
        print('Listing Accounts for user %s' % cm.username)
        # TODO
    if args.add:
        print('Adding Provider for user %s' % cm.username)
        # TODO
    if args.update:
        print('Updating transactions for user %s' % cm.username)
        # TODO
    if args.transactions:
        print('Display Transactions for user %s' % cm.username)
        # TODO
