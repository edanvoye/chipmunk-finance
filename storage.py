
import os
import sqlite3

class UserData():
    def __init__(self):
        self.conn = None

    def exists(self, username):
        return os.path.exists(os.path.join('userdata', username + '.db'))

    def create(self, username, password):

        if not os.path.exists('userdata'):
            os.makedirs('userdata')

        self.conn = sqlite3.connect(os.path.join('userdata', username + '.db'))

    def open(self, username, password):

        # TODO Validate password

        self.conn = sqlite3.connect(os.path.join('userdata', username + '.db'))
