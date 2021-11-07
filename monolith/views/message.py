from flask import Blueprint, redirect, render_template
from flask.globals import request
from flask_login import current_user
import re
from monolith.database import User, db, Message, Messages
from monolith.forms import MessageForm
from datetime import datetime
from base64 import b64encode
message = Blueprint('message', __name__) 

# Messages on rendering (message and code)
CHANGE_BODY = 'Change body!'
USER_INEXISTENT = ' not registered'
BLACKLIST = " doesn't want messages from you"
FORBIDDEN_WORDS = 'Forbidden words for '
SCHEDULED = 'Scheduled!'
DATE_ERROR = 'Date format DD/MM/YYYY hh:mm'
DRAFT = 'Draft!'

# ------ ROUTES -------
@message.route('/mailbox', methods=['GET', 'POST'])
# Show the mailbox
def mailbox():
    # if the user isn't athenticated he can't see messages,
    # so he will be redirect to the login page
    if not current_user.is_authenticated:
        return redirect("/login")
    msg_field = request.args.get('msg')
    msg_user = request.args.get('user')
    msg_date = request.args.get('date')

    # get the number of new messages to display the notifications
    inbox = current_user.to_read
    # get the number of sent messages that have been read to display the notifications
    if current_user.read == '':
        read = 0
    else:
        read = len(current_user.read.split(" "))
    # no search request
    if not msg_field and not msg_user and not msg_date:
        return render_template("mailbox.html", inbox = inbox, read = read)
    # search request
    res_received, res_sent, res_to_be_sent = search_messages(msg_field, msg_user, msg_date)
    return render_template("mailbox/searched_list.html", 
        page_title = 'Search', 
        inbox = res_received,
        sent = res_sent,
        scheduled = res_to_be_sent,
        read = read
    )
    # return render_template("mailbox.html", res_received=res_received, res_sent=res_sent, # res_to_be_sent=res_to_be_sent, boolean=boolean, inbox = inbox, read = read)



@message.route('/mailbox/draft/', defaults={'id': ''}, methods = ['GET', 'POST'])
@message.route('/mailbox/draft/<id>', methods=['GET', 'POST'])
# Show the draft messages
def draft(id):
    if not current_user.is_authenticated:
        return redirect("/login")  
    draft = current_user.draft
    messages = Messages().to_messages(draft)
    # check if user wants to delete message
    if (request.form.__contains__('delete')):
        message_id = request.form['delete']
        # find the message with same id and swap it
        newlist = Messages([message for message in messages.messages if message_id != message.id])
        current_user.draft = newlist.to_string()
        db.session.commit()
    messages = Messages().to_messages(current_user.draft)
    # check if the request is to see all messages...
    if (id == ''):
        return render_template("mailbox/messages_list_.html", page_title = 'Draft', messages = messages.messages)
    # ... or if a fixed message is selected by id
    m = get_message_by_id(messages.messages, id)
    # launch template to edit if m is already in draft
    return edit_message(m.dest, m) if m else redirect('/mailbox')


@message.route('/mailbox/sent/', defaults={'id': ''}, methods = ['GET', 'POST'])
@message.route('/mailbox/sent/<id>', methods=['GET', 'POST']) 
# Show the sent messages or a message corresponding to a specific id
def sent(id):
    if not current_user.is_authenticated:
        return redirect("/login")
    sent = current_user.sent
    messages = Messages().to_messages(sent)
    # check if user wants to delete message
    if (request.form.__contains__('delete')):
        message_id = request.form['delete']
        # find the message with same id and swap it
        newlist = Messages([message for message in messages.messages if message_id != message.id])
        current_user.sent = newlist.to_string()
        db.session.commit()
    messages = Messages().to_messages(current_user.sent)
    # check if the request is to see all messages...
    if (id == ''):
        # set the flag read at True for all the message that the receiver has read
        # in order to put at zero the number in the notification
        read_msg = current_user.read.split(" ")
        set_all_read(read_msg)
        return render_template("mailbox/messages_list_.html", page_title = 'Sent', messages = messages.messages, read_msg = read_msg) 
    # ... or if a fixed message is selected by id
    m = get_message_by_id(messages.messages, id)
    if not m:
        return redirect('/mailbox')
    # launch template to read the sent message
    form = fill_message_form_from_message(m)
    return render_template("message.html", 
        mphoto = 'data:image/jpeg;base64,' + m.image if m.image != '' else None,
        message = m,
        disabled = True, 
        form = form)
    

