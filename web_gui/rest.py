
from flask import render_template, g, Blueprint, jsonify, request
from flask_restful import reqparse, Resource, Api

from . import auth

rest_api = Blueprint('rest_api', __name__)

parser = reqparse.RequestParser()
parser.add_argument('count', type=int, default=20)
parser.add_argument('offset', type=int, default=0)

daterange_parser = reqparse.RequestParser()
daterange_parser.add_argument('from', type=str, default=None)
daterange_parser.add_argument('to', type=str, default=None)

api = Api(rest_api)

## REST API

class AuthResource(Resource):
    method_decorators = [auth.login_required]

class AccountTransactions(AuthResource):
    def get(self, account_id):
        args = parser.parse_args()
        return [t for t in g.user.iter_transactions(account_id, args['count'], args['offset'])]
api.add_resource(AccountTransactions, '/transactions/<int:account_id>')

class AccountPositions(AuthResource):
    def get(self, account_id):
        return [p for p in g.user.iter_positions(account_id)]
api.add_resource(AccountPositions, '/positions/<int:account_id>')

class AccountBalanceHistory(AuthResource):
    def get(self, account_id):
        args = parser.parse_args()
        name,currency,balance,description,base_type = g.user.get_account_info(account_id)
        ret = {
            'id':account_id,
            'name':name,
            'currency':currency,
            'currency_to_base':g.user.to_base_currency(currency),
            'description':description,
            'base_type':base_type,
            'history':[b for b in g.user.iter_historical_balance(account_id, args['count'], args['offset'])]}
        return ret
api.add_resource(AccountBalanceHistory, '/history/<int:account_id>')

class AccountBalanceHistoryByDate(AuthResource):
    def get(self, account_id):
        args = daterange_parser.parse_args()
        name,currency,balance,description,base_type = g.user.get_account_info(account_id)
        ret = {
            'id':account_id,
            'name':name,
            'currency':currency,
            'currency_to_base':g.user.to_base_currency(currency),
            'description':description,
            'base_type':base_type,
            'history':[b for b in g.user.get_eod_balance_for_range(account_id, args['from'], args['to'])]}
        return ret
api.add_resource(AccountBalanceHistoryByDate, '/history_by_date/<int:account_id>')

class AccountList(AuthResource):
    def get(self):
        return [a for a in g.user.iter_accounts()]
api.add_resource(AccountList, '/accounts')

## API for async actions

@rest_api.route("/async/create/account_update")
@auth.login_required
def async_create_account_update():
    action_id = g.cm.create_account_update_async_action()
    return jsonify({'rcode':'OK', 'action_id':action_id})

@rest_api.route("/async/status/<int:action_id>")
@auth.login_required
def async_action_status(action_id):
    status,progress,user_query,_ = g.user.action_status(action_id)
    return jsonify({'status':status,'progress':progress,'user_query':user_query})

@rest_api.route("/async/update/<int:action_id>")
@auth.login_required
def async_action_update(action_id):
    user_response = request.args.get('user_response')
    g.user.action_update(action_id, 'user_response', user_response=user_response)
    return jsonify({'rcode':'OK'})
    
# TODO Rest Api for Positions
