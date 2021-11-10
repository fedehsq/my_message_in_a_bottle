import unittest
from monolith.background import do_task, lottery
import unittest
from monolith.app import app as tested_app
from bs4 import BeautifulSoup
from werkzeug.datastructures import ImmutableDict
from monolith.database import Message, Messages, db
from flask_login import current_user
from sqlalchemy.orm import sessionmaker, Session
from monolith.background import check_notifications_inbox, check_msg, check_notifications_sent, check_deleted
from monolith.classes.tests.user_test import post_login

# Auxiliary funtions

class TestBackground(unittest.TestCase):
    def test_do_task(self):
        self.assertEqual(do_task(), [])

class TestLottery(unittest.TestCase):
    def test_lottery_task(self):
        self.assertEqual(lottery(), "lottery extraction done!")

# Tester class for celery's background tasks
# 1. Task that deliver messages when the time is expired
# 2. Task that don't deliver messages when the time is not expired
# 3. Task that counts for each client the number of message sent that have been read from the recipient(s)
# 4. Task that counts for each client the number of message not read
class TestCeleryFun(unittest.TestCase):
    def test_message(self):
        app = tested_app.test_client()
        with app:
            # insert a message in the scheduled section of messages
            msg = Message("example@example.com", "example@example.com", "Ciao 1!", "12/12/2010 12:35") 
            id = msg.id
            post_login(app, 'example@example.com', 'admin', 'username')
            to_be_sent = current_user.to_be_sent
            # create a new queue of messages with the message
            messages = Messages().to_messages(to_be_sent)
            messages.enqueue(msg)
            current_user.to_be_sent = messages.to_string()
            # call the delivery task
            check_msg()
            post_login(app, 'example@example.com', 'admin', 'username')
            # check if the user has received the message
            received = current_user.received
            received = Messages().to_messages(received)
            for message in received.messages:
                id_to_check = message.id
            self.assertEqual(id_to_check, id)
    
    def test_bad_time(self):
        app = tested_app.test_client()
        with app:
            # insert a message in the scheduled section of messages
            msg = Message("example@example.com", "example@example.com", "Ciao 2!", "12/12/2022 12:35") 
            id = msg.id
            post_login(app, 'example@example.com', 'admin', 'username')
            to_be_sent = current_user.to_be_sent
            # check if the user to_be_sent queue is empty
            messages = Messages().to_messages(to_be_sent)
            messages.enqueue(msg)
            current_user.to_be_sent = messages.to_string()
            db.session.commit()
            # call the delivery task
            check_msg()
            post_login(app, 'example@example.com', 'admin', 'username')
            # check if the user has still the message in to be sent messages
            # if so, it means that it has not been delivered
            scheduled = current_user.to_be_sent
            scheduled = Messages().to_messages(scheduled)
            for message in scheduled.messages:
                id_to_check = message.id
            self.assertEqual(id_to_check, id)

    
    def test_read(self):
        app = tested_app.test_client()
        with app:
            # insert a message in received with the flag read True
            msg = Message("example@example.com", "example@example.com", "Ciao 4!", "12/12/2010 12:35", True) 
            post_login(app, 'example@example.com', 'admin', 'username')
            received = current_user.received
            # create a new queue of messages with the message
            messages = Messages().to_messages(received)
            messages.enqueue(msg)
            current_user.received = messages.to_string()
            # now I check if the recipient (the same of sender, for simplicity) has read the message
            # the method returns the list (in a string) of messages' id that have been read
            check_notifications_sent()
            post_login(app, 'example@example.com', 'admin', 'username')
            read = current_user.read.split(" ")
            self.assertEqual(len(read), 1)


    def test_toread(self):
        app = tested_app.test_client()
        with app:
            # insert a message in inbox with the flag read False
            msg = Message("example@example.com", "example@example.com", "Ciao 3!", "12/12/2010 12:35") 
            post_login(app, 'example@example.com', 'admin', 'username') 
            received = current_user.received
            # check if the user sent queue is empty
            messages = Messages().to_messages(received)
            messages.enqueue(msg)
            current_user.received = messages.to_string()
            # now the inbox contains 3 message that has not been read yet (1 new message and
            # 2 from the previous tests)
            check_notifications_inbox()
            post_login(app, 'example@example.com', 'admin', 'username')
            to_read = current_user.to_read
            self.assertEqual(to_read, 3)

    def test_check_delited(self): 
        self.assertEqual(check_deleted(),"check_deleted done!")
