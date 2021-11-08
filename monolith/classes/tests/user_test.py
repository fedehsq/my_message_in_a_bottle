import unittest

from monolith.app import app as tested_app
from bs4 import BeautifulSoup
from werkzeug.datastructures import ImmutableDict
from monolith.database import Message, Messages, db
from flask_login import current_user
from sqlalchemy.orm import sessionmaker, Session
from monolith.background import check_notifications_inbox, check_msg, check_notifications_sent

from monolith.views.message import draft

#### THE IDEA IS TO PUT IN EVERY HTML PAGE AN UNIQUE ID 
#### THAT WILL BE SEARCHED BY PYTEST TO COMPUTE THE RESULT

# Keywords used for testing: searched words in the html pages to understand the result.

# LOGIN KEYWORDS:
LOGIN_PAGE_TITLE = 'My message in a bottle'
USERNAME = 'Admin'
WRONG_CREDENTIALS = 'Incorrect username or password.'

# REGISTER KEYWORDS:
REGISTRATION_PAGE_TITLE = 'Registration'
REGISTRATION_DONE = 'You are registered! Please log in.'
WRONG_EMAIL = 'Email already registered.'
WRONG_DATE = 'Date format DD/MM/YYYY.'

# PROFILE PAGE KEYWORDS:
PROFILE_PAGE_TITLE = 'Profile'
UPDATE_DONE = 'Personal info updated. Return to dashboard'
WRONG_DATE = 'Date format DD/MM/YYYY.'

# UNSUBSCRIBED PAGE KEYWORDS
UNSUBSCRIBED_PAGE_TITLE = 'Unsubscribed'

# MESSAGE KEYWORDS
MSG_CREATION_PAGE_TITLE = "Message"
MSG_DRAFT = 'Draft! back to homepage.'
MSG_SCHEDULED = 'Scheduled! back to homepage.'
WRONG_DATE_TIME = 'Date format DD/MM/YYYY hh:mm'
WRONG_WORDS = 'Change body!'

# MAILBOX KEYWORDS
MAILBOX = "Mailbox"
INBOX="Inbox"
# DRAFT KEYWORDS
DRAFT_PAGE_TITLE = 'Draft'

# REPORT
REPORT_PAGE_TITLE = "User report"
WRONG_REPORT_EMAIL = "No user with this email."

# LOTTERY
LOTTERY_PAGE_TITLE = "Play Lottery"
LOTTERY_ERROR_NUMBER = "Number not allowed! Please choose another number between 1 and 100"

# ----- Auxiliary functions used in the tests ------ 

# Get the requested page, an unique id is assigned in one field
# on the html page to recognize the field with which to test.
def get_page_id(app, page, html_id):
    # Request the page
    response = app.get(page, follow_redirects = True)
    # extract the html page from the response
    html = str(response.data, 'utf8')
    # parse this page
    soup = BeautifulSoup(html, 'html.parser')
    # access and return the interesting field to check
    message = soup.find(id = html_id).text
    return message

# Try to post on the requested page, an unique id is assigned in one field
# on the html page to recognize the field with which test.
def post_and_get_result_id(app, page, data, html_id):
    # Pass the parameters that will fill the login form: 
    # in case of successfully login, generally, a message appears on the 
    # requested page or there will be a redirection to another page,
    # otherwise an error message appears on this page.
    # These possibilities are tested to understand the response.
    response = app.post(page, 
        data = data, 
        follow_redirects = True)
    # extract the html page from the response
    html = str(response.data, 'utf8')
    # parse this page
    soup = BeautifulSoup(html, 'html.parser')
    # access and return the interesting field to check
    message = soup.find(id = html_id).text
    return message

# Try to login an user, an unique id is assigned in one field
# on the html page to recognize the field with which test.
def post_login(app, email, password, html_id):
    # Pass the parameters that will fill the login form: 
    # In case of successfully login, there will be a redirection to the homepage
    # otherwise an error message appears on this page (wrong username or password).
    # These two possibilities are tested to understand the response.
    return post_and_get_result_id(app, '/login', 
        {'email': email, 'password': password}, 
        html_id)

