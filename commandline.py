
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

    # if args.interactive:
    #     while 1:
    #         show_menu()
    #         key = input()
    #         if key=='q':
    #             break
    #         if key=='a':
    #             for c in providers.get_provider_classes():
    #                 print(c.meta.name)
    #             # TODO display list of providers, ask user to choose one
    #             # Then call login, and then add to database


    
