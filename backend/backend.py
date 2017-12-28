from flask import Flask, request, jsonify
import requests
import base64
import os
from time import gmtime, strftime
import datetime
import string
import imghdr
import postcard_creator
import random
import hashlib
import sys
import logging
import settings
import db_access
import secret_handler
from xml.sax.saxutils import escape
from xml.dom.minidom import Text, Element

logger = logging.getLogger('postcard-love')
VALID_PIC_EXT = ['gif', 'png', 'jpg', 'tiff', 'bmp']
RECAPTCHA_HOST = 'https://www.google.com/recaptcha/api/siteverify'

app = Flask(__name__, static_url_path='')
# app.debug = True

if not os.path.exists(settings.BASEDIR_PICTURES):
    os.makedirs(settings.BASEDIR_PICTURES)


class InvalidPictureException(Exception):
    pass


@app.after_request
def add_header(response):
    response.cache_control.max_age = 0
    return response


@app.route('/')
def serve():
    return app.send_static_file('index.html')


@app.route('/api/submit', methods=['GET'])
def meh():
    return random.choice(['ಠ_ಠ', '(ง\'̀-\'́)ง', '◉_◉', '┻━┻ ︵ヽ(`Д´)ﾉ︵ ┻━┻'])


@app.route('/api/submit', methods=['POST'])
def api_submit():
    if request.get_json() is not None:
        payload = request.get_json()

        required_args = ['g-recaptcha-response', 'pictures']
        for required in required_args:
            if not required in payload:
                logger.error('/api/submit required parameter {} missing'.format(required))
                return jsonify(error='Required parameter "{}" is missing 🙊'
                               .format(required)), 400

        for picture in payload.get('pictures'):
            if not picture.get('src'):
                logger.error('/api/submit picture without src argument')
                return jsonify(error='Invalid picture given. Picture without src argument 🙊'), 400

        data = {
            'secret': settings.CAPTCHA_SECRET,
            'response': payload.get('g-recaptcha-response')
        }
        resp = requests.post(RECAPTCHA_HOST, data=data)
        captcha_response = resp.json()
        if resp.status_code is not 200 or \
                not captcha_response.get('success'):
            logger.error('/api/submit captcha wrong')
            return jsonify(error='Captcha is wrong 🙊'), 400

        response_msg = ''
        secret = payload.get('secret')
        is_valid_secret = secret_handler.is_valid_secret(secret)

        if len(payload.get('pictures')) > 1 and \
                not is_valid_secret:
            payload['pictures'] = [payload['pictures'][0]]
            response_msg = response_msg + ' only first picture is printed out. '

        try:
            process_postcard_request(payload)
        except InvalidPictureException:
            return jsonify(error='Invalid picture given 🙊'), 400

        return jsonify({
            'success': True,
            'message': response_msg or ''
        }), 200

    pass


def has_valid_secret(secret):
    return False


def process_postcard_request(payload):
    picture_paths = []
    message = escape(payload.get('message') or '')[:400]
    sender = escape(payload.get('name') or '')[:40]
    secret = ''
    priority = 0

    if secret_handler.is_valid_secret(payload.get('secret')):
        secret = payload.get('secret')[:1024]
        priority = secret_handler.get_priority(secret)

    identifier = 'p-' + datetime.datetime.now().strftime("%f")

    for picture in payload.get('pictures'):
        name = identifier + '_' + picture.get('name')
        picture_paths.append(store_image(picture.get('src'), name))

    if not picture_paths:
        raise InvalidPictureException  # raise exception if all pictures are invalid

    store_postcard(message, sender, picture_paths, recipient=settings.RECIPIENT_DEFAULT,
                   identifier=identifier, secret=secret, priority=priority)


def store_postcard(message, sender_name, picture_paths, recipient, identifier='', secret='', priority=0):
    for path in picture_paths:
        db_access.store_postcard(db_access.StorePostcardRequest(
            message, path,
            sender_name=sender_name,
            picture_group=identifier,
            secret=secret,
            priority=priority), recipient=recipient)


def throw_exception_if_invalid_picture(byte_stream):
    ext = imghdr.what('', h=byte_stream)
    if ext not in VALID_PIC_EXT:
        raise InvalidPictureException


def store_image(encoded_picture, sender_name=''):
    try:
        src = encoded_picture.split(';')[1].split(',')[1]
    except Exception:
        # wrong encoded
        raise InvalidPictureException

    folder_name = 'bean'
    absolute_folder = os.path.join(settings.BASEDIR_PICTURES, folder_name)
    if not os.path.exists(absolute_folder):
        os.makedirs(absolute_folder)

    basename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") \
               + '_{}.png'.format(to_valid_filename(sender_name))
    basename = os.path.join(folder_name, basename)

    filename = os.path.join(settings.BASEDIR_PICTURES, basename)
    logger.info('storing picture {}'.format(filename))

    image_64_decode = base64.b64decode(src)
    throw_exception_if_invalid_picture(image_64_decode)

    image_result = open(filename, 'wb')
    image_result.write(image_64_decode)
    image_result.close()

    return basename


def to_valid_filename(name):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    name = name.strip()
    name = ''.join(c for c in name if c in valid_chars)
    name = name.replace(' ', '_')
    if len(name) > 50:
        name = name[:50]
    return name


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    app.run(host='0.0.0.0', port=5000)