# Try to register an user, an unique id is assigned in one field
# on the html page to recognize the field with which test.
def post_register(app, email, firstname, lastname, password, date_of_birth, wrong_words, html_id): 
    # Pass the parameters that will fill the registration form.
    # In case of successfully registration, a message appears on the 
    # screen that suggest to the user to go to the login page.
    # In case of incorrect registration, two messages can appears in this page.
    #   1: email already used
    #   2: wrong date format
    # These messages are checked to test the proper case (success or kind of error). 
    return post_and_get_result_id(app, '/register', 
        {'email': email, 'firstname': firstname, 'lastname': lastname, 
        'password': password, 'date_of_birth': date_of_birth,  'forbidden_words': wrong_words}, 
        html_id)

# Try to update an user info, an unique id is assigned in one field
# on the html page to recognize the field with which test.
def post_update_profile(app, email, firstname, lastname, password, date_of_birth, html_id): 
    # Pass the parameters that will fill the info profile form.
    # In case of successfully update, 
    # a message appears to the page (suggest to come back to dashboard)
    # In case of wrong form filling a message shows the error (only the date can be wrong)
    return post_and_get_result_id(app, '/profile', 
        {'email': email, 'firstname': firstname, 'lastname': lastname, 
        'password': password, 'date_of_birth': date_of_birth}, 
        html_id)


# Try to save/schedule a message, an unique id is assigned in one field
# on the html page to recognize the field with which test.
def post_message(app, receiver, body, date, time, choice, html_id):
    # Pass the parameters that will fill the message form: 
    # In case of successfully edits, there will be 2 different messages
    # according to the tapped button
    #   1. Draft ok
    #   2. Schedule ok
    # otherwise an error message appears on this page (wrong date/time).
    # These two possibilities are tested to understand the response.

    return post_and_get_result_id(app, '/message' + "/" + receiver, 
        {'receiver': receiver, 'body': body, 'date': date, 
        'time': time, 'choice': choice}, 
        html_id)

# Edit a message through message id
def post_edit_message(app, receiver, body, date, time, choice, message_id, html_id):
    # Pass the parameters that will fill the message form: 
    # In case of successfully edits, there will be 2 different messages
    # according to the tapped button
    #   1. Draft ok
    #   2. Schedule ok
    # otherwise an error message appears on this page (wrong date/time).
    # These two possibilities are tested to understand the response.
    return post_and_get_result_id(app, '/mailbox/draft/' + message_id, 
        {'receiver': receiver, 'body': body, 'date': date, 
        'time': time, 'choice': choice}, 
        html_id)

# Try to report a user
def post_report(app, email, reason, html_id):
    page = '/users/report/' + email
    return post_and_get_result_id(app, page, 
        {'email': email, 'reason': reason}, html_id)

#Try to post a lottery number
def post_lottery(app, number, html_id):
    return post_and_get_result_id(app, '/playLottery', {'number': number}, html_id)


# Tester class for the login operation.
# The possible cases are 3: 
#   1. The user requests for the login page (GET).
#   2. The user inserts correct email and password (POST).
#   3. The user inserts wrong email and/or password (POST).
#   4. The user try to get the login page when he is already logged. (GET)
class TestLogin(unittest.TestCase):

    def test_login(self):
        app = tested_app.test_client()

        # ------ GET: LOGIN PAGE ------
        title = get_page_id(app, '/login', 'page_title')
        self.assertEqual(title, LOGIN_PAGE_TITLE)

        # ------ POST: CORRECT LOGIN -----
        username = post_login(app, 'example@example.com', 'admin', 'username')
        self.assertEqual(username, USERNAME)

        # ------ GET: LOGOUT -----
        title = get_page_id(app, '/logout', 'page_title')
        self.assertEqual(title, LOGIN_PAGE_TITLE)

        # ----- POST: INCORRECT LOGIN, WRONG CREDENTIALS ------
        wrong_credentials = post_login(app, 'a', 'b', 'wrong_credentials')
        self.assertEqual(wrong_credentials, WRONG_CREDENTIALS)

        # ----- GET: LOGIN PAGE REQUEST WHEN THE CLIENT IS ALREADY LOGGED ------
        with app:                
            post_login(app, 'example@example.com', 'admin', 'username')
            username = get_page_id(app, '/login', 'username')
            # Client is already logged and will be redirected to his dashboard
            self.assertEqual(username, USERNAME)

