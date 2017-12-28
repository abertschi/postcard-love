import sqlite3
from pony.orm import *
import time, datetime
from postcard_creator.postcard_creator import Recipient

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
set_sql_debug(True)


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

    return cards


@db_session
def mark_postcard_as_sent(postcard_id):
    card = DbPostcard[postcard_id]
    card.is_sent = True
    card.send_date = datetime.datetime.now()


@db_session
def print_all_postcards():
    print('showing all postcards')
    DbRecipient.select().show(width=1000)
    DbPostcardGroup.select().show(width=1000)
    DbPostcard.select().show(width=1000)


@db_session
def print_pending_postcards():
    print('showing pending postcards')
    DbRecipient.select().show(width=1000)
    DbPostcardGroup.select().show(width=1000)
    select(p for p in DbPostcard if p.is_sent is False).show(width=1000)


@db_session
def print_sent_postcards():
    print('showing sent postcards')
    DbRecipient.select().show(width=1000)
    DbPostcardGroup.select().show(width=1000)
    select(p for p in DbPostcard if p.is_sent is True) \
        .sort_by(DbPostcard.send_date).show(width=1000)


if __name__ == '__main__':
    p = StorePostcardRequest(message='hi', picture_path='./test')
    r = Recipient(prename='prename', lastname='lastname', street='street', zip_code=0, place='NN')
    # store_postcard(p, r)
    # mark_postcard_as_sent(100)
    print_pending_postcards()
    print_sent_postcards()
    pass
