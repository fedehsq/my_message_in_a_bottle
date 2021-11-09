from flask import Blueprint, redirect, render_template, request
from monolith.database import User, db
from monolith.forms import UserForm, ReportForm, LotteryForm
from flask_login import current_user
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
_APP = None
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'svg'}

from monolith.views.message import edit_message

users = Blueprint('users', __name__)

# ----- HELPER FUNCTIONS ------
# If the user does not select a file, the browser submits an
# empty file without a filename.
def save_photo(file, user):
    if file and not file.filename == '':
        file.filename = user.email + file.filename
        filename = secure_filename(file.filename)
        from monolith.app import APP
        file.save(os.path.join(APP.config['UPLOAD_FOLDER'], filename))
        user.photo_path = 'profile_pics/' + filename

# programatically fill the UserForm with a User
def fill_form_with_user(user):
    form = UserForm()
    form.email.data = user.email
    form.firstname.data = user.firstname
    form.lastname.data = user.lastname
    form.date_of_birth.data = user.date_of_birth
    form.points.data = user.points
    form.forbidden_words.data = user.forbidden_words
    form.blacklist.data = user.blacklist
    # password is omitted for security reason
    return form

# programatically fill a user from a UserForm
def fill_user_with_form(form):
    new_user = User()
    new_user.email = form.email.data
    new_user.firstname = form.firstname.data
    new_user.lastname = form.lastname.data
    new_user.password = form.password.data
    new_user.forbidden_words = form.forbidden_words.data
    new_user.blacklist = form.blacklist.data
    new_user.date_of_birth = form.date_of_birth.data
    return new_user

# Post request to edit
def edit_profile():
    form = UserForm()
    # the email is not editable 
    # so manual fill this field to avoid error on submit
    form.email.data = current_user.email
    points = current_user.points
    if form.validate_on_submit():
        # update user info
        form.populate_obj(current_user)
        current_user.points = points
        current_user.set_password(form.password.data)
        current_user.date_of_birth = form.date_of_birth.data
        # update profile pic of user
        save_photo(form.photo.data, current_user)
        db.session.commit()
        # display a message advising correct info update
        return render_template("profile.html", 
            mphoto = current_user.photo_path,
            form = fill_form_with_user(current_user), 
            just_edited = "Personal info updated. Return to ")
    # wrong date format
    else:
        return render_template("profile.html", 
            form = fill_form_with_user(current_user), 
            date_error_message = "Date format DD/MM/YYYY.")

# Open a page with user infos
def show_profile():
    form = fill_form_with_user(current_user)
    suggest = "README: separate each forbidden word and each blacklisted user with a ','"
    return render_template("profile.html", mphoto = current_user.photo_path, form = form, suggest = suggest)

# Register a user if all fields are properly filled
def user_registration(form):
    global _APP
    new_user = fill_user_with_form(form)
    possible_user = db.session.query(User).filter(User.email == new_user.email).first()
    if form.validate_on_submit():
        # check if the user with this email is already registered
        if possible_user is not None:
            return render_template('register.html', form = form, 
                mphoto = 'profile_pics/profile_pic.svg',
                email_error_message = "Email already registered.")
        """
        Password should be hashed with some salt. For example if you choose a hash function x, 
        where x is in [md5, sha1, bcrypt], the hashed_password should be = x(password + s) where
        s is a secret key.
        """
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        save_photo(form.photo.data, new_user)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        # after a successful registration, a message appears in the same page
        # inviting the just registered user to login
        # return redirect('/users')
        return render_template('register.html', mphoto = new_user.photo_path, form = form, 
            just_registered = "You are registered! Please")
    # case in which the date format is incorrect
    else:
        # wrong dath of birth inserted and
        # check if the user with this email is already registered
        if possible_user is not None:
            return render_template('register.html', form = form, 
                mphoto = 'profile_pics/profile_pic.svg',
                email_error_message = "Email already registered.", 
                date_error_message = "Date format DD/MM/YYYY.")
        else:
            return render_template('register.html', form = form, 
                mphoto = 'profile_pics/profile_pic.svg',
                date_error_message = "Date format DD/MM/YYYY.")

# Return filtered users
# List all searched users by name, surname or email
def search_users(searched_input):
    tmp=[]
    users = db.session.query(User)
    for u in users:
        if not searched_input.lower() in u.firstname.lower() and not searched_input.lower() in u.lastname.lower() and not searched_input.lower() in u.email.lower():
            tmp.append(u.firstname)
    for i in tmp:
        users.filter_by(firstname=i).delete()
    return users
    
# ----- ROUTES ------
@users.route('/users')
def get_users():
    if current_user.is_authenticated:
        users = db.session.query(User)
        searched_input=request.args.get("search")
    else:
        return redirect("/login")
    if searched_input:
        users=search_users(searched_input)
        return render_template("users.html", users = users, current_user = current_user, searched_input="You searched: "+searched_input)
    else:
        return render_template("users.html", users = users, current_user = current_user)

# Get the profile information of the authenticated user
@users.route('/profile', methods=['POST', 'GET'])
def get_profile():
    # check if user is authenticated...
    if current_user.is_authenticated:
         # request to open profile page
        if request.method == 'GET':
            return show_profile()
        else:
            # request to edit profile
            return edit_profile()
    # ...otherwise he is redirect to the login page
    else:
        return redirect("/login")
   
# Register a new user
@users.route('/register', methods=['POST', 'GET'])
def register():
    # check if the user is already logged, 
    # if so the user will be redirected to his dashboard
    if current_user.is_authenticated:
        return redirect("/")
    form = UserForm()
    # registration post request
    if request.method == 'POST':
        return user_registration(form)       
    else:
        # get the page
        suggest = "README: separate each forbidden word with a ',' "
        return render_template('register.html', mphoto = 'profile_pics/profile_pic.svg', form = form, suggest = suggest)   

# Route for report a user
@users.route("/users/report/<email>", methods = ['GET','POST'])
def report(email):
    # if the user isn't athenticated he can't send report,
    # so he will be redirect to the login page
    if not current_user.is_authenticated:
        return redirect("/login")
    form = ReportForm()
    if request.method == 'GET':
        form.email.data = email
        return render_template('report.html', form = form)
    else:
        if form.validate_on_submit():
            email = form.data["email"]
            possible_user = db.session.query(User).filter(User.email == email).first()
            # check if exists the user, if not redirect to report page again
            if possible_user is None:
                return render_template('report.html', form = form, email_error_message = 'No user with this email.')
            else:
                possible_user.reports += 1
                # check if reports are 3, so the user become blocked and can't login anymore
                if possible_user.reports == 3:
                    possible_user.is_blocked = True
                db.session.commit()
                return redirect("/")

#route to play lottery
@users.route('/playLottery', methods=['GET','POST'])
def play_lottery():
    #check if user is authenticated 
    if not current_user.is_authenticated:
        return redirect("/")
    form = LotteryForm()
    if request.method == 'POST':
        number = form.data['number']
        if number > 100 or number < 1:
            return render_template('lottery.html', form = form, error_number = "Number not allowed! Please choose another number between 1 and 100", number = current_user.lottery_number)
        current_user.lottery_number = number
        db.session.commit()
        return redirect("/")
    else:
        return render_template('lottery.html', form = form, number = current_user.lottery_number)
  