# Tester class for the regoster operation.
# The possible cases are 5:
#   1. The user requests for the registration page. (GET)
#   2. The user inserts correct email and date of birth. (POST)
#   3. The user inserts an email already registered. (POST)
#   4. The user inserts a date format not correct. (POST)
#   5. The user inserts an email already registered and a date format not correct. (POST)
#   6. The user try to get the registration page when he is already logged. (GET)
class TestRegister(unittest.TestCase):

    def test_register(self):    
        app = tested_app.test_client()
        # ------ GET: REGISTER PAGE ------
        response = get_page_id(app, '/register', 'page_title')
        self.assertEqual(response, REGISTRATION_PAGE_TITLE) 
        
        # ------ CORRECT REGISTRATION -----
        response = post_register(app, 'pao@pao.com', 'paola', 
            'petri', 'pao', '05/06/1998', 'parolaccia', 'registration_done')
        self.assertEqual(response, REGISTRATION_DONE)

        # ----- INCORRECT REGISTRATION: EMAIL ALREADY REGISTERED ------
        response = post_register(app, 'pao@pao.com', 'paola', 
            'petri', 'pao', '05/06/1998', 'parolaccia', 'wrong_email')
        self.assertEqual(response,  WRONG_EMAIL)

        # ----- INCORRECT REGISTRATION: DATE OF BIRTH IN INCORRECT FORMAT ------
        response = post_register(app, 'a@b', 'a', 
            'b', 'ab', '055/06/98', 'parolaccia', 'wrong_date')
        self.assertEqual(response, WRONG_DATE)

        # ----- INCORRECT REGISTRATION: EMAIL ALREADY REGISTERED AND DATE OF BIRTH IN INCORRECT FORMAT ------
        response = post_register(app, 'pao@pao.com', 'paola', 
            'petri', 'pao', '5/06/98', 'parolaccia', 'wrong_email')
        response1 = post_register(app, 'pao@pao.com', 'paola', 
            'petri', 'pao', '5/06/98', 'parolaccia', 'wrong_date')
        self.assertEqual(response,  WRONG_EMAIL)
        self.assertEqual(response1,  WRONG_DATE)

        # ----- GET: REGISTRATION PAGE REQUEST WHEN THE CLIENT IS ALREADY LOGGED ------
        with app:                
            post_login(app, 'example@example.com', 'admin', 'username')
            # Client is already logged and requests for the registration page
            username = get_page_id(app, '/register', 'username')
            self.assertEqual(username, USERNAME) 

class TestGetPostReport(unittest.TestCase):
    def test_get_post_report(self):
        # ----- 1 GET: REPORT PAGE REQUEST WHEN THE CLIENT ISN'T LOGGED ------
        app = tested_app.test_client()
        
        title = get_page_id(app, '/users/report/pao@pao.com', 'page_title')
        # Client isn't logged, it is redirect to the login page
        self.assertEqual(title, LOGIN_PAGE_TITLE)

        # ------ 2 GET: REPORT PAGE REQUEST WHEN THE CLIENT IS LOGGED ------
        with app:
            # login the user              
            username = post_login(app, 'example@example.com', 'admin', 'username')
            title = get_page_id(app, '/users/report/pao@pao.com', 'page_title')
            # Client is logged, it is on the report page
            self.assertEqual(title, REPORT_PAGE_TITLE)

            # ------ 3 POST A REPORT, it works only before tests on update profile information ------
            post_report(app, "example@example.com", "reason", 'username')
            self.assertEqual(username,USERNAME)

            # ------ 4 POST A REPORT WITH WRONG EMAIL ------
            error_email = post_report(app, "wrong_email@wrong.com", "reason", "wrong_email")
            self.assertEqual(error_email, WRONG_REPORT_EMAIL)

