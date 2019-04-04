
from flask import render_template, g

from . import app, auth

## Graph URLS

# TODO Refactor balance graph to accept a date range, add function in storage to get account balance over time (time series)
# TODO Create graph with all accounts, and a dynamic dataset for sum of all accounts
# TODO Add checkboxes to include or ignore accounts
# TODO Add fields to change the date range

@app.route("/")
@auth.login_required
def home():
    return render_template('home.html')

@app.route("/account_balance/<int:account_id>")
@auth.login_required
def chart(account_id):
    name,currency,balance,description = g.user.get_account_info(account_id)
    return render_template('account_balance_chart.html', 
        account_id=account_id, 
        account_name=name, 
        account_description=description, 
        account_currency=currency)

@app.route("/accounts")
@auth.login_required
def accounts():
    return render_template('accounts.html')
