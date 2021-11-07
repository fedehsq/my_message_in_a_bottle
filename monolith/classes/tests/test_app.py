from monolith.app import create_app
import unittest

class TestApp(unittest.TestCase):
    def test_create_app(self):
        self.assertEqual(create_app().name, 'monolith.app')