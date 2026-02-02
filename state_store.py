import logging

import sqlitedict


class StateStore():
    def __init__(self, db_file_path):
        self._db_file_path = db_file_path

    @property
    def db(self):
        return sqlitedict.SqliteDict(self._db_file_path, autocommit=True)

    def set_input_port(self, input_port):
        self.db['input_port'] = input_port

    @property
    def input_port(self):
        return self.db.get('input_port')

    def set_output_port(self, output_port):
        self.db['output_port'] = output_port

    @property
    def output_port(self):
        return self.db.get('output_port')

    def set_pattern(self, pattern):
        self.db['last_pattern'] = pattern

    @property
    def pattern(self):
        return self.db.get('last_pattern', 0)

    def set_bpm(self, bpm):
        self.db[f'last_bpm_{self.pattern}'] = bpm

    @property
    def bpm(self):
        return self.db.get(f'last_bpm_{self.pattern}', 120)

