# flask
from flask import Flask
from flask import render_template
from flask import abort
from flask import session
from flask import flash
from flask import redirect
from flask import request
# cache buster
from flask_cachebuster import CacheBuster
# loging
import logging
import logging.handlers
# config
from config import *
# py std
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.DevelopmentConfig')
    file_handler = logging.handlers.RotatingFileHandler('log/errorlog.txt')
    session_time = 60*60*3 # session time, 3H
    app.config['PERMANENT_SESSION_LIFETIME'] = session_time
    app.logger.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)
    return app

app = create_app()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/hello/')
def hello():
    return 'Hello, World'


# run server
if __name__ == '__main__':
    print(" * Starting --> server... ")
    app.run(debug=app.config['DEBUG'], port=app.config['PORT'])
