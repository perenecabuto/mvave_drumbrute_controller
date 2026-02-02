import multiprocessing
import time


class MidiClock():
    CLOCK_TICK_CMD = 0xF8
    DEFAULT_BPM = 120

    def __init__(self):
        self._bpm = multiprocessing.Value('i', self.DEFAULT_BPM)

    @property
    def bpm(self):
        return self._bpm.value

    def set_bpm(self, bpm):
        with self._bpm.get_lock():
            self._bpm.value = bpm

    def run(self, stop_event, midi_out, output_port):
        midi_out.open_port(output_port)

        while not stop_event.is_set():
            bpm = self.bpm
            pulse_rate = 60.0 / (bpm * 24)
            midi_out.send_message([self.CLOCK_TICK_CMD, 255, 255])
            t1 = time.perf_counter()
            if bpm <= 3000:
                time.sleep(pulse_rate * 0.8)
            t2 = time.perf_counter()
            while (t2 - t1) < pulse_rate:
                t2 = time.perf_counter()
