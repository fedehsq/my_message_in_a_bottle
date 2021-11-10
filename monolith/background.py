from os import read
from re import M
import re
from celery import Celery
from celery.schedules import crontab
from monolith.database import User, db, Messages
from datetime import datetime, timedelta
from random import seed, randint

BACKEND = BROKER = 'redis://localhost:6379'
celery = Celery(__name__, backend=BACKEND, broker=BROKER)
_APP = None

#celery.conf.timezone = 'Europe/Rome'
#celery.conf.timezone = 'Europe/Rome'
celery.conf.beat_schedule = {
    "check-every-minute-msg": {
        "task": "check_messages",
        "schedule": timedelta(seconds=60),
     }, 
    "inbox_notifications": {
        "task": "notifications_inbox",
        "schedule": timedelta(seconds = 60),
    },
    "sent_notifications": {
        "task": "notifications_sent",
        "schedule": timedelta(seconds = 60),
    },
    "lottery-game":{
        "task": "lottery_task",
        "schedule": timedelta(days = 30)     #day_of_month="1" for a monthly lottery, 60 seconds to do tests 
    },
    "check_deleted_users":{
        "task": "check_deleted_users",
        "schedule": timedelta(seconds = 60) 
    }
}

# celery periodic task to detect which of the message sent, has been received and read 
@celery.task(name = 'notifications_sent')
def check_notifications_sent():
    with _APP.app_context():
        users = db.session.query(User)
        # for each registered user
        for user in users:
            read_list = "" # list of id in which I save the read msg id
            # get the list of sent messages
            sent = user.sent
            sent = Messages().to_messages(sent)

            # for each message sent check if the recipient has read the message
            for msg in sent.messages:
                # only if the sender has not received the notification yet
                if msg.read == False:
                    # get dest
                    dest = msg.dest
                    # get message id
                    id = msg.id

                    # get the list of recipients from the string
                    dest_list = dest.split(",")
                    len_lis = len(dest_list)
                    
                    for i in range(0, len_lis):
                        dest_list[i] = dest_list[i].strip()
                
                    # for each dest, check if it has read the message
                    for dest in dest_list:
                        q = db.session.query(User).filter(User.email == dest)
                        rec = q.first()
                        # get the received list msg of the current dest
                        inbox = rec.received
                        inbox = Messages().to_messages(inbox)

                        # search in inbox for the current msg (with id) and check if it has been read
                        for m in inbox.messages:
                            if m.id == id and m.read == True:
                                if len(read_list) == 0:
                                    read_list = read_list + str(id)
                                else:
                                    read_list = read_list + " " + str(id)
            # update the list of msg id that have been read
            user.read = read_list
            print("Messaggi che il dest ha letto: ")
            print(read_list)
            db.session.commit()

#celery periodic task that extract a number and check if there are winners
@celery.task(name = 'lottery_task')
def lottery():
    with _APP.app_context():
        #generate random number between 1-100
        seed()
        number_extract = randint(1,100)
        #number_extract = 10
        users = db.session.query(User)
        for usr in users:
            if usr.lottery_number == number_extract:
                usr.points +=100
            #reset the user's lottery number for the next extraction
            usr.lottery_number = 0 
        db.session.commit()
        return "lottery extraction done!"

# celery periodic task to detect the number of message that have not been read
@celery.task(name = 'notifications_inbox')
def check_notifications_inbox():
    with _APP.app_context():
        users = db.session.query(User)
        # for each registered user
        for user in users:
            to_read = 0
            # get the list of received msg
            inbox = user.received
            inbox = Messages().to_messages(inbox)

            # for each message, control the flag read
            for msg in inbox.messages:
                if msg.read == False:
                    # count the number of messages not read
                    to_read = to_read + 1
            # update the number of notifications to read
            user.to_read = to_read
            db.session.commit()
            print("Messaggi da leggere: " + str(to_read))


@celery.task(name = 'check_messages')
def check_msg():
    with _APP.app_context():
        # for each registered user
        users = db.session.query(User)
        for user in users:
            # get the to_be_sent list of the sender
            delivery_list = user.to_be_sent

            # get the Message list and check if there is one
            # with expired time of delivery
            delivery_list = Messages().to_messages(delivery_list)

            for msg in delivery_list.messages:
                
                #retrieving the time (str) in which the message should be delivered
                delivery_time = msg.time 
                # convert it in datetime 
                delivery_time = datetime.strptime(delivery_time, '%d/%m/%Y %H:%M') 
                # get the current time 
                current_time = datetime.now()

                # if the message has a delivery time corresponding to now or to a passed time, it will be delivered
                if (current_time > delivery_time):
                    # send message
                    recipient_mail = msg.dest
                    # check if there is more than a recipient
                    recipients_list = recipient_mail.split(",")
                    len_lis = len(recipients_list)
                    for i in range(0,len_lis):
                        recipients_list[i] = recipients_list[i].strip()
                    
                    # send the message to each recipient
                    for rec in recipients_list:
                        q = db.session.query(User).filter(User.email == rec)
                        dest = q.first()
                        # get the received messages of dest
                        received = dest.received
                        # create a new queue of messages with the received message
                        messages = Messages()
                        messages.enqueue(msg)
                        # check if the dest received queue is empty
                        if (received == '[]'):
                            dest.received = messages.to_string()
                        else:
                            messages = Messages().to_messages(received)
                            messages.enqueue(msg)
                            dest.received = messages.to_string()
                        db.session.commit()

            
                    # remove msg from to_be_sent list of the sender
                    # retrieve the old list of to_be_sent messages (str)
                    to_be_sent = user.to_be_sent
                    # convert the string into a list of Message
                    messages = Messages().to_messages(to_be_sent)
                    # remove the sent message from the list
                    for item in messages.messages:
                        if item.to_string() == msg.to_string():
                            messages.messages.remove(item)
                    
                    # convert the updated list in string and put it in the database 
                    user.to_be_sent = messages.to_string()
                    
                    # put the message in the sent list of the sender
                    # get the sent messages of the sender
                    sent = user.sent
                    # create a new queue of messages with the sent message
                    messages = Messages()
                    messages.enqueue(msg)
                    # check if the user sent queue is empty
                    if (sent == '[]'):
                        user.sent = messages.to_string()
                    else:
                        messages = Messages().to_messages(sent)
                        messages.enqueue(msg)
                        user.sent = messages.to_string()
                    db.session.commit()

@celery.task(name = "check_deleted_users")
def check_deleted():
    with _APP.app_context():
        # for each registered user
        users = db.session.query(User)
        for user in users:
            if user.deleted == True:
                if user.to_be_sent == "[]":
                    db.session.query(User).filter(User.email == user.email).delete()
                    db.session.commit()
        return "check_deleted done!"


@celery.task
def do_task():
    global _APP
    # lazy init
    if _APP is None:
        from monolith.app import create_app
        app = create_app()
        db.init_app(app)
        _APP = app
    else:
        app = _APP
    return []