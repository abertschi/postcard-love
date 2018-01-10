from pony.orm import *
import datetime
from postcard_creator.postcard_creator import Recipient
import settings
import logging
import sys
from settings import BASEDIR_PICTURES, DEV_IGNORE_SECRET
import os
import shutil

logger = logging.getLogger('postcard-love')

db = Database()
db.bind(provider='sqlite', filename='postcard-love.sqlite', create_db=True)


class StorePostcardRequest:
    def __init__(self, message, picture_path, sender_name='',
                 picture_group='', secret='', priority=0):
        self.priority = priority
        self.message = message
        self.sender_name = sender_name
        self.picture_path = picture_path
        self.picture_group = picture_group
        self.secret = secret


class DbRecipient(db.Entity):
    id = PrimaryKey(int, auto=True)
    firstname = Required(str)
    lastname = Required(str)
    street = Required(str)
    zipcode = Required(int)
    city = Required(str)
    postcards = Set('DbPostcard')


class DbPostcardGroup(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    postcards = Set('DbPostcard')


class DbPostcard(db.Entity):
    id = PrimaryKey(int, auto=True)
    message = Optional(str)
    sender_name = Optional(str)
    picture_path = Required(str)

    priority = Optional(int)
    secret = Optional(str)
    create_date = Required(datetime.datetime, default=datetime.datetime.now())
    send_date = Optional(datetime.datetime)
    is_sent = Required(bool, default=False)
    recipient = Required(DbRecipient)
    picture_group = Optional(DbPostcardGroup)


db.generate_mapping(create_tables=True)
set_sql_debug(settings.DB_DEBUG)


@db_session
def store_postcard(postcard_request, recipient):
    if type(recipient) is not Recipient:
        raise Exception('recipient needs type postcard creator Reciplient')

    r = select(r for r in DbRecipient if
               r.firstname == recipient.prename and
               r.lastname == recipient.lastname and
               r.street == recipient.street and
               r.zipcode == recipient.zip_code and
               r.city == recipient.place)[:]

    if r:
        r = r[0]
    else:
        r = DbRecipient(firstname=recipient.prename,
                        lastname=recipient.lastname,
                        street=recipient.street,
                        city=recipient.place,
                        zipcode=recipient.zip_code)

    g = ''
    if postcard_request.picture_group:
        g = select(g for g in DbPostcardGroup if
                   g.name == postcard_request.picture_group)[:]
        if g:
            g = g[0]
        else:
            g = DbPostcardGroup(name=postcard_request.picture_group)

    p = DbPostcard(message=postcard_request.message,
                   sender_name=postcard_request.sender_name,
                   priority=postcard_request.priority,
                   picture_path=postcard_request.picture_path,
                   secret=postcard_request.secret,
                   picture_group=g,
                   create_date=datetime.datetime.now(),
                   recipient=r)


@db_session
def get_pending_postcards(limit=10):
    cards = select(c for c in DbPostcard if c.is_sent is False) \
                .sort_by(desc(DbPostcard.priority))[:limit]

    for c in cards:
        # load collection so that not proxied outside of db_session
        # TODO: is there a better way to do this?
        c.recipient.firstname

    return cards


@db_session
def mark_postcard_as_sent(postcard_id):
    card = DbPostcard[postcard_id]
    card.is_sent = True
    card.send_date = datetime.datetime.now()
    move_picture_to_sent_folder(card)


@db_session
def get_size_of_pending_postcards():
    return len(select(p for p in DbPostcard if p.is_sent is False)[:])


@db_session
def get_size_of_all_postcards():
    return len(select(p for p in DbPostcard)[:])


@db_session
def move_picture(db_postcard, relative_target):
    """
    the path scheme for a vanilla picture is BASEDIR_PICTURES/k with k = <user>/<image>
    Move picture to BASEDIR_PICTURES/relative_target/k

    :param db_postcard:
    :param relative_target:
    :return: nothing
    """
    target_path_abs = os.path.join(BASEDIR_PICTURES, relative_target)
    if not os.path.exists(target_path_abs):
        logger.info('creating directory {}'.format(target_path_abs))
        os.makedirs(target_path_abs)

    old_path_rel = db_postcard.picture_path
    new_path_rel = os.path.join(relative_target, db_postcard.picture_path)

    old_path_abs = os.path.join(BASEDIR_PICTURES, old_path_rel)
    new_path_abs = os.path.join(BASEDIR_PICTURES, new_path_rel)

    new_dirname = os.path.dirname(new_path_abs)
    if not os.path.exists(new_dirname):
        logger.info('creating directory {}'.format(new_dirname))
        os.makedirs(new_dirname, exist_ok=True)

    try:
        shutil.move(old_path_abs, new_path_abs)
        logger.info('moving {} to {}'.format(old_path_abs, new_path_abs))
        db_postcard.picture_path = new_path_rel
    except Exception:
        logger.exception('can not move file {} to {}'
                         .format(old_path_abs, new_path_abs))
    pass


@db_session
def move_picture_to_cancel_folder(db_postcard):
    move_picture(db_postcard, '_cancel')
    pass


@db_session
def move_picture_to_sent_folder(db_postcard):
    move_picture(db_postcard, '_sent')


@db_session
def print_all_postcards():
    print('showing all postcards')
    DbRecipient.select().show(width=1000)
    DbPostcardGroup.select().show(width=1000)
    DbPostcard.select().show(width=1000)


@db_session
def print_pending_postcards():
    print('='[:1] * 50)
    print('showing pending postcards')
    print('='[:1] * 50)
    DbRecipient.select().show(width=1000)
    DbPostcardGroup.select().show(width=1000)
    select(p for p in DbPostcard if p.is_sent is False).show(width=1000)


@db_session
def print_sent_postcards():
    print('='[:1] * 50)
    print('showing sent postcards')
    print('='[:1] * 50)
    DbRecipient.select().show(width=1000)
    DbPostcardGroup.select().show(width=1000)
    select(p for p in DbPostcard if p.is_sent is True) \
        .sort_by(DbPostcard.send_date).show(width=1000)


@db_session
def clean_up_postcards():
    cards = select(p for p in DbPostcard)[:]
    for c in cards:
        if DEV_IGNORE_SECRET:
            if c.secret is DEV_IGNORE_SECRET:
                move_picture_to_cancel_folder(c)
                continue

        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt="%Y-%m-%d %H:%M:%S")

    p = StorePostcardRequest(message='hi', picture_path='./test')
    r = Recipient(prename='prename', lastname='lastname', street='street', zip_code=0, place='NN')
    # store_postcard(p, r)
    # mark_postcard_as_sent(100)

    print_pending_postcards()
    print_sent_postcards()
    clean_up_postcards()
    pass