class TestGetPostLottery(unittest.TestCase):
    def test_get_post_lottery(self):
        # ----- 1 GET: LOTTERY PAGE REQUEST WHEN THE CLIENT ISN'T LOGGED ------
        app = tested_app.test_client()
        title = get_page_id(app, '/playLottery', 'page_title')
        # Client isn't logged, it is redirect to the login page
        self.assertEqual(title, LOGIN_PAGE_TITLE)

                # ------ 2 GET: LOTTERY PAGE REQUEST WHEN THE CLIENT IS LOGGED ------
        with app:
            # login the user              
            username = post_login(app, 'example@example.com', 'admin', 'username')
            title = get_page_id(app, '/playLottery', 'page_title')
            # Client is logged, it is on the play lottery page
            self.assertEqual(title, LOTTERY_PAGE_TITLE)

                # ------ 3 POST LOTTERY NUMBER SUCCEDED ------
            post_lottery(app, 22, "username")
            self.assertEqual(username, USERNAME)

                # ------ 4 POST WITH INCORRECT NUMBER ------
            error_number = post_lottery(app, 120, "error_number")
            self.assertEqual(error_number, LOTTERY_ERROR_NUMBER)


# Tester class for the info user page operation.
# The possible cases are 4:
#   1. The user requests for the profile info page when he isn't logged. (GET)
#   2. The user requests for the profile info page when he is logged. (GET)
#   3. The user updates correctly his infos (the date of birth). (POST)
#   4. The user inserts a date format not correct. (POST)
class TestUserInfo(unittest.TestCase):

    def test_get_profile(self):
        # ----- 1 GET: PROFILE PAGE REQUEST WHEN THE CLIENT ISN'T LOGGED ------
        app = tested_app.test_client()
        title = get_page_id(app, '/profile', 'page_title')
        # Client isn't logged, it is redirect to the login page
        self.assertEqual(title, LOGIN_PAGE_TITLE)
        # ------ 2 GET: PROFILE PAGE REQUEST WHEN THE CLIENT IS LOGGED ------
        with app:
            # login the user              
            post_login(app, 'example@example.com', 'admin', 'username')
            title = get_page_id(app, '/profile', 'page_title')
            # Client is logged, it is on the profile page
            self.assertEqual(title, PROFILE_PAGE_TITLE)
       
        # ------ 3 POST: USER UPDATES CORRECTLY HIS INFO (DATE OF BIRTH) ------
            response = post_update_profile(app, '', 'a', 
                'b', 'admin', '05/06/1998', 'profile_edited')
            self.assertEqual(response, UPDATE_DONE)

        # ------ 4 POST: USER DOESN'T UPDATE CORRECTLY HIS INFO (WRONG DATE OF BIRTH) ------
            response = post_update_profile(app, '', 'a', 
                'b', 'admin', '055/056/15998', 'wrong_date')
            self.assertEqual(response, WRONG_DATE)

class TestUserOperations(unittest.TestCase):

    def test_get_users(self):
        app = tested_app.test_client()
        response = app.get('/users')
        # Client isn't logged, it is redirect to the login page
        self.assertEqual(response.status_code, 302)
        title = get_page_id(app, '/login', 'page_title')
        self.assertEqual(title, LOGIN_PAGE_TITLE)

        # ------ POST: CORRECT LOGIN -----
        with app:                
            post_login(app, 'example@example.com', 'admin', 'username')
            response = app.get('/users')
            # Client is now logged, it can sees registered users
            self.assertEqual(response.status_code, 200)
            #Client tries to search the user admin
            response = get_page_id(app,'/users?search=admin','results')
            self.assertEqual(response, "You searched: admin")
