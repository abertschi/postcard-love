from db_access import get_pending_postcards, DbPostcard, DbRecipient, \
    mark_postcard_as_sent, get_size_of_pending_postcards, move_picture_to_cancel_folder
import logging
import settings
import random
import sys
import os
from postcard_creator.postcard_creator import Token, PostcardCreator, Postcard, Recipient, Sender, \
    PostcardCreatorException
from xml.sax.saxutils import escape
import json
import emoji
import unicodedata

logger = logging.getLogger('send_job')

import codecs
import image_utility
from html.entities import codepoint2name


def html_replace(exc):
    if isinstance(exc, (UnicodeEncodeError, UnicodeTranslateError)):
        s = [u'&%s;' % codepoint2name[ord(c)]
             for c in exc.object[exc.start:exc.end]]
        return ''.join(s), exc.end
    else:
        raise TypeError("can't handle {}".format(exc.__name__))


codecs.register_error('html_replace', html_replace)


def process():
    logger.info('starting send_job to send postcards ...')
    api_wrappers, try_again = _get_pcc_wrapper(stop_on_first_valid=False)
    if not api_wrappers:
        logger.info('no valid accounts. try again {}. terminating send_job'.format(try_again or 'later'))
        exit(1)

    random.shuffle(api_wrappers)
    pending_cards = get_pending_postcards(limit=len(api_wrappers))
    sent_cards = send_cards(api_wrappers, pending_cards)
    logger.info('{}/{} postcards ({}) are sent'.format(len(sent_cards), get_size_of_pending_postcards(), sent_cards))


def create_api_recipient(db_postcard):
    return Recipient(prename=db_postcard.recipient.firstname,
                     lastname=db_postcard.recipient.lastname,
                     street=db_postcard.recipient.street,
                     zip_code=db_postcard.recipient.zipcode,
                     place=db_postcard.recipient.city)


def create_api_sender(db_postcard):
    sender_firstname = db_postcard.sender_name if \
        db_postcard.sender_name else db_postcard.recipient.firstname

    sender_lastname = '' if \
        sender_firstname is not db_postcard.recipient.firstname \
        else db_postcard.recipient.lastname

    return Sender(prename=_escape(sender_firstname)[:100],
                  lastname=_escape(sender_lastname),
                  street=db_postcard.recipient.street,
                  zip_code=db_postcard.recipient.zipcode,
                  place=db_postcard.recipient.city)


def _escape(string):
    return escape(emoji.demojize(string))


def _remove_special_characters(string):
    return unicodedata.normalize('NFKD', string).encode('iso_8859_1', 'ignore').decode('utf-8')


def send_cards(api_wrappers, db_cards):
    card_i = 0
    sent_cards = []

    for api_wrapper in api_wrappers:
        if card_i >= len(db_cards):
            break

        pending_card = db_cards[card_i]
        card_i = card_i + 1

        if not image_utility.can_printout_card(pending_card):
            # todo refactor this method to accept one card and one wrapper
            move_picture_to_cancel_folder(pending_card)
            continue

        file = os.path.join(settings.BASEDIR_PICTURES, pending_card.picture_path)
        api_picture_stream = open(file, 'rb')
        api_message = escape(pending_card.message)[:400]

        logger.debug('uploading file {}'.format(file))
        logger.debug('message: ' + api_message)

        api_card = Postcard(sender=create_api_sender(pending_card),
                            recipient=create_api_recipient(pending_card),
                            picture_stream=api_picture_stream,
                            message=api_message)
        try:
            response = api_wrapper.send_free_card(postcard=api_card, mock_send=settings.MOCK_SEND)
        except Exception:
            # weird behaviour noticed with unicode characters
            # hack for now, if something breaks, retry again but ignore all non ascii characters
            logger.error('something went wrong with postcard-creator. Perhaps special chars in msg. Retrying once')
            logger.error('msg = {}, name={}'.format(api_card.message,
                                                    api_card.sender.prename
                                                    + api_card.sender.lastname))

            api_card.message = _remove_special_characters(api_card.message)
            api_card.sender.prename = _remove_special_characters(api_card.sender.prename)
            api_card.sender.lastname = _remove_special_characters(api_card.sender.lastname)

            response = api_wrapper.send_free_card(postcard=api_card, mock_send=settings.MOCK_SEND)

        if response:
            logger.debug('postcard id:{} is sent'.format(pending_card.id))
            mark_postcard_as_sent(postcard_id=pending_card.id)
            sent_cards.append(pending_card.id)

    return sent_cards


def _get_pcc_wrapper(stop_on_first_valid=True):
    pcc_wrappers = []
    try_again_after = ''

    for account in settings.POST_ACCOUNTS:
        token = Token()
        if token.has_valid_credentials(account.get('username'), account.get('password')):
            pcc = PostcardCreator(token)
            if pcc.has_free_postcard():
                pcc_wrappers.append(pcc)
                logger.info('account {} is valid'.format(account.get("username")))
                if stop_on_first_valid:
                    break
            else:
                next_quota = pcc.get_quota().get('next')
                if next_quota < try_again_after or try_again_after is '':
                    try_again_after = next_quota
                logger.debug('account {} is invalid. '.format(account.get("username")) +
                             'new quota available after {}.'.format(next_quota))
        else:
            logger.warning('wrong user credentials '
                           'for {}'.format(account.get("username")))

    return pcc_wrappers, try_again_after


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt="%Y-%m-%d %H:%M:%S")

    process()