@message.route('/mailbox/scheduled/', defaults={'id': ''}, methods = ['GET', 'POST'])
@message.route('/mailbox/scheduled/<id>', methods=['GET', 'POST'])
# Show the scheduled messages or a message corresponding to a specific id
def scheduled(id):
    if not current_user.is_authenticated:
        return redirect("/login") 
    to_be_sent = Messages().to_messages(current_user.to_be_sent).messages
    print(to_be_sent)
    
    # check if user wants to delete message and check if the user has points to do this
    if (request.form.__contains__('delete') and current_user.points >= 150):
        message_id = request.form['delete']
        # find the message with same id and swap it
        newlist = Messages([message for message in to_be_sent if message_id != message.id])
        current_user.to_be_sent = newlist.to_string()
        current_user.points -= 150
        db.session.commit()
    to_be_sent = Messages().to_messages(current_user.to_be_sent).messages

    # check if the request is to see all messages...
    if (id == ''):
        return render_template("mailbox/messages_list_.html", page_title = 'Scheduled', messages = to_be_sent, points = current_user.points) 
    # ... or if a fixed message is selected by id
    m = get_message_by_id(to_be_sent, id)
    print(to_be_sent)
    if not m:
        return redirect('/mailbox')
    # launch template to read the sent message
    form = fill_message_form_from_message(m)
    return render_template("message.html", 
        message = m,
        disabled = True,
        mphoto = 'data:image/jpeg;base64,' + m.image if m.image != '' else None,
        form = form)


@message.route('/mailbox/inbox/', defaults={'id': ''}, methods = ['GET', 'POST'])
@message.route('/mailbox/inbox/<id>', methods=['GET', 'POST'])
# Show the inbox messages or the message corresponding to a specific id
def inbox(id):
    if not current_user.is_authenticated:
        return redirect("/login")  
    inbox = current_user.received
    messages = Messages().to_messages(inbox)
    # check if user wants to delete message
    if (request.form.__contains__('delete')):
        message_id = request.form['delete']
        # find the message with same id and swap it
        newlist = Messages([message for message in messages.messages if message_id != message.id])
        current_user.received = newlist.to_string()
        db.session.commit()
    messages = Messages().to_messages(current_user.received)
    # check if the request is to see all messages...
    if (id == ''):
        return render_template("mailbox/messages_list_.html", 
            page_title = 'Inbox', 
            messages = messages.messages) 
    # ... or if a fixed message is selected by id
    m = get_message_by_id(messages.messages, id)
    if not m:
        return redirect('/mailbox')
    # set the flag read to True, because the user is reading the message
    set_read(id)
    # launch template to read the sent message
    form = fill_message_form_from_message(m)
    form.receiver.label = 'From'
    return render_template("message.html", 
        mphoto = 'data:image/jpeg;base64,' + m.image if m.image != '' else None,
        message = m,
        disabled = True, 
        form = form)


@message.route('/mailbox/forward/<id>', methods=['POST', 'GET'])
def forward(id):
    # forward for inbox or received
    received = current_user.received
    messages = Messages().to_messages(received)
    m = get_message_by_id(messages.messages, id)
    # not found in inbox
    if not m:
        sent = current_user.sent
        messages = Messages().to_messages(sent)
        m = get_message_by_id(messages.messages, id)
    if not m:
        return redirect('/mailbox')
    return edit_message('', m)


@message.route('/mailbox/reply/<id>', methods=['POST', 'GET'])
def reply(id):
    # Replay for inbox
    received = current_user.received
    messages = Messages().to_messages(received)
    m = get_message_by_id(messages.messages, id)
    if not m:
        return redirect('/mailbox')
    return edit_message(m.sender, None)


