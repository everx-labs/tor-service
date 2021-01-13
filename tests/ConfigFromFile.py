import os
import logging
import unittest

from torauth import Config

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))


class ConfigFromFile(unittest.TestCase):
    def test(self):
        env_file = os.path.join(os.path.dirname(__file__), '.env.test')

        config = Config(env_file)
        self.assertEqual(config.root_initial_value, '123')
