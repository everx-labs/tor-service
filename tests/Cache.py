import asyncio
from unittest import TestCase, IsolatedAsyncioTestCase
from torauth.Cache import Cache

cache = Cache()


class TestCache_1(TestCase):

    def test_add(self):
        cache.add(public_key='abc0', retention_sec=10,
                  rand='000', context={'a': 'rec0'})
        cache.add(public_key='abc1', retention_sec=60,
                  rand='001', context={'a': 'rec1'})
        cache.add(public_key='abc2', retention_sec=60,
                  rand='002', context={'a': 'rec2'})
        cache.add(public_key='abc3', retention_sec=10,
                  rand='003', context={'a': 'rec3'})

    def test_get(self):
        x = cache.get('abc2')
        self.assertEqual(x['context'], {'a': 'rec2'})

    def test_remove(self):
        x = cache.remove('abc2')
        x = cache.get('abc2')
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
        self.assertEqual(cache.get('abc0'), None)
        self.assertEqual(cache.get('abc3'), None)

        # Try to get remained entry
        x = cache.get('abc1')
        self.assertEqual(x['context'], {'a': 'rec1'})
