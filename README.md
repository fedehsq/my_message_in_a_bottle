# Implementation

0. Added pytest in requirements.txt
1. Changing home page: now the applications starts with login form with the possibility to register a new user.
2. Updating users page adding also the email, because more users could be the same name and surname, so the email act as an unique indentifier.
3. Remove the possibility to have more registered users with the same email, in case of already registered, display an error message in the same page
4. Force a user to fill properly date field in registration.
5. When a registration is completed, user is suggested to go to the login page.
6. Idea of test: extract a unique text string on the html page for testing the correct result.
7. A client that is not logged can't read the registered users list.
8. A client that is logged can't navigate to the registration page and to the login page. It is redirect to its homepage.

## TODO ##
1. If i am already logged, and i try to access to the login page, error, also valid for the reg page

## Instructions
1. Open the project in your IDE.
2. From IDE terminal, or normal Ubuntu/MacOS terminal execute the command `virtualenv venv` inside project root.
3. Now, you have to activate it, by executing the command `source venv/bin/activate`.
4. You have to install all requirements, let's do that with `pip install -r requirements.txt`.

**Perfect!** now you can run flask application!

<span style="color:orange">WARNING:</span> each time that you open a new terminal session you have
to execute the step 3.


### Run the application

If you want to run the application, you can use the script `run.sh` by typing `bash run.sh`,
or you can set these environment variables:

```
FLASK_DEBUG=1
FLASK_ENV=development
```
