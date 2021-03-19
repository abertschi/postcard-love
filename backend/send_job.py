from db_access import get_pending_postcards, \
    mark_postcard_as_sent, get_size_of_pending_postcards, mark_postcard_as_cancelled
import logging
import settings
import random
import sys
import os
from postcard_creator.postcard_creator import Token, PostcardCreator, Postcard, Recipient, Sender
from xml.sax.saxutils import escape
import emoji
import unicodedata
import codecs
import image_utility
from html.entities import codepoint2name

logger = logging.getLogger('send_job')


def _html_replace(exc):
    if isinstance(exc, (UnicodeEncodeError, UnicodeTranslateError)):
        s = [u'&%s;' % codepoint2name[ord(c)]
             for c in exc.object[exc.start:exc.end]]
        return ''.join(s), exc.end
    else:
        raise TypeError("can't handle {}".format(exc.__name__))


codecs.register_error('html_replace', _html_replace)


def process():
    logger.info('starting send_job to send postcards ...')
    api_wrappers, try_again = _get_pcc_wrapper(stop_on_first_valid=False)
    if not api_wrappers:
        logger.info('no valid accounts. try again {}. terminating send_job'.format(try_again or 'later'))
        exit(1)

    random.shuffle(api_wrappers)
    pending_cards = get_pending_postcards()

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


def send_cards(api_wrappers, db_cards):
    card_i = 0
    sent_cards = []
    try_only_one_wrapper = False

    for api_wrapper in api_wrappers:
        if try_only_one_wrapper:
            # on exception we may rather leave and not try more wrappers
            break

        while card_i < len(db_cards):
            pending_card = db_cards[card_i]
            card_i = card_i + 1

            if not image_utility.can_printout_card(pending_card):
                # Todo, reuse wrapper if card was cancelled
                logger.info('card {} was flagged as cancelled.'.format(pending_card.id))
                mark_postcard_as_cancelled(pending_card.id)
                continue

            try:
                response = send_card_with_wrapper(api_wrapper, pending_card)
                if response:
                    logger.debug('postcard id:{} is sent'.format(pending_card.id))
                    mark_postcard_as_sent(postcard_id=pending_card.id)
                    sent_cards.append(pending_card.id)
                    # on success we break out of the loop to use the next
                    # api wrapper and potentially send more cards
                    break
                else:
                    logger.info('postcard id:{} is not sent. try next one'.format(pending_card.id))
                    # on mock send or no send but no exception try next card if more cards left
                    continue

            except Exception as e:
                logger.warning('error in sending card {}'.format(pending_card.id))
                logger.warning(e)
                logger.warning('trying next card')
                try_only_one_wrapper = True
                # on exception there may be an issue with the card itself, so try
                # next card as long as there are pending cards
                continue

    return sent_cards


def send_card_with_wrapper(wrapper, card):
    file = os.path.join(settings.BASEDIR_PICTURES, card.picture_path)
    api_picture_stream = open(file, 'rb')
    api_message = escape(card.message)[:400]

    logger.debug('uploading file {}'.format(file))
    logger.debug('message: ' + api_message)

    api_card = Postcard(sender=create_api_sender(card),
                        recipient=create_api_recipient(card),
                        picture_stream=api_picture_stream,
                        message=api_message)
    try:
        response = wrapper.send_free_card(postcard=api_card, mock_send=settings.MOCK_SEND)
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
        response = wrapper.send_free_card(postcard=api_card, mock_send=settings.MOCK_SEND)

    return False if settings.MOCK_SEND else response


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


def _escape(string):
    return escape(emoji.demojize(string))


def _remove_special_characters(string):
    return unicodedata.normalize('NFKD', string).encode('iso_8859_1', 'ignore').decode('utf-8')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt="%Y-%m-%d %H:%M:%S")

    process()
