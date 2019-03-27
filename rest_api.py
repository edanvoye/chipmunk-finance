
from flask import Flask
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
from flask import g
from flask.json import jsonify

from storage import UserData

auth = HTTPBasicAuth()
app = Flask('Chipmunk Finance')
api = Api(app)

@auth.verify_password
def verify_password(username, password):
    print('verify_password ' + username)
    data = UserData()
    if not data.exists(username):
        print('no exist')
        return False
    try:
        data.open(username, password)
        g.user = data
        return True
    except Exception as e:
        print('except %s' % e)
        return False

class AuthResource(Resource):
    method_decorators = [auth.login_required]

# class Account(AuthResource):
#     def get(self, account_id):
#         return {'id': account_id}
# api.add_resource(Account, '/api/account/<account_id>')

class AccountList(AuthResource):
    def get(self):
        return [a for a in g.user.iter_accounts()]
api.add_resource(AccountList, '/api/accounts')

# Runs the Flask Server for our REST API
def run_rest_server(cm, debug=False):
    app.run(debug=debug)
