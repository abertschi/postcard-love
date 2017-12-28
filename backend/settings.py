import os

CAPTCHA_SECRET = ''
MOCK_SEND = False
DB_DEBUG = False

POST_ACCOUNTS = [
    {
        'username': '',
        'password': ''
    }
]

#of type postcard_creator.Recipient
RECIPIENT_DEFAULT = None

BASEDIR_PICTURES = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'images')

try:
    from settings_local import *
except ImportError:
    pass