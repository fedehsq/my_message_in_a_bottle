from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import defaultload
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date
import json

db = SQLAlchemy()

#json.dumps([{'miao':'miaomiao'}]) #from dict to json (str)
#json.loads(json.dumps([{'miao':'miaomiao'}])) #from json (str) to dict
    
class User(db.Model):

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    photo_path = db.Column(db.Unicode(128), default = 'profile_pics/profile_pic.svg')
    email = db.Column(db.Unicode(128), nullable=False)
    firstname = db.Column(db.Unicode(128))
    lastname = db.Column(db.Unicode(128))
    password = db.Column(db.Unicode(128))
    to_read = db.Column(db.Integer, default = 0)
    read = db.Column(db.Unicode(128), default="")
    received = db.Column(db.Unicode(128), default = '[]')
    sent = db.Column(db.Unicode(128), default = '[]')
    to_be_sent = db.Column(db.Unicode(128), default = '[]')
    draft = db.Column(db.Unicode(8196), default = '[]')
    forbidden_words = db.Column(db.Unicode(128), default = "")
    blacklist = db.Column(db.Unicode(128), default = "")
    date_of_birth = db.Column(db.DateTime)
    reports = db.Column(db.Integer, default = 0)
    lottery_number = db.Column(db.Integer, default = 0)
    points = db.Column(db.Integer, default = 0)
    is_blocked = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    deleted = db.Column(db.Boolean, default = False)
    is_anonymous = False

    def __init__(self, *args, **kw):
        super(User, self).__init__(*args, **kw)
        self._authenticated = False

    def set_password(self, password):
        self.password = generate_password_hash(password)

    @property
    def is_authenticated(self):
        return self._authenticated

    def authenticate(self, password):
        checked = check_password_hash(self.password, password)
        self._authenticated = checked
        return self._authenticated

    def get_id(self):
        return self.id

class Message():
    def __init__(self, sender: str, dest: str, body: str, time: str, 
        id = None, image = None, read = False, 
        bold = False, italic = False, underline = False):

        self.sender = sender
        self.dest = dest
        self.body = body
        self.time = time
        self.id = str(hash(sender + dest + body + time)) if not id else id
        # base64 photo
        self.image = image if image else ''
        self.read = read
        self.bold = bold
        self.italic = italic
        self.underline = underline
        
        
    def to_string(self):
        return json.dumps(
            {'id': self.id, 'sender': self.sender, 'dest' : self.dest, 
             'body' : self.body, 'time' : self.time, 'image' : self.image, 
             'read': self.read, 'bold': self.bold, 
             'italic': self.italic, 'underline': self.underline})

class Messages():

    def __init__(self, messages = None):
        self.messages = [] if messages == None else messages

    def enqueue(self, m: Message):
        self.messages.append(m)

    def to_string(self):
        messages = []
        for m in self.messages:
            messages.append(m.to_string())
        return json.dumps(messages)
        #return json.dumps([message.to_string() for message in self.messages])

    def to_message(self, msg: str): 
        obj =  json.loads(msg)
        return Message(
            obj['sender'], obj['dest'], obj['body'], 
            obj['time'], obj['id'], obj['image'], 
            obj['read'], obj['bold'], obj['italic'], obj['underline']
        )

    def to_messages(self, msg_list):
        messages = json.loads(msg_list)
        m = Messages()
        for message in messages:
            m.enqueue(self.to_message(message))
        return m