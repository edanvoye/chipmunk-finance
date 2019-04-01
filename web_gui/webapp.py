
from flask import g

from storage import UserData

from . import app, auth

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

## Load all views

from .views import *
from .rest import *

## Runs the Flask Server for our REST API

def run_web_server(cm, debug=False):
    app.run(debug=debug)
