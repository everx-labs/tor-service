import os
import logging
import unittest

from torauth import Config

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))

env_file = os.path.join(os.path.dirname(__file__), '.env.incomplete')


class ConfigFromIncompleteFile(unittest.TestCase):

    def test_1(self):
        #
        # Test 1.
        # Enviroment vars are not set, and NOT all required vars set in .env file
        # This test MUST raise TypeError
        #
        with self.assertRaises(TypeError) as cm:
            Config(env_file)

        self.assertEqual(str(cm.exception),
                         'Variable not set ROOT_INITIAL_VALUE')

    def test_2(self):
        # Test 2.
        # Some enviroment vars are already set, and some vars are set in .env file
        # As a result, all required variables are present

        os.environ['ROOT_INITIAL_VALUE'] = '200'

        config = Config(env_file)
        self.assertEqual(config.root_initial_value, '200')
        self.assertEqual(config.giver_address,
                         '0:356b2709c0a8492af0bf290e3a6cf5e0c0ff9f4457f1e83a01a8059f394b66c2')