# Tester class for message creation, send and save operations
# The possible cases are 
# 1. Get the message creation page when user isn't logged (GET)
# 2. Get the message creation page when user is logged (GET)
# 3. Write a message and schedule it (POST)
# 4. Write a message and save it as a draft (POST)
# 5. Write an incorrect message (wrong date) (POST)

# Tester class for the message creation.
class TestMessageCreation(unittest.TestCase):
    def test_message_creation(self):
        app = tested_app.test_client()
        # ------ 1 GET: MESSAGE CREATION PAGE NOT LOGGED ------
        page_title = get_page_id(app, '/message', 'page_title')
        # user isn't logged, redirect to login page
        self.assertEqual(page_title, LOGIN_PAGE_TITLE)

        with app:
            # ------ 2 GET: MESSAGE CREATION PAGE LOGGED ------
            post_login(app, 'example@example.com', 'admin', 'username')
            # user is logged, remain on page
            page_title = get_page_id(app, '/message', 'page_title')
            self.assertEqual(page_title, MSG_CREATION_PAGE_TITLE)

            # ----- 3 POST: Write a message and save it
            # 2 messages to cover all cases
            response = post_message(app, 'example@example.com', 'hi', 
                 '05/06/2022', '11:12', 'Draft', 'drafted')
            self.assertEqual(response, MSG_DRAFT)

            response = post_message(app, 'example@example.com', 'hi', 
                 '05/06/2022', '11:12', 'Draft', 'drafted')
            self.assertEqual(response, MSG_DRAFT) 

            # ----- 3 POST: Write a message and schedule it
            # 2 messages to cover all cases
            response = post_message(app, 'example@example.com', 'hi', 
                 '05/06/2022', '11:12', 'Schedule', 'scheduled')
            self.assertEqual(response, MSG_SCHEDULED) 

            response = post_message(app, 'example@example.com', 'hi', 
                 '05/06/2022', '11:12', 'Schedule', 'scheduled')
            self.assertEqual(response, MSG_SCHEDULED) 
            
            # ----- 3 POST: Write an incorrect message (wrong date)
            response = post_message(app, 'examplee@example.com', 'hi', 
                 '05/806/1998', '11:12', 'Draft', 'wrong_date')
            self.assertEqual(response, WRONG_DATE_TIME)


# Tester class for edit draft message
# The possible cases are 
# 1. Get the edit message page when user isn't logged (GET)
# 2. Get the edit message page when user is logged (GET)
# 3. Select a draft message to edit (GET)
# 4. Edit a message and schedule it (POST)
# 5. Edit a message and save it as a draft (POST)
# 6. Edit a message passing wrong date (POST)

# Tester class for the draft message edit.
class TestEditMessage(unittest.TestCase):
    def test_draft(self):
        app = tested_app.test_client()
        # ------ 1 GET: DRAFT PAGE NOT LOGGED ------
        page_title = get_page_id(app, '/mailbox/draft', 'page_title')
        # user isn't logged, redirect to login page
        self.assertEqual(page_title, LOGIN_PAGE_TITLE)

        with app:
            # ------ 2 GET: DRAFT PAGE LOGGED ------
            post_login(app, 'example@example.com', 'admin', 'username')
            # user is logged, remain on page
            page_title = get_page_id(app, '/mailbox/draft', 'page_title')
            self.assertEqual(page_title, DRAFT_PAGE_TITLE)

            # ----- 3 GET: SELECT A DRAFT MESSAGE TO EDIT
            # get the first user message
            draft = Messages().to_messages(current_user.draft).messages
            id = draft[0].id
            page_title = get_page_id(app, '/mailbox/draft/' + id, 'page_title')
            self.assertEqual(page_title, MSG_CREATION_PAGE_TITLE)

             # ----- 4 POST: Edit a message and schedule it (POST)
            response = post_edit_message(app, 'example@example.com', 'hi', 
                 '05/06/2022', '11:12', 'Schedule', id, 'scheduled')
            self.assertEqual(response, MSG_SCHEDULED)

            # ----- 5 POST: Edit a message and save it as a draft (POST)
            response = post_edit_message(app, 'example@example.com', 'hi', 
                 '05/06/2022', '11:12', 'Draft', id, 'drafted')
            self.assertEqual(response, MSG_DRAFT) 

            # ----- 5 POST: Write an incorrect message (wrong date)
            response = post_edit_message(app, 'example@example.com', 'hi', 
                 '05/806/1998', '11:12', 'Draft', id, 'wrong_date')
            self.assertEqual(response, WRONG_DATE_TIME)


            """
            # ----- 3 POST: Write a message and schedule it
            # 2 messages to cover all cases
            response = post_message(app, 'example@example.com', 'hi', 
                 '05/06/2022', '11:12', 'Schedule', 'scheduled')
            self.assertEqual(response, MSG_SCHEDULED) 

                response = post_message(app, 'example@example.com', 'hi', 
                 '05/06/2022', '11:12', 'Schedule', 'scheduled')
            self.assertEqual(response, MSG_SCHEDULED) """

           

class TestGetMessages(unittest.TestCase):
    def test_get_messages(self):
        # ----- 1 GET: MESSAGES PAGE REQUEST WHEN THE CLIENT ISN'T LOGGED ------
        app = tested_app.test_client()
        title = get_page_id(app, '/mailbox', 'page_title')
        # Client isn't logged, it is redirect to the login page
        self.assertEqual(title, LOGIN_PAGE_TITLE)

                # ------ 2 GET: MESSAGES PAGE REQUEST WHEN THE CLIENT IS LOGGED ------
        with app:
            # login the user              
            post_login(app, 'example@example.com', 'admin', 'username')
            title = get_page_id(app, '/mailbox', 'page_title')
            # Client is logged, it is on the messages page
            self.assertEqual(title, MAILBOX)

            #display = ['receiver', 'body', 'date', 'time' 'send', 'save'] 

class TestForbbidenWords(unittest.TestCase):
    def test_forbbidden_words(self):
        app = tested_app.test_client()
        title = get_page_id(app, '/', 'page_title')
        self.assertEqual(title, LOGIN_PAGE_TITLE)

        with app:
            post_register(app, 'wrongwords@test.com', 'wrong','words','wrongwords','10/10/2021','parolaccia','email')
            post_login(app, 'example@example.com', 'admin', 'username')
            response = post_message(app, 'wrongwords@test.com', 'parolaccia ciao', 
                 '05/06/1998', '11:12', 'Schedule', 'wrong_words')
            self.assertEqual(response, WRONG_WORDS)


# Tester class for the info user page operation.
# The possible cases are 2:
#   1. The user requests for the account delete when he isn't logged. (GET)
#   2. The user requests for the account delte when he is logged. (GET)
class TestDeleteUsuer(unittest.TestCase):
    def test_get_delete(self):
        # ----- 1 GET: DELETE REQUEST WHEN THE CLIENT ISN'T LOGGED ------
        app = tested_app.test_client()
        title = get_page_id(app, '/delete', 'page_title')
        # Client isn't logged, it is redirect to the login page
        self.assertEqual(title, LOGIN_PAGE_TITLE)

        # ------ 2 GET: DELETE REQUEST WHEN THE CLIENT IS LOGGED ------
        with app:
            # login the user              
            post_login(app, 'example@example.com', 'admin', 'username')
            # clean the scheduled messages queue because if celery is not started, the user won't be
            # deleted until his scheduled messages will be delivered
            current_user.to_be_sent = '[]'
            db.session.commit()
            title = get_page_id(app, '/delete', 'page_title')
            # Client is logged, it is on the profile page
            self.assertEqual(title, UNSUBSCRIBED_PAGE_TITLE)

