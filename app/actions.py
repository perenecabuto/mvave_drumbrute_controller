import logging

from devices import MidiInOutConnector, Drumbrute, MidiClock
from app.data import StateStore


class BehaviorController():

    def __init__(
        self,
        drumbrute: Drumbrute,
        state_store: StateStore,
        midi_clock: MidiClock,
        max_bpm: int = 300,
    ):
        self.drumbrute = drumbrute
        self.state_store = state_store
        self.midi_clock = midi_clock
        self.max_bpm = max_bpm

        self.change_mode_start = None

    def on_start_behaviour(self, midi_connector: MidiInOutConnector):
        self._change_pattern(midi_connector, self.state_store.pattern)
        self._update_bpm(self.state_store.bpm)
        if self.state_store.playing:
            self.drumbrute.play(midi_connector)
        else:
            self.drumbrute.stop(midi_connector)

    def previous_pattern_behaviour(self, midi_connector: MidiInOutConnector, midi_msg, delta):
        self._change_pattern(midi_connector, self.state_store.pattern - 1)
        self._update_bpm(self.state_store.bpm)

    def next_pattern_behaviour(self, midi_connector: MidiInOutConnector, midi_msg, delta):
        self._change_pattern(midi_connector, self.state_store.pattern + 1)
        self._update_bpm(self.state_store.bpm)

    def toggle_play_behaviour(self, midi_connector: MidiInOutConnector, midi_msg, delta):
        playing = not self.state_store.playing
        if playing:
            self.drumbrute.play(midi_connector)
        else:
            self.drumbrute.stop(midi_connector)
        self.state_store.set_playing(playing)
        action = "PLAY" if playing else "STOP"
        logging.info('%s PATTERN:%d BPM:%d', action, self.state_store.pattern + 1, self.state_store.bpm)

    def increase_bpm_behaviour(self, midi_connector: MidiInOutConnector, midi_msg, delta):
        self._update_bpm(self.state_store.bpm + 1)

    def decrease_bpm_behaviour(self, midi_connector: MidiInOutConnector, midi_msg, delta):
        self._update_bpm(self.state_store.bpm - 1)

    def show_enter_bpm_behaviour(self, midi_connector: MidiInOutConnector, midi_msg, delta):
        logging.info('BPM MODE ACTIVATED')

    def _change_pattern(self, midi_connector: MidiInOutConnector, pattern_num: int):
        pattern_num = max(0, min(pattern_num, self._max_pattern_num() - 1))
        drumbrute_bank = pattern_num // self.drumbrute.max_patterns
        drumbrute_pattern = pattern_num % self.drumbrute.max_patterns

        logging.info(
            'DRUMBRUTE PATTERN:%d BANK:%d',
            drumbrute_pattern + 1, drumbrute_bank + 1)

        self.drumbrute.change_bank(midi_connector, drumbrute_bank)
        self.drumbrute.change_pattern(midi_connector, drumbrute_pattern)
        self.state_store.set_pattern(pattern_num)

    def _update_bpm(self, bpm: int):
        bpm = max(0, min(bpm, self.max_bpm))
        self.midi_clock.set_bpm(bpm)
        self.state_store.set_bpm(bpm)
        logging.info('CHANGE PATTERN:%s BPM:%d', self.state_store.pattern + 1, bpm)

    def _max_pattern_num(self):
        return self.drumbrute.max_patterns * self.drumbrute.max_banks
