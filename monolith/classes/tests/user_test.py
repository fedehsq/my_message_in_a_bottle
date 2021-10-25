import unittest

from monolith.app import app as tested_app
from bs4 import BeautifulSoup

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

# ----- Auxiliary functions used in the tests ------ 

# Get the login page, an unique id is assigned in one field
# on the html page to recognize the field with which to test.
def get_login(app, html_id):
    # Request the login page
    response = app.get('/login', follow_redirects = True)
    # extract the html page from the response
    html = str(response.data, 'utf8')
    # parse this page
    soup = BeautifulSoup(html, 'html.parser')
    # access and return the interesting field to check
    message = soup.find(id = html_id).text
    return message

# Get the logout page, an unique id is assigned in one field
# on the html page to recognize the field with which test.
def get_logout(app, html_id):
    # Request the logout page
    response = app.get('/logout', follow_redirects = True)
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
    # Pass the parameters that will feed the login form: 
    # In case of successfully login, there will be a redirection to the homepage
    # otherwise an error message appears on this page.
    # These two possibilities are tested to understand the response.
    response = app.post('/login', 
        data = {'email': email, 'password': password}, 
        follow_redirects = True)
    # extract the html page from the response
    html = str(response.data, 'utf8')
    # parse this page
    soup = BeautifulSoup(html, 'html.parser')
    # access and return the interesting field to check
    message = soup.find(id = html_id).text
    return message


# Get the registration page, an unique id is assigned in one field
# on the html page to recognize the field with which test.
def get_register(app, html_id): 
    # Request the registration page
    response = app.get('/create_user', follow_redirects = True)
    # extract the html page from the response
    html = str(response.data, 'utf8')
    # parse this page
    soup = BeautifulSoup(html, 'html.parser')
    # access to the interesting field ro check
    message = soup.find(id = html_id).text
    return message

# Try to register an user, an unique id is assigned in one field
# on the html page to recognize the field with which test.
def post_register(app, email, firstname, lastname, password, date_of_birth, html_id): 
    # Pass the parameters that will feed the registration form.
    # In case of successfully or incorrect registration, some messages appears in this page.
    # These messages are checked to test the proper case (success or kind of error). 
    response = app.post('/create_user', 
        data = {'email': email, 'firstname': firstname, 'lastname': lastname, 
                'password': password, 'dateofbirth': date_of_birth}, 
        follow_redirects = True)
    # extract the html page from the response
    html = str(response.data, 'utf8')
    # parse this page
    soup = BeautifulSoup(html, 'html.parser')
    # access to the interesting field ro check
    message = soup.find(id = html_id).text
    return message

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
        title = get_login(app, 'page_title')
        self.assertEqual(title, LOGIN_PAGE_TITLE)

        # ------ POST: CORRECT LOGIN -----
        username = post_login(app, 'example@example.com', 'admin', 'username')
        self.assertEqual(username, USERNAME)

        # ------ GET: LOGOUT -----
        title = get_logout(app, 'page_title')
        self.assertEqual(title, LOGIN_PAGE_TITLE)

        # ----- POST: INCORRECT LOGIN, WRONG CREDENTIALS ------
        wrong_credentials = post_login(app, 'a', 'b', 'wrong_credentials')
        self.assertEqual(wrong_credentials, WRONG_CREDENTIALS)

        # ----- GET: LOGIN PAGE REQUEST WHEN THE CLIENT IS ALREADY LOGGED ------
        with app:                
            post_login(app, 'example@example.com', 'admin', 'username')
            username = get_login(app, 'username')
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
        response = get_register(app, 'page_title')
        self.assertEqual(response, REGISTRATION_PAGE_TITLE) 
        
        # ------ CORRECT REGISTRATION -----
        response = post_register(app, 'pao@pao.com', 'paola', 
            'petri', 'pao', '05/06/1998', 'registration_done')
        self.assertEqual(response, REGISTRATION_DONE)

        # ----- INCORRECT REGISTRATION: EMAIL ALREADY REGISTERED ------
        response = post_register(app, 'pao@pao.com', 'paola', 
            'petri', 'pao', '05/06/1998', 'wrong_email')
        self.assertEqual(response,  WRONG_EMAIL)

        # ----- INCORRECT REGISTRATION: DATE OF BIRTH IN INCORRECT FORMAT ------
        response = post_register(app, 'a@b', 'a', 
            'b', 'ab', '05/06/98', 'wrong_date')
        self.assertEqual(response, WRONG_DATE)

        # ----- INCORRECT REGISTRATION: EMAIL ALREADY REGISTERED AND DATE OF BIRTH IN INCORRECT FORMAT ------
        response = post_register(app, 'pao@pao.com', 'paola', 
            'petri', 'pao', '5/06/98', 'wrong_email')
        response1 = post_register(app, 'pao@pao.com', 'paola', 
            'petri', 'pao', '5/06/98', 'wrong_date')
        self.assertEqual(response,  WRONG_EMAIL)
        self.assertEqual(response1,  WRONG_DATE)

        # ----- GET: REGISTRATION PAGE REQUEST WHEN THE CLIENT IS ALREADY LOGGED ------
        with app:                
            post_login(app, 'example@example.com', 'admin', 'username')
            # Client is already logged and requests for the registration page
            username = get_register(app, 'username')
            self.assertEqual(username, USERNAME) 
           
class TestUserOperations(unittest.TestCase):
    def test_get_users(self):
        app = tested_app.test_client()
        response = app.get('/users')
        # Client isn't logged, it is redirect to the login page
        self.assertEqual(response.status_code, 302)
        title = get_login(app, 'page_title')
        self.assertEqual(title, LOGIN_PAGE_TITLE)

         # ------ POST: CORRECT LOGIN -----
        with app:                
            post_login(app, 'example@example.com', 'admin', 'username')
            response = app.get('/users')
            # Client is now logged, it can sees registered users
            self.assertEqual(response.status_code, 200)