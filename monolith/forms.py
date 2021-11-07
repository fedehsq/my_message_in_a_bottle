import wtforms as f
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea
from datetime import datetime

class LoginForm(FlaskForm):
    email = f.StringField('Email', validators=[DataRequired()])
    password = f.PasswordField('Password', validators=[DataRequired()])
    display = ['email', 'password']

class UserForm(FlaskForm):
    photo = f.FileField('Photo')
    email = f.StringField('Email', validators=[DataRequired()])
    firstname = f.StringField('Firstname', validators=[DataRequired()])
    lastname = f.StringField('Lastname', validators=[DataRequired()])
    password = f.PasswordField('Password', validators=[DataRequired()])
    points = f.IntegerField('Points')
    date_of_birth = f.DateField('Date of birth', format='%d/%m/%Y')
    forbidden_words = f.StringField('Forbbidden Words', widget = TextArea())
    blacklist = f.StringField('Blacklist', widget = TextArea())
    display = ['photo', 'email', 'firstname', 'lastname', 'password', 'points', 'date_of_birth', 'blacklist', 'forbidden_words']

class MessageForm(FlaskForm):
    receiver = f.StringField('To', validators=[DataRequired()])
    body = f.StringField('Message', validators=[DataRequired()], widget=TextArea())
    photo = f.FileField('Photo', default=None)
    date  = f.DateField('Date',format='%d/%m/%Y', validators=[DataRequired()])
    time  = f.TimeField('Time',format='%H:%M', validators=[DataRequired()])
    choice = f.RadioField('Label', choices = [('Draft', 'Draft'),('Schedule', 'Schedule')], default='Schedule')
    display = ['receiver', 'body', 'photo', 'date', 'time' 'choice']

class ReadMessageForm(FlaskForm):
    sender = f.StringField('From')
    body = f.StringField('Message', widget = TextArea())
    date  = f.StringField('Date')
    display = ['from', 'body', 'date']

class ViewMessageForm(FlaskForm):
    receiver = f.Label('To', 'To')
    body = f.Label('Message', 'Message')
    date  = f.Label('Date', 'Message')
    display = ['receiver', 'body', 'date']

class ReportForm(FlaskForm):
    email = f.StringField('Email', validators=[DataRequired()])
    reason = f.StringField('Reason', widget = TextArea())
    display = ['email','reason']

class LotteryForm(FlaskForm):
    number = f.IntegerField('number', validators=[DataRequired()])
    display = ['number']