import time
import logging


class DrumbruteController():

    PC = 0xC0
    START = 0xFA
    STOP = 0xFC

    def __init__(
        self,
        state,
        channel:int = 10,
        filter_play_event_fn=None,
    ):
        self.state = state
        self.channel = channel

        self.filter_play_event_fn = filter_play_event_fn \
            if filter_play_event_fn is not None \
            else lambda _: True

        self.max_patterns = 16
        self.max_bpm = 300
        self.change_mode_threshold = 5

        self.playing = False
        self.change_mode_start = None

    @property
    def current_pattern(self):
        return self.state.pattern

    @property
    def current_bpm(self):
        return self.state.bpm

    def change_pattern(self, midi_out, pattern_num: int):
        pattern_num = max(0, min(pattern_num, self.max_patterns - 1))
        self.state.set_pattern(pattern_num)
        logging.info('SET PATTERN:%d BPM:%d', pattern_num + 1, self.current_bpm)
        cmd = self.PC + (self.channel - 1)
        midi_out.send_message([cmd, 0, pattern_num])

    def change_bpm(self, bpm):
        bpm = max(0, min(bpm, self.max_bpm))
        self.state.set_bpm(bpm)

        logging.info(
            'CHANGE BPM PATTERN:%d BPM:%d',
            self.current_pattern + 1, self.current_bpm)

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

        self.change_pattern(midi_out, self.current_pattern + 1)

    def previous_pattern_behaviour(self, midi_out, midi_msg, delta):
        if self.is_in_bpm_mode():
            self.change_bpm(self.current_bpm + 1)
            return

        self.change_pattern(midi_out, self.current_pattern - 1)

    def toggle_play_behaviour(self, midi_out, midi_msg, delta):
        if self.is_in_bpm_mode():
            self.change_bpm(self.current_bpm - 1)
            return

        if not self.filter_play_event_fn(midi_msg):
            return

        self.playing = not(self.playing)
        if self.playing:
            midi_out.send_message([self.START, 255, 255])
            logging.info(
                'PLAY PATTERN:%d BPM:%d',
                self.current_pattern + 1, self.current_bpm)
        else:
            midi_out.send_message([self.STOP, 255, 255])
            logging.info(
                'PAUSE PATTERN:%d BPM:%d',
                self.current_pattern + 1, self.current_bpm)

    def change_mode_behaviour(self, midi_out, midi_msg, delta):
        if not self.is_in_bpm_mode():
            logging.info(f'ENTERING HOLD MODE: hold for %d s', self.change_mode_threshold)
            self.change_mode_start = time.time()

