import time
from multiprocessing import Value
from multiprocessing.synchronize import Event

from devices.midi_connector import MidiInOutConnector

DEFAULT_BPM = 120
CLOCK_TICK_CMD = 0xF8


class MidiClock():

    def __init__(self):
        self._bpm = Value('i', DEFAULT_BPM)

    @property
    def bpm(self):
        return self._bpm.value

    def set_bpm(self, bpm):
        with self._bpm.get_lock():
            self._bpm.value = bpm

    def run(
        self,
        stop_event: Event,
        midi_connector: MidiInOutConnector
    ):
        midi_connector.open_ports()

        while not stop_event.is_set():
            pulse_rate = 60.0 / (self.bpm * 24)
            midi_connector.send_message([CLOCK_TICK_CMD, 255, 255])
            t1 = time.perf_counter()
            if self.bpm <= 3000:
                time.sleep(pulse_rate * 0.8)
            t2 = time.perf_counter()
            while not stop_event.is_set() and (t2 - t1) < pulse_rate:
                t2 = time.perf_counter()
