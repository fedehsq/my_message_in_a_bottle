from monolith.database import Message
import unittest

# Tester class for the auxiliary classes Message operations
# 1. Get the string corresponding to the Message object, in order to be saved later in the database

class TestMessageClasses(unittest.TestCase):

    def test_msg_to_string(self):
        msg = Message("example@example.com", "example@example.com", "Ciao!", "12/12/2010 12:35", False) 
        # get the id assigned to a msg
        self.assertEqual(msg.to_string(), '{"id": "' + msg.id + '", "sender": "example@example.com", "dest": "example@example.com", "body": "Ciao!", "time": "12/12/2010 12:35", "image": "", "read": false, "bold": false, "italic": false, "underline": false}')
       