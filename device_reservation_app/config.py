import os

from dotenv import load_dotenv
from sqlalchemy.pool import QueuePool

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


def creator(args):
    pass


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY', 'DEVELOPMENT')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:////' + os.path.join(basedir, 'app.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE = 28700
    SQLALCHEMY_POOL_TIMEOUT = 2000
    SQLALCHEMY_ENGINE_OPTIONS = {
        'isolation_level': 'READ UNCOMMITTED',
        'pool_pre_ping': True
    }
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['smarigowda@logitech.com']
    ELASTICSEARCH_URL = os.environ.get('MS_TRANSLATOR_KEY')
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://')
    POSTS_PER_PAGE = 25