@message.route('/message/', defaults={'receiver': ''}, methods = ['GET', 'POST'])
@message.route('/message/<receiver>', methods = ['GET', 'POST'])
# Edit or create a new message, msg is None when the message is created,
# msg is not None when the message is draft
def edit_message(receiver, msg = None):
    # check if user is authenticated
    if (not current_user.is_authenticated):
        return redirect('/login')
    form = MessageForm()
    # check if the requested message already exists
    if (msg != None and form.body.data == None):
        form = fill_message_form_from_message(msg)
    if request.method == 'GET':
        suggest = "README: separate each recipient with a ','"
        #form.photo.data = Image.open('monolith/static/default.png')
        form.receiver.data = receiver
        return render_template("message.html",
            message = msg if msg else None,
            # pass the photo if it exists
            mphoto = 'data:image/jpeg;base64,' 
                + msg.image if msg and msg.image != '' else None, 
            form = form, suggest = suggest)
    else:
        # build the message
        message = build_message(form, msg)
        photo = 'data:image/jpeg;base64,' + message.image if message.image != '' else None
        if form.validate_on_submit():
            # checking if it is new or edited
            # message = build_message(form, msg)
            # photo = 'data:image/jpeg;base64,' + message.image if message.image != '' else None
            # user wants to schedule the message
            if form.choice.data == 'Schedule':
                # render a template with correct values
                # (message ok for every dest, massage ok for some dests, 
                # message not ok for anyone)
                code, data = validate_message(message)
                # user doesn't exists
                if (code == USER_INEXISTENT):
                    return render_template("message.html", 
                        mphoto = photo if msg else None,
                        message = message,
                        wrong_dest = data + USER_INEXISTENT, 
                        form = form)
                # current user is in the blacklist of the dest
                if (code == BLACKLIST):
                    return render_template("message.html", 
                        mphoto = photo if msg else None,
                        message = message,
                        blacklist_dest = data + BLACKLIST, 
                        form = form)
                # forbidden words for every dest
                if code == CHANGE_BODY:
                    return render_template("message.html", 
                        mphoto = photo if msg else None,
                        message = message,
                        error = CHANGE_BODY, 
                        form = form)
                # forbidden words for some dest
                if code == FORBIDDEN_WORDS:
                    return render_template("message.html", 
                        mphoto = photo if msg else None,
                        message = message,
                        forbidden = FORBIDDEN_WORDS +
                            data + '! The message has been scheduled removing them.', 
                        form = form)
                # message can be scheduled, remove msg from draft
                draft_remove(msg)
                if code == SCHEDULED:
                    return render_template("message.html", 
                        mphoto = photo,
                        message = message,
                        disabled = True, 
                        scheduled = SCHEDULED, 
                        form = form)
            # user wants to draft/edit a message 
            else:
                # Check if message already exists, it is to draft
                update_draft_message(msg, message) if msg!= None else draft_new_message(message)  
                return render_template("message.html", 
                    mphoto = photo,
                    message = message,
                    disabled = True,
                    form = form, 
                    draft = DRAFT)
        # invalid date
        else:
            # photo = 'data:image/jpeg;base64,' + msg.image if msg and msg.image != '' else None,
            return render_template('message.html',
                mphoto = photo if msg else None,
                message = message,
                form = form, 
                date_error_message = DATE_ERROR)


# ----- HELPER FUNCTIONS ------
# When a user open a message from inbox, the flag "read" is changed to True
def set_read(id):
    received = current_user.received
    messages = Messages().to_messages(received)
    for msg in messages.messages:
        if msg.id == id:
            msg.read = True
    current_user.received = messages.to_string()
    if current_user.to_read > 0:
        current_user.to_read = current_user.to_read - 1
    db.session.commit()


# When a user open the sent messages the notifications are removed changing the local
# flag read to True
def set_all_read(list_read):
    sent = current_user.sent
    messages = Messages().to_messages(sent)
    for id in list_read:
        for msg in messages.messages:
            if id == msg.id:
                msg.read = True
    current_user.sent = messages.to_string()
    current_user.read = ''
    db.session.commit()    


