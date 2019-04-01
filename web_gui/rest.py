
from flask import render_template, g, Blueprint
from flask_restful import reqparse, Resource, Api

from . import auth

rest_api = Blueprint('rest_api', __name__)

parser = reqparse.RequestParser()
parser.add_argument('count', type=int, default=20)
parser.add_argument('offset', type=int, default=0)

api = Api(rest_api)

## REST API

class AuthResource(Resource):
    method_decorators = [auth.login_required]

class AccountTransactions(AuthResource):
    def get(self, account_id):
        args = parser.parse_args()
        return [t for t in g.user.iter_transactions(account_id, args['count'], args['offset'])]
api.add_resource(AccountTransactions, '/transactions/<account_id>')

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
api.add_resource(AccountBalanceHistory, '/history/<account_id>')

class AccountList(AuthResource):
    def get(self):
# TODO We also need balance in the base currency + base_currency
        return [a for a in g.user.iter_accounts()]
api.add_resource(AccountList, '/accounts')