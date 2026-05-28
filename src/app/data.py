import sqlitedict

from devices.midi_clock import DEFAULT_BPM


class StateStore():

    def __init__(self, db_file_path: str):
        self._db_file_path = db_file_path
        self._db = None

    @property
    def db(self):
        if self._db is None or self._db.conn is None or not self._db.conn.is_alive():
            self._db = sqlitedict.SqliteDict(self._db_file_path, autocommit=True)
        return self._db

    def set_input_port(self, input_port: int):
        self.db['input_port'] = input_port

    @property
    def input_port(self) -> int | None:
        return self.db.get('input_port')

    def set_output_port(self, output_port: int):
        self.db['output_port'] = output_port

    @property
    def output_port(self) -> int | None:
        return self.db.get('output_port')

    def set_pattern(self, pattern: int):
        self.db['last_pattern'] = pattern

    @property
    def pattern(self) -> int:
        return self.db.get('last_pattern', 0)

    def set_bpm(self, bpm: int):
        self.db[f'last_bpm_{self.pattern}'] = bpm

    @property
    def bpm(self) -> int:
        return self.db.get(f'last_bpm_{self.pattern}', DEFAULT_BPM)

    def set_playing(self, playing: bool):
        self.db['playing'] = playing

    @property
    def playing(self) -> bool:
        return self.db.get('playing', False)