# Check if the message is valid to be sent
def validate_message(message):
    updated_list = []
    recipients = message.dest
    # get the recipients list 
    recipients_list = recipients.split(", ")
    len_lis = len(recipients_list)
    removed_dst = ''
    # check if the recipients are registered
    not_registered = check_dests(recipients_list)
    if not_registered != "":
        return (USER_INEXISTENT, not_registered)
    # check if the recipients are deleted (but still registered because they
    # don't have empty scheduled queue)
    deleted = check_deleted(recipients_list)
    if deleted != "":
        return (USER_INEXISTENT, deleted)
    # check if the sender is in one of the recipient's blacklist 
    blacklist = check_blacklist(recipients_list, current_user)
    if blacklist != "":
        return (BLACKLIST, blacklist)
    # check for each recipient if there is someone that doesn't accept one
    # of the words in the body
    for item in recipients_list:
        if check_words(message, item):
            if removed_dst == '':
                removed_dst = item
            else:
                removed_dst = removed_dst + ", " + item
        else:
            updated_list.append(item)
    return result_send(updated_list, len_lis, message, removed_dst)


# Check message body to avoid forbidden words for a particular receiver
def check_words(message, rec):
    receiver = db.session.query(User).filter(User.email == rec).first()
    forbidden_words = receiver.forbidden_words
    if not forbidden_words:
        return False
    forbidden_words = forbidden_words.split(", ")
    msg = message.to_string()
    msg_arr = re.split('\W', msg)
    for word in forbidden_words:
        if word in msg_arr:
            return True
    return False


# Check if all the recipients of the message are registered
def check_dests(recipients_list):
    unregistered = ""
    registered_users = []
    users = db.session.query(User)
    # get a list of all registered users
    for u in users:
        registered_users.append(u.email)
    # for each recipient, check if it is in the list of registered user
    for item in recipients_list:
        # if there is a not registered user, return its email
        if item not in registered_users:
            if unregistered == "":
                unregistered = unregistered + item
            else:
                unregistered = unregistered + ", " + item
    return unregistered

# Check if all the recepients are not deleted
def check_deleted(recipients_list):
    deleted = ""
    deleted_users = []
    users = db.session.query(User)
    # get a list of all registered users
    for u in users:
        if(u.deleted == True):
            deleted_users.append(u.email)
    for item in recipients_list:
        if item in deleted_users:
            if deleted == "":
                deleted = deleted + item
            else:
                deleted = deleted + ", " + item
    return deleted

# Check if the sender is in one of the recipient's blacklist
def check_blacklist(recipients_list, sender):
    blacklisted_by = ""
    # for each recipient get the black list and ensure the sender is not present
    for item in recipients_list:
        q = db.session.query(User).filter(User.email == item)
        user = q.first()
        blacklist = (user.blacklist).split(", ")
        # if the sender is in the recipient "item" blacklist, return the recipient
        if sender.email in blacklist:
            if blacklisted_by == "":
                blacklisted_by = blacklisted_by + item
            else:
                blacklisted_by = blacklisted_by + ", " + item
    return blacklisted_by


# Auxiliary fuction to check if the message can be sent 
# or there are some problems, content or recipients related
def result_send(updated_list, len_lis, message, removed_dst):
    # now the recipients list is updated
    # if there are no words forbidden for any recipient in the list
    # the message can be scheduled
    if len(updated_list) == len_lis:
        send_message(message)
        return (SCHEDULED, [])
    # else someone of the recipients has been removed
    else:
        # if the updated list is empty, the sender has to change the message body
        # because the message will not be sent to anyone
        if len(updated_list) == 0:
            return (CHANGE_BODY, [])
        # else, the recipients list is not empty, so the message will be sent 
        # to the recipients who accept the body of the message
        else:
            updated_dest = ''.join(updated_list)
            message.dest = updated_dest
            send_message(message)
            return (FORBIDDEN_WORDS, removed_dst)


# Draft a message when user tap the draft button for a new message
def draft_new_message(message):
    # save to db the last index
    current_user.last_draft_id = message.id
    # get the draft messages of current user
    draft = current_user.draft
    # create a new queue of messages with the written message
    messages = Messages()
    messages.enqueue(message)
    # check if the user draft queue is empty
    if (draft == '[]'):
        current_user.draft = messages.to_string()
    else:
        messages = Messages().to_messages(draft)
        messages.enqueue(message)
        current_user.draft = messages.to_string()
    db.session.commit()


