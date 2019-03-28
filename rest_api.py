
from flask import Flask
from flask_restful import reqparse, Resource, Api
from flask_httpauth import HTTPBasicAuth
from flask import g
from flask.json import jsonify

from storage import UserData

auth = HTTPBasicAuth()
app = Flask('Chipmunk Finance')
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('count', type=int, default=10)
parser.add_argument('offset', type=int, default=0)

@auth.verify_password
def verify_password(username, password):
    data = UserData()
    if not data.exists(username):
        return False
    try:
        data.open(username, password)
        g.user = data
        return True
    except Exception as e:
        return False

class AuthResource(Resource):
    method_decorators = [auth.login_required]

class AccountTransactions(AuthResource):
    def get(self, account_id):
        args = parser.parse_args()
        return [t for t in g.user.iter_transactions(account_id, args['count'], args['offset'])]
api.add_resource(AccountTransactions, '/api/transactions/<account_id>')

class AccountBalanceHistory(AuthResource):
    def get(self, account_id):
        args = parser.parse_args()
        return [b for b in g.user.iter_historical_balance(account_id, args['count'], args['offset'])]
api.add_resource(AccountBalanceHistory, '/api/history/<account_id>')

class AccountList(AuthResource):
    def get(self):
        return [a for a in g.user.iter_accounts()]
api.add_resource(AccountList, '/api/accounts')

# Runs the Flask Server for our REST API
def run_rest_server(cm, debug=False):
    app.run(debug=debug)
