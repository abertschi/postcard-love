import os

CAPTCHA_SECRET = ''
MOCK_SEND = False

POST_ACCOUNTS = [
    {
        'username': '',
        'password': ''
    }
]

RECIPIENT_DEFAULT = None #of type postcard_creator.Recipient

BASEDIR_PICTURES = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'images')

try:
    from settings_local import *
except ImportError:
    pass