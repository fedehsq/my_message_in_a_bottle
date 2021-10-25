from flask import Blueprint, redirect, render_template, request, make_response
from sqlalchemy.sql.operators import isnot

from monolith.database import User, db
from monolith.forms import UserForm, LoginForm
from flask_login import current_user

users = Blueprint('users', __name__)

@users.route('/users')
def get_users():
    if current_user.is_authenticated:
        users = db.session.query(User)
        return render_template("users.html", users = users)
    else:
        return redirect("/login")

@users.route('/create_user', methods=['POST', 'GET'])
def create_user():
    # check if the user is already logged, 
    # if so the user will be redirected to his dashboard
    if current_user.is_authenticated:
        return redirect("/")
    form = UserForm()
    if request.method == 'POST':
        new_user = User()
        form.populate_obj(new_user)
        possible_user = db.session.query(User).filter(User.email == new_user.email).first()
        if form.validate_on_submit():
            # check if the user with this email is already registered
            if possible_user is not None:
                return render_template('create_user.html', form = form, 
                    email_error_message = "Email already registered.")
            """
            Password should be hashed with some salt. For example if you choose a hash function x, 
            where x is in [md5, sha1, bcrypt], the hashed_password should be = x(password + s) where
            s is a secret key.
            """
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()
            # after a successful registration, a message appears in the same page
            # inviting the just registered user to login
            # return redirect('/users')
            return render_template('create_user.html', form = form, 
                just_registered = "You are registered! Please")
        # case in which the date format is incorrect
        else:
            # wrong dath of birth inserted and
            # check if the user with this email is already registered
            if possible_user is not None:
                return render_template('create_user.html', form = form, 
                    email_error_message = "Email already registered.", 
                    date_error_message = "Date format DD/MM/YYYY.")
            else:
                return render_template('create_user.html', form = form, 
                    date_error_message = "Date format DD/MM/YYYY.")
    else:
        return render_template('create_user.html', form = form)