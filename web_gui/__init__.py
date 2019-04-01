
from flask import Flask
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()
app = Flask('Chipmunk Finance', template_folder='web_gui/templates', static_folder='web_gui/static')

from .webapp import run_web_server
