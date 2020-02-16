import os
import binascii

class Config(object):
    """Base config """
    DEBUG = False
    PORT = 8080
    SECRET_KEY = "qwertyuiop" #binascii.hexlify(os.urandom(128)).decode()



class ProductionConfig(Config):
    """Uses production server config."""
    if os.getenv("SECRET_KEY") is not None:
        SECRET_KEY = str(os.getenv("SECRET_KEY"))

    if os.getenv("PORT") is not None:
        PORT = os.getenv("PORT")


class DevelopmentConfig(Config):
    """ Config for development """
    DEBUG = True
    if os.getenv("PORT") is not None:
        PORT = os.getenv("PORT")
    if os.getenv("SECRET_KEY") is not None:
        SECRET_KEY = str(os.getenv("SECRET_KEY"))
