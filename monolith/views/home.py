from flask import Blueprint, render_template
from werkzeug.utils import redirect
from monolith.auth import current_user
from monolith.views.auth import login

home = Blueprint('home', __name__)

@home.route('/')
def index():
    if current_user is not None and hasattr(current_user, 'id'):
        # calculate the number of notifications 
        # number of message received to read + number of message sent that have been read       

        # get the list of messages' id that have been read
        if current_user.read == '':
            read = 0
        else:
            read = len(current_user.read.split(" "))
        number = current_user.to_read + read
        return render_template("index.html", number = number)
    else:
        return redirect("/login")
