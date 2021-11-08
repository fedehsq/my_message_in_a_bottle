from monolith.database import Message, Messages
import unittest
from monolith.classes.tests.user_test import tested_app, get_page_id, LOGIN_PAGE_TITLE, post_login, INBOX,MAILBOX
import json
from monolith.background import check_msg
from flask_login import current_user
from monolith.classes.tests.user_test import post_and_get_result_id, get_page_id
from monolith.views.message import search_messages
# Tester class for the auxiliary classe Messages operations
# 1. Create an object with Messages type (builder)
# 2. Enqueue a Message in the list of Message(s)

class TestMessageClasses(unittest.TestCase):

    def test_enqueue(self):
        msg = Message("example@example.com", "example@example.com", "Ciao!", "12/12/2010 12:35", False)
        msgs = Messages()
        msgs.enqueue(msg)
        msg_id = msg.id
        self.assertEqual(msgs.to_string(), '["{\\"id\\": \\"' + (msg_id) + '\\", \\"sender\\": \\"example@example.com\\", \\"dest\\": \\"example@example.com\\", \\"body\\": \\"Ciao!\\", \\"time\\": \\"12/12/2010 12:35\\", \\"image\\": \\"\\", \\"read\\": false, \\"bold\\": false, \\"italic\\": false, \\"underline\\": false}"]')

    def test_tostring(self):
        msg = Message("example@example.com", "example@example.com", "Ciao!", "12/12/2010 12:35", False)
        msgs = Messages()
        msgs.enqueue(msg)
        msg_id = msg.id
        self.maxDiff = None
        self.assertEqual(msgs.to_string(), '["{\\"id\\": \\"' + str(msg_id) + '\\", \\"sender\\": \\"example@example.com\\", \\"dest\\": \\"example@example.com\\", \\"body\\": \\"Ciao!\\", \\"time\\": \\"12/12/2010 12:35\\", \\"image\\": \\"\\", \\"read\\": false, \\"bold\\": false, \\"italic\\": false, \\"underline\\": false}"]' )
        

class TestInbox(unittest.TestCase):
    def test_inbox(self):
        app = tested_app.test_client()
        # ------ GET: LOGOUT -----
        title = get_page_id(app, '/logout', 'page_title')
        self.assertEqual(title, LOGIN_PAGE_TITLE)
        # ------ Test1: inbox without login -----
        title = get_page_id(app, '/mailbox/inbox', 'page_title')
        self.assertEqual(title, LOGIN_PAGE_TITLE)
            # ------ Test2: inbox with login -----
        with app:
            post_login(app, 'example@example.com', 'admin', 'username')
            title = get_page_id(app, '/mailbox/inbox', 'page_title')
            self.assertEqual(title, INBOX)
            # ------ Test3: inbox with non-existing id -----
            title = get_page_id(app, '/mailbox/inbox/12345', 'page_title')
            self.assertEqual(title, MAILBOX)
            # ------ Test4: inbox with existing id -----
            msg = Message("example@example.com", "example@example.com", "Ciao!", "12/12/2010 12:35") 
            id = msg.id
            # create a new queue of messages with the message
            messages = Messages()
            messages.enqueue(msg)
            current_user.to_be_sent = messages.to_string()
            check_msg()
            post_login(app, 'example@example.com', 'admin', 'username')
            received = current_user.received
            received = Messages().to_messages(received)
            for message in received.messages:
                id_to_check = message.id
            self.assertEqual(id_to_check, id)
            url="/mailbox/inbox/"+id
            response=get_page_id(app,url,"page_title")
            self.assertEqual(response, "Message")

            # ------ Test5: inbox with existing id and delete-----
            response=post_and_get_result_id(app,'/mailbox/inbox',{"delete":id},"page_title")
            self.assertEqual(response, INBOX)

class TestForward(unittest.TestCase):
    def test_forward(self):
        app = tested_app.test_client()
        with app:
            # ------ Test1: forward an existing message-----

            post_login(app, 'example@example.com', 'admin', 'username')
            msg = Message("example@example.com", "example@example.com", "Ciao!", "12/12/2010 12:35") 
            id = msg.id
            # create a new queue of messages with the message
            messages = Messages()
            messages.enqueue(msg)
            current_user.to_be_sent = messages.to_string()
            check_msg()
            post_login(app, 'example@example.com', 'admin', 'username')
            received = current_user.received
            received = Messages().to_messages(received)
            for message in received.messages:
                id_to_check = message.id
            self.assertEqual(id_to_check, id)
            url="/mailbox/forward/"+id
            response=get_page_id(app,url,"page_title")
            self.assertEqual(response, "Message")

            # ------ Test2: forward with wrong id-----
            url="/mailbox/forward/"+"-1"
            response=get_page_id(app,url,"page_title")
            self.assertEqual(response, MAILBOX)
            # ------ removing the created message-----
            response=post_and_get_result_id(app,'/mailbox/inbox',{"delete":id},"page_title")
            self.assertEqual(response, INBOX)

class TestReply(unittest.TestCase):
    def test_reply(self):
        app = tested_app.test_client()
        with app:
            # ------ Test1: correct reply-----
            post_login(app, 'example@example.com', 'admin', 'username')
            msg = Message("example@example.com", "example@example.com", "Ciao!", "12/12/2010 12:35") 
            id = msg.id
            # create a new queue of messages with the message
            messages = Messages()
            messages.enqueue(msg)
            current_user.to_be_sent = messages.to_string()
            check_msg()
            post_login(app, 'example@example.com', 'admin', 'username')
            received = current_user.received
            received = Messages().to_messages(received)
            for message in received.messages:
                id_to_check = message.id
            self.assertEqual(id_to_check, id)
            url="/mailbox/reply/"+id
            response=get_page_id(app,url,"page_title")
            self.assertEqual(response, "Message")
             # ------ Test2: wrong reply-----
            url="/mailbox/reply/"+"-1"
            response=get_page_id(app,url,"page_title")
            self.assertEqual(response, MAILBOX)
            # ------ removing the created message-----
            response=post_and_get_result_id(app,'/mailbox/inbox',{"delete":id},"page_title")
            self.assertEqual(response, INBOX)

class TestScheduled(unittest.TestCase):
    def test_scheduled(self):
        app = tested_app.test_client()
        # ------ Test get mailbox scheduled with user not logged -----
        title = get_page_id(app, '/mailbox/scheduled/', 'page_title')
        self.assertEqual(title, LOGIN_PAGE_TITLE)
        with app:
            # ------ Test1: scheduled without id-----
            post_login(app, 'example@example.com', 'admin', 'username')
            response=get_page_id(app,"mailbox/scheduled/","page_title")
            self.assertEqual(response, "Scheduled")
            # ------ Test2: scheduled with wrong id-----
            url="/mailbox/scheduled/"+"-1"
            response=get_page_id(app,url,"page_title")
            self.assertEqual(response, MAILBOX)


class TestSent(unittest.TestCase):
    def test_sent(self):
        app = tested_app.test_client()
        # ------ Test get mailbox sent with user not logged -----
        title = get_page_id(app, '/mailbox/sent/', 'page_title')
        self.assertEqual(title, LOGIN_PAGE_TITLE)
        with app:
            # ------ Test1: send with correct id-----
            post_login(app, 'example@example.com', 'admin', 'username')
            msg = Message("example@example.com", "example@example.com", "Ciao!", "12/12/2010 12:35") 
            id = msg.id
            # create a new queue of messages with the message
            messages = Messages()
            messages.enqueue(msg)
            current_user.to_be_sent = messages.to_string()
            check_msg()
            post_login(app, 'example@example.com', 'admin', 'username')
            received = current_user.received
            received = Messages().to_messages(received)
            for message in received.messages:
                id_to_check = message.id
            self.assertEqual(id_to_check, id)
            url="/mailbox/sent/"+id
            response=get_page_id(app,url,"page_title")
            self.assertEqual(response, "Message")
            # ------ Test2: send without id-----
            url="/mailbox/sent/"
            response=get_page_id(app,url,"page_title")
            self.assertEqual(response, "Sent")
            # ------ Test3: send with wrong id-----
            url="/mailbox/sent/"+"-1"
            response=get_page_id(app,url,"page_title")
            self.assertEqual(response, MAILBOX)
            # ------ Test4: removing from the sent list-----
            response=post_and_get_result_id(app,'/mailbox/sent',{"delete":id},"page_title")
            self.assertEqual(response, "Sent")
            # ------ removing the created message-----
            response=post_and_get_result_id(app,'/mailbox/inbox',{"delete":id},"page_title")
            self.assertEqual(response, INBOX)


class TestSearchMessages(unittest.TestCase):
    def test_search_messages(self):
        app = tested_app.test_client()

        with app:     
            #Create urls to test the searching of the message 
            BASE_URL = "https://localhost:5000/mailbox"
            TEST1 = BASE_URL + "?msg=prova&date=&user="
            #Test 1 - The user is not logged  
            resp=get_page_id(app,BASE_URL,"page_title")
            self.assertEqual(resp,LOGIN_PAGE_TITLE)   
            #Test 2 - The user is logged and requests the mailbox page
            post_login(app, 'example@example.com', 'admin', 'username')

            resp=get_page_id(app,BASE_URL,"page_title")
            self.assertEqual(resp,"Mailbox")

            resp=get_page_id(app,TEST1,"page_title")
            self.assertEqual(resp,"Search")
            resp=search_messages("","","12345")
            self.assertEqual(resp,"error")