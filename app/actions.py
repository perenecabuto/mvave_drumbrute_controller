import time
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
        self.midi_clock.set_bpm(self.state_store.bpm)
        self.drumbrute.change_pattern(midi_connector, self.state_store.pattern)

    def previous_pattern_behaviour(self, midi_connector: MidiInOutConnector, midi_msg, delta):
        self._change_pattern(midi_connector, self.state_store.pattern - 1)

    def next_pattern_behaviour(self, midi_connector: MidiInOutConnector, midi_msg, delta):
        self._change_pattern(midi_connector, self.state_store.pattern + 1)

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
        pattern_num = min(max(0, pattern_num), self.drumbrute.max_patterns - 1)
        if pattern_num == self.state_store.pattern:
            return
        self.drumbrute.change_pattern(midi_connector, pattern_num)
        self.state_store.set_pattern(pattern_num)
        self._update_bpm(self.state_store.bpm)

    def _update_bpm(self, bpm: int):
        bpm = max(0, min(bpm, self.max_bpm))
        self.midi_clock.set_bpm(bpm)
        self.state_store.set_bpm(bpm)
        logging.info('CHANGE PATTERN:%s BPM:%d', self.state_store.pattern + 1, bpm)
