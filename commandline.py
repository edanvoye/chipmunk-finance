
import getpass
import argparse

from engine import ChipmunkEngine

def show_menu():
    print('-- Chipmunk Menu --')
    print('l: List Accounts')
    print('a: Add Provider')
    print('u: Update All Account')
    print('q: Quit')

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--interactive", action="store_true", help="show interactive menu")

    args = parser.parse_args()

    username = input("Username: ")
    password = getpass.getpass()

    cm = ChipmunkEngine()
    cm.login(username, password)

    if args.interactive:
        while 1:
            show_menu()
            key = input()
            if key=='q':
                break


    
