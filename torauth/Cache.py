import time
from typing import Any


class Cache:
    ''' Inner cache for registered callbacks '''

    def __init__(self):
        self.data = {}

    def add(self, public_key: str, retention_sec: int, rand: str, context: Any) -> None:
        '''
        Saves data in a dictionary
        : param public_key: user public key
        : param context: serializable context
        : param retention_sec: time period to keep data
        '''
        self.data[public_key] = {
            'context': context,
            'rand': rand,
            'timestamp': time.time(),
            'retention_sec': retention_sec
        }

    def clean_obsolete(self):
        obsolete_contexts = []
        for k in list(self.data):
            v = self.data[k]
            if v['timestamp'] + v['retention_sec'] < time.time():
                obsolete_contexts.append(v['context'])
                del self.data[k]
        return obsolete_contexts

    def get(self, key):
        return self.data.get(key)

    def remove(self, key):
        return self.data.pop(key)
