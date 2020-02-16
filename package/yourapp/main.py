from flask import Flask
from flask_cachebuster import CacheBuster
from config import *
import os
import logging
import logging.handlers



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
from views import * # needs app

def cache_buster():
    """ static url cache buster, to load new css and js """
    config = { 'extensions': ['.js', '.css'], 'hash_size': 5 }
    cache_buster = CacheBuster(config=config)
    cache_buster.init_app(app)


if app.config['DEBUG']:
    # if in debug moode then remove old css and js files that might be cached 
    cache_buster()

if __name__ == '__main__':
    print(" * Starting --> server...")
    app.run(debug=app.config['DEBUG'], port=app.config['PORT'])
