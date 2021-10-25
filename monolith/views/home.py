from flask import Blueprint, render_template, request
from werkzeug.utils import redirect


from monolith.auth import current_user
from monolith.forms import LoginForm
from monolith.views.auth import login

home = Blueprint('home', __name__)


@home.route('/')
def index():
    if current_user is not None and hasattr(current_user, 'id'):
        welcome = "Logged In!"
    else:
        return redirect("/login")
    return render_template("index.html", welcome=welcome)
