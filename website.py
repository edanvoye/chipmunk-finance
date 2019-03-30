
from flask import Flask, render_template, g
from flask_restful import reqparse, Resource, Api
from flask_httpauth import HTTPBasicAuth
from flask.json import jsonify

from storage import UserData

auth = HTTPBasicAuth()
app = Flask('Chipmunk Finance')
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('count', type=int, default=20)
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

## Graph URLS

# TODO Refactor Graphs to get data from a REST call
# TODO Refactor balance graph to accept a date range, add function in storage to get account balance over time (time series)
# TODO Create graph with all accounts, and a dynamic dataset for sum of all accounts
# TODO Add checkboxes to include or ignore accounts
# TODO Add fields to change the date range

@app.route("/account_balance/<account_id>")
@auth.login_required
def chart(account_id):
    args = parser.parse_args()
    name,currency,balance,description = g.user.get_account_info(account_id)
    data = g.user.iter_historical_balance(account_id, args['count'])
    return render_template('account_balance_chart.html', 
        account_id=account_id, 
        account_name=name, 
        account_description=description, 
        account_currency=currency, 
        data=data)

## REST API

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
        name,currency,balance,description = g.user.get_account_info(account_id)
        ret = {
            'id':account_id,
            'name':name,
            'currency':currency,
            'description':description,
            'history':[b for b in g.user.iter_historical_balance(account_id, args['count'], args['offset'])]}
        return ret
api.add_resource(AccountBalanceHistory, '/api/history/<account_id>')

class AccountList(AuthResource):
    def get(self):
        return [a for a in g.user.iter_accounts()]
api.add_resource(AccountList, '/api/accounts')

## Runs the Flask Server for our REST API

def run_rest_server(cm, debug=False):
    app.run(debug=debug)
