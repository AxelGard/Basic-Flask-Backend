from flask import Flask
from flask_cachebuster import CacheBuster
from config import *
import os
import logging
import logging.handlers



def create_app():
    app = Flask(__name__)
    app.config.from_object('config.DevelopmentConfig')
    file_handler = logging.handlers.RotatingFileHandler('errorlog.txt')
    app.config['PERMANENT_SESSION_LIFETIME'] = 10800 # session time, 3H
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

cache_buster()

# run server
if __name__ == '__main__':
    print(" * Starting --> server...")
    app.run(debug=app.config['DEBUG'], port=app.config['PORT'])
