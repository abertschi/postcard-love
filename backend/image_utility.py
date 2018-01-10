from db_access import DbPostcard
from pony.orm import *
from sightengine.client import SightengineClient
from settings import NSFW_DETECTION_ENABLED, NSFW_CLIENT_ID, NSFW_CLIENT_PW, BASEDIR_PICTURES, DEV_IGNORE_SECRET
import os
from secret_handler import is_valid_secret
import logging
import json
import sys

logger = logging.getLogger('postcard-love')
client = SightengineClient(NSFW_CLIENT_ID, NSFW_CLIENT_PW)

NSFW_SCORE_THRESHOLD = 0.5


def can_printout_card(dbcard):
    if DEV_IGNORE_SECRET and is_valid_secret(DEV_IGNORE_SECRET) \
            and DEV_IGNORE_SECRET == dbcard.secret:
        return False

    if not NSFW_DETECTION_ENABLED:
        logger.debug('NSFW detection is disabled')
        return True

    abs_path = os.path.join(BASEDIR_PICTURES, dbcard.picture_path)

    if is_valid_secret(dbcard.secret):
        logger.debug('Not checking for NSFW content in picture {}. Valid secret set.'
                     .format(abs_path, dbcard.id))
        return True

    return check_for_nsfw(dbcard.id, dbcard.picture_path)


def check_for_nsfw(card_id, abs_path):
    output = client.check('nudity').set_file(abs_path)
    if output.get('status') != 'success':
        logger.error('nsfw check not successful for image {} with postcard id {}: {}. '
                     'Marking picture as safe.'
                     .format(abs_path, card_id, json.dumps(output)))
        return True

    nudity = output.get('nudity')
    if nudity is None:
        logger.error('something went wrong, sightengine has wrong ouput structure. {}. '
                     'Marking picture as safe.'
                     .format(json.dumps(output)))
        return True

    score = nudity.get('raw') or 1
    if score >= NSFW_SCORE_THRESHOLD:
        logger.info('picture {} / {} was flagged as NSFW. Raw score: {}'
                    .format(card_id, abs_path, score))
        return False

    logger.info('picture {} / {} does not contain NSFW content. Score {}'
                .format(card_id, abs_path, score))
    return True


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt="%Y-%m-%d %H:%M:%S")

    check_for_nsfw('__id__', '/Users/abertschi/beandata/pgm/postcard-love/project/backend/images/img.png')
