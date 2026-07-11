import dbm.gnu
from typing import Optional

from devices.midi_clock import DEFAULT_BPM


class StateStore:
    def __init__(self, db_file_path: str):
        self._db = dbm.gnu.open(db_file_path, "c")

    def close(self):
        self._db.close()

    def _get(self, key: str, default=None):
        value = self._db.get(key.encode())
        if value is None:
            return default
        return value.decode()

    def _set(self, key: str, value):
        self._db[key.encode()] = str(value).encode()

    def set_input_port(self, input_port: int):
        self._set("input_port", input_port)

    @property
    def input_port(self) -> Optional[int]:
        value = self._get("input_port")
        return None if value is None else int(value)

    def set_output_port(self, output_port: int):
        self._set("output_port", output_port)

    @property
    def output_port(self) -> Optional[int]:
        value = self._get("output_port")
        return None if value is None else int(value)

    def set_pattern(self, pattern: int):
        self._set("last_pattern", pattern)

    @property
    def pattern(self) -> int:
        return int(self._get("last_pattern", 0))

    def set_bpm(self, bpm: int):
        self._set(f"last_bpm_{self.pattern}", bpm)

    @property
    def bpm(self) -> int:
        return int(self._get(f"last_bpm_{self.pattern}", DEFAULT_BPM))

    def set_playing(self, playing: bool):
        self._set("playing", int(playing))

    @property
    def playing(self) -> bool:
        return bool(int(self._get("playing", 0)))
