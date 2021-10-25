from flask import Blueprint, redirect, render_template
from flask.globals import request
from flask_login import login_user, logout_user, current_user

from monolith.database import User, db
from monolith.forms import LoginForm

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # check if the user is already logged, 
    # if so the user will be redirected to his dashboard
    if current_user.is_authenticated:
        return redirect("/")
    form = LoginForm()
    if form.validate_on_submit():
        email, password = form.data['email'], form.data['password']
        q = db.session.query(User).filter(User.email == email)
        user = q.first()
        if user is not None and user.authenticate(password):
            login_user(user)
            return redirect('/')
        else:
            # tells to the user that he inserted wrong credentials
            return render_template('login.html', form = form, 
            wrong_credentials = "Incorrect username or password.")
    return render_template('login.html', form = form)


@auth.route("/logout")
def logout():
    logout_user()
    return redirect('/')
