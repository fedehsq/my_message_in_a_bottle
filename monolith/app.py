import datetime
from celery import Celery
from flask import Flask
from celery.schedules import crontab
from monolith.auth import login_manager
from monolith.database import Message, Messages, User, db
from monolith.views import blueprints
from flask_login import current_user
from monolith.background import do_task
import os
import sys

UPLOAD_FOLDER = os.path.abspath("monolith/static/profile_pics/")

#UPLOAD_FOLDER = '/Users/federicobernacca/Documents/HW2/monolith/static/profile_pics'
#UPLOAD_FOLDER = '/Users/federicobernacca/Documents/HW2/monolith/static/profile_pics'
#ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

APP = None

def create_app():
    app = Flask(__name__)
    app.config['WTF_CSRF_SECRET_KEY'] = 'A SECRET KEY'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'ANOTHER ONE'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../mmiab.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


    for bp in blueprints:
        app.register_blueprint(bp)
        bp.app = app

    db.init_app(app)
    login_manager.init_app(app)
    db.create_all(app=app)
    # create a first admin user
    with app.app_context():
        do_task.delay()
        # delete all users in database if pytest is running
        if "PYTEST_CURRENT_TEST" in os.environ:
            print('qua')
            db.session.query(User).delete()
        q = db.session.query(User).filter(User.email == 'example@example.com')
        user = q.first()
        #print(user.email)
        if user is None:
            example = User()
            example.firstname = 'Admin'
            example.lastname = 'Admin'
            example.email = 'example@example.com'
            example.dateofbirth = datetime.datetime(2020, 10, 5)
            example.is_admin = True
            example.set_password('admin')
            example.received = '[]'
            example.sent = '[]'
            example.to_be_sent = '[]'
            example.draft = '[]'
            db.session.add(example)
            db.session.commit()
    return app

app = APP = create_app()
if __name__ == '__main__':
    app.run()