# Draft a message when user tap the save button
def update_draft_message(old, new):
    # get the draft messages of current user
    draft = current_user.draft
    messages = Messages().to_messages(draft)
    # find the message with same id and swap it
    for msg in messages.messages:
        if msg.id == old.id:
            msg.dest = new.dest
            msg.body = new.body
            msg.time = new.time
            msg.image = new.image
            msg.bold = new.bold
            msg.italic = new.italic
            msg.underline = new.underline
            # msg.id = new.id
            # avoid pythest missing
            # break
    current_user.draft = messages.to_string()
    db.session.commit()


# Remove the draft from draft when it has been sent
def draft_remove(message):
    if not message:
        return
    # get the draft messages of current user
    draft = current_user.draft
    messages = Messages().to_messages(draft)
    # find the message with same id and swap it
    for msg in messages.messages:
        if msg.id == message.id:
            messages.messages.remove(msg)
            break
    current_user.draft = messages.to_string()
    db.session.commit()


# Send a message when user tap the save button
def send_message(message):
    #current_user.last_draft_id = message.id
    messages = Messages()
    messages.enqueue(message)
    # get the to_be_sent messages of current user
    to_be_sent = current_user.to_be_sent
    # check if the user to_be_sent queue is empty
    if (to_be_sent == '[]'):
        current_user.to_be_sent = messages.to_string()
    else:
        messages = Messages().to_messages(to_be_sent)
        messages.enqueue(message)
        current_user.to_be_sent = messages.to_string()
    db.session.commit()


# build a new message if msg is None, else edit msg 
# (build a new message with same id of msg)
def build_message(form, msg):
    # covert date to string
    str_date = date_to_string(form.date.data, form.time.data)
    # check if there is an image attached
    file = form.photo.data
    image_string = msg.image if msg else None
    if request.form.get('confirm') and request.form.get('confirm') == '0':
        image_string = None
    elif request.form.get('confirm') and request.form.get('confirm') == '1':
        byte_image = b64encode(file.read())
        image_string = byte_image.decode('utf-8')
    # build the message to draft or to send
    id = msg.id if msg else None
    bold = True if request.form.get('bold') else False
    italic = True if request.form.get('italic') else False
    underline = True if request.form.get('underline') else False
    return Message(current_user.email, form.receiver.data, 
        form.body.data, str_date, id, image_string, False,
        bold, italic, underline)


# Return the message with id 'id' 
def get_message_by_id(messages, id):
    m = None
    for message in messages:
        if (message.id == id):
            # avoid pytest missing
            m = message
    return m


# Programatically fill a message form
def fill_message_form_from_message(message):
    date = datetime.strptime(message.time.split(' ')[0], '%d/%m/%Y')
    time = datetime.strptime(message.time.split(' ')[1], '%H:%M')
    form = MessageForm()
    form.receiver.data = message.dest
    form.body.data = message.body
    form.date.data = date
    form.time.data = time
    form.choice.data = 'Schedule'
    return form


# covert the date into a string
def date_to_string(date, time):
    try:
        str_date = date.strftime('%d/%m/%Y')
    except:
        str_date = ''
    try:
        str_time = time.strftime('%H:%M')
    except: 
        str_time = ''
    return str_date + ' ' + str_time        


# Given the body, the sender and the date, returns the filtered messages
def search_messages(msg_field, msg_user, msg_date):
    res_to_be_sent=[]
    res_received=[]
    res_sent=[]
    to_be_sent_messages = Messages().to_messages(current_user.to_be_sent).messages
    received_messages = Messages().to_messages(current_user.received).messages
    sent_messages=Messages().to_messages(current_user.sent).messages
    

    if not msg_field and not msg_user and not msg_date:
        return 0,0,0

    if msg_date:
        try:
            msg_date=datetime.strptime(msg_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            print(msg_date)
        except:
            return "error"
    for cm in to_be_sent_messages:
        if msg_field in cm.body and msg_user in cm.sender and msg_date in cm.time:
            if msg_field or msg_user or msg_date: 
                res_to_be_sent.append(cm)

    for cm in sent_messages:
        if msg_field in cm.body and msg_user in cm.sender and msg_date in cm.time:
            res_sent.append(cm)
    
    for cm in received_messages:
        if msg_field in cm.body and msg_user in cm.sender and msg_date in cm.time:
            res_received.append(cm)

    return res_received,res_sent,res_to_be_sent

