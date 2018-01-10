import os
from collections import defaultdict
import logging

CAPTCHA_SECRET = ''
MOCK_SEND = False
DB_DEBUG = False
REST_DEBUG = False
IGNORE_CAPTCHA = False

POST_ACCOUNTS = [
    {
        'username': '',
        'password': ''
    }
]

#of type postcard_creator.Recipient
RECIPIENT_DEFAULT = None

BASEDIR_PICTURES = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'images')

# structure
# {
#     'priority': 0
# }
SECRETS_MAP = defaultdict(set)

DEV_IGNORE_SECRET = None

try:
    from secrets.settings_local import *
except ImportError:
    logging.getLogger('settings').warn('no local settings found')
    pass