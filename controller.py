import time
import logging


class DrumbruteController():

    PC = 0xC0
    START = 0xFA
    STOP = 0xFC

    def __init__(
        self,
        channel:int = 10,
        filter_play_event_fn=None,
        change_bpm_callback=None,
    ):
        self.channel = channel

        self.filter_play_event_fn = filter_play_event_fn \
            if filter_play_event_fn is not None \
            else lambda _: True

        self.change_bpm_callback = change_bpm_callback \
            if change_bpm_callback is not None \
            else lambda bpm: None

        self.max_patterns = 16
        self.max_bpm = 300
        self.current_pattern = 0
        self.current_bpm = 120
        self.change_mode_threshold = 5

        self.playing = False
        self.change_mode_start = None

    def change_pattern(self, midi_out, pattern_num: int):
        cmd = self.PC + (self.channel - 1)
        midi_out.send_message([cmd, 0, pattern_num])
        self.current_pattern = pattern_num
        logging.info('CHANGE PATTERN to %d', pattern_num + 1)

    def change_bpm(self, bpm):
        self.current_bpm = max(0, min(bpm, self.max_bpm))
        self.change_bpm_callback(self.current_bpm)
        logging.info('CHANGE BPM to %d', self.current_bpm)

    def is_in_bpm_mode(self):
        elapsed_time = time.time() - self.change_mode_start if self.change_mode_start else 0
        in_bpm_mode = elapsed_time >= self.change_mode_threshold
        return in_bpm_mode

    def next_pattern_behaviour(self, midi_out, midi_msg, delta):
        if self.is_in_bpm_mode():
            self.change_mode_start = None
            return

        if self.change_mode_start:
            logging.info("DEACTIVATE BPM MODE")
            self.change_mode_start = None

        current_pattern = min(self.current_pattern + 1, self.max_patterns - 1)
        self.change_pattern(midi_out, current_pattern)

    def previous_pattern_behaviour(self, midi_out, midi_msg, delta):
        if self.is_in_bpm_mode():
            self.change_bpm(self.current_bpm + 1)
            return
        current_pattern = max(self.current_pattern - 1, 0)
        self.change_pattern(midi_out, current_pattern)

    def toggle_play_behaviour(self, midi_out, midi_msg, delta):
        if self.is_in_bpm_mode():
            self.change_bpm(self.current_bpm - 1)
            return
        if not self.filter_play_event_fn(midi_msg):
            return

        self.playing = not(self.playing)
        if self.playing:
            midi_out.send_message([self.START, 255, 255])
            logging.info(f'PLAY bpm=%d', self.current_bpm)
        else:
            midi_out.send_message([self.STOP, 255, 255])
            logging.info('PAUSE current_pattern=%d', self.current_pattern)

    def change_mode_behaviour(self, midi_out, midi_msg, delta):
        if not self.is_in_bpm_mode():
            logging.info(f'ENTERING HOLD MODE: hold for %d s', self.change_mode_threshold)
            self.change_mode_start = time.time()

