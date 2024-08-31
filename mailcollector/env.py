import os

REDIS_HOST = os.environ.get('REDIS_HOST', '')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)
DB_NAME = os.environ.get('DB_NAME', 'postgres')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', '1234')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5431')
