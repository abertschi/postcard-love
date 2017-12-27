from flask import Flask, request, jsonify
import requests
import base64
import os
from time import gmtime, strftime
import datetime
import string
import imghdr
import sqlite3

app = Flask(__name__, static_url_path='')
app.debug = True

RECAPTCHA_HOST = 'https://www.google.com/recaptcha/api/siteverify'
SECRET = '6LdoUj0UAAAAAKq4moxwk-ds8IO6GUkvqsS7B9xe'

# https://www.pythoncentral.io/introduction-to-sqlite-in-python/
db = sqlite3.connect('postcard-love.db')

IMG_DIR = './images'
IMG_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), IMG_DIR)
if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

VALID_PIC_EXT = ['gif', 'png', 'jpg', 'tiff', 'bmp']


@app.route('/')
def serve():
    print('called')
    return app.send_static_file('index.html')


@app.route('/api/submit', methods=['POST'])
def api_submit():
    if request.get_json() is not None:
        payload = request.get_json()

        required_args = ['g-recaptcha-response', 'pictures']
        for required in required_args:
            if not required in payload:
                return jsonify(error='Required parameter "{}" is missing'.format(required)), 400

        for picture in payload.get('pictures'):
            if not picture.get('src'):
                return jsonify(error='Invalid picture in request. Picture without src argument'), 400

        data = {
            'secret': SECRET,
            'response': payload.get('g-recaptcha-response')
        }
        resp = requests.post(RECAPTCHA_HOST, data=data)
        captcha_response = resp.json()
        if resp.status_code is not 200 or \
                not captcha_response.get('success'):
            return jsonify(error='Captcha is wrong'), 400

        process_postcard_request(payload)

        return jsonify({
            'success': True,
            'message': ''
        }), 200

    pass

def foo():
    if not imghdr.what() in VALID_PIC_EXT:
        pass


def process_postcard_request(payload):
    message = payload.get('message')
    sender = payload.get('name')

    for picture in payload.get('pictures'):
        name = picture.get('name')
        if not name:
            name = 'postcard'
        name = to_valid_filename(name)

        src = picture.get('src')
        split = src.split(';')
        format = split[0]
        src = split[1]
        split = src.split(',')
        src = split[1]

        basename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f_{}.png".format(name))
        filename = os.path.join(IMG_DIR, basename)
        print(filename)

        image_64_decode = base64.b64decode(src)
        image_result = open(filename, 'wb')
        image_result.write(image_64_decode)
        image_result.close()
    pass


def to_valid_filename(name):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    name = name.strip()
    name = ''.join(c for c in name if c in valid_chars)
    name = name.replace(' ', '_')
    if len(name) > 50:
        name = name[:50]
    return name


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
