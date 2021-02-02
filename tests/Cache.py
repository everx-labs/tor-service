import asyncio
from unittest import TestCase, IsolatedAsyncioTestCase
from torauth.Cache import Cache

cache = Cache()


class TestCache_1(TestCase):

    def test_add(self):
        cache.add(seq='0', webhook_url='https://ex.com/0', pin=None, retention_sec=10,
                  rand='000', context={'a': 'rec0'})
        cache.add(seq='1', webhook_url='https://ex.com/1', pin='pin1', retention_sec=60,
                  rand='001', context={'a': 'rec1'})
        cache.add(seq='2', webhook_url='https://ex.com/2', pin='pin2', retention_sec=60,
                  rand='010', context={'a': 'rec2'})
        cache.add(seq='3', webhook_url='https://ex.com/3', pin='pin3', retention_sec=10,
                  rand='011', context={'a': 'rec3'})

    def test_get(self):
        x = cache.get('2')
        self.assertEqual(x['context'], {'a': 'rec2'})

    def test_remove(self):
        x = cache.remove('2')
        x = cache.get('2')
        self.assertEqual(x, None)


class TestCache_2(IsolatedAsyncioTestCase):

    async def test_obsolete(self):
        await asyncio.sleep(11)

        # After this pause only one entry should remain
        obsoletes = cache.clean_obsolete()
        self.assertEqual(len(obsoletes), 2)
        self.assertEqual(obsoletes[0], {'a': 'rec0'})
        self.assertEqual(obsoletes[1], {'a': 'rec3'})

        # Try to get removed entries
        self.assertEqual(cache.get('0'), None)
        self.assertEqual(cache.get('3'), None)

        # Try to get remained entry
        x = cache.get('1')
        self.assertEqual(x['context'], {'a': 'rec1'})
        self.assertEqual(x['webhook_url'], 'https://ex.com/1')
