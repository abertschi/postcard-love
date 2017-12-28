from db_access import get_pending_postcards, DbPostcard, DbRecipient, mark_postcard_as_sent
import logging
import settings
import random
import sys
from postcard_creator.postcard_creator import Token, PostcardCreator, Postcard, Recipient, Sender
from xml.sax.saxutils import escape

logger = logging.getLogger('send_job')


def process():
    logger.info('starting send_job to send postcards ...')
    api_wrappers, try_again = _get_pcc_wrapper(stop_on_first_valid=False)
    if not api_wrappers:
        logger.info('no valid accounts. try again {}. terminating send_job'.format(try_again or 'later'))
        exit(1)

    random.shuffle(api_wrappers)
    pending_cards = get_pending_postcards(limit=len(api_wrappers))
    sent_cards = send_cards(api_wrappers, pending_cards)
    logger.info('{} postcards ({}) are sent'.format(len(sent_cards), sent_cards))


def create_api_recipient(db_postcard):
    return Recipient(prename=db_postcard.recipient.fistname,
                     lastname=db_postcard.recipient.lastname,
                     street=db_postcard.recipient.street,
                     zip_code=db_postcard.recipient.zipcode,
                     place=db_postcard.recipient.city)


def create_api_sender(db_postcard):
    sender_firstname = db_postcard.sender_name \
        if db_postcard.sender_name else db_postcard.recipient.fistname

    sender_lastname = db_postcard.recipient.lastname \
        if sender_firstname is not db_postcard.recipient.fistname else ''

    return Sender(prename=escape(sender_firstname),
                  lastname=escape(sender_lastname),
                  street=db_postcard.street,
                  zip_code=db_postcard.zipcode,
                  place=db_postcard.city)


def send_cards(api_wrappers, db_cards):
    card_i = 0
    sent_cards = []

    for api_wrapper in api_wrappers:
        if card_i >= len(db_cards):
            break

        pending_card = db_cards[card_i]
        card_i = card_i + 1

        api_picture_stream = None
        api_message = pending_card.message

        api_card = Postcard(sender=create_api_sender(pending_card),
                            recipient=create_api_recipient(pending_card),
                            picture_stream=api_picture_stream,
                            message=escape(api_message))

        response = api_wrapper.send_free_card(postcard=api_card, mock_send=settings.MOCK_SEND)
        if response:
            logger.info('postcard id:{} is sent'.format(pending_card.id))
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
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    process()
