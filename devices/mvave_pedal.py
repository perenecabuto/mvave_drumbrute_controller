import time
import logging
from typing import Callable

from devices.midi_connector import MidiInOutConnector
from enum import Enum


class PedalButton(Enum):
    A_PRESS = (201, 0)
    A_RELEASE = (185, 0)
    B_PRESS = (193, 1)
    C_PRESS = (153, 49)
    C_RELEASE = (153, 42)


Behavior = Callable[[MidiInOutConnector, list[int], float], None]


class MVavePedalListener():

    def __init__(
        self,
        change_mode_threshold: int = 5,
        change_mode_button: PedalButton = PedalButton.C_PRESS,
    ):
        self.change_mode_threshold = change_mode_threshold
        self.change_mode_button = change_mode_button
        self._play_behaviours = {}
        self._bpm_behaviours = {}

        self._on_event = lambda *args: None
        self._on_start = lambda midi_connector: None
        self._change_mode_start = None
        self._skip_next_message = False

    @property
    def is_in_bpm_mode(self) -> bool:
        if not self._change_mode_start:
            return False
        elapsed_time = time.time() - self._change_mode_start if self._change_mode_start else 0
        return elapsed_time >= self.change_mode_threshold

    def start_bpm_mode(self):
        if not self._change_mode_start:
            self._change_mode_start = time.time()

    def set_play_mode(self, skip_next_message=False):
        self._change_mode_start = None
        self._skip_next_message = skip_next_message

    def add_play_behaviour(self, pedal_btn: PedalButton, callback: Behavior):
        if pedal_btn == self.change_mode_button:
            raise ValueError("Change mode button cannot be used for play behaviour")
        self._play_behaviours[pedal_btn] = callback

    def add_bpm_behaviour(self, pedal_btn: PedalButton, callback: Behavior):
        if pedal_btn == self.change_mode_button:
            raise ValueError("Change mode button cannot be used for BPM behaviour")
        self._bpm_behaviours[pedal_btn] = callback

    def on_start(self, callback: Behavior):
        self._on_start = callback
        return self

    def on_event(self, callback: Behavior):
        self._on_event = callback
        return self

    def _skip_message(self) -> bool:
        skip = bool(self._skip_next_message)
        self._skip_next_message = False
        return skip

    def _get_behavior_for_button(self, pedal_btn: PedalButton):
        if pedal_btn == self.change_mode_button:
            if not self.is_in_bpm_mode:
                logging.info("ACTIVATE BPM MODE (%d seconds)", self.change_mode_threshold)
                return lambda *args: self.start_bpm_mode()
            else:
                logging.info("TOGGLE BACK TO PLAY MODE")
                return lambda *args: self.set_play_mode(skip_next_message=True)

        if self.is_in_bpm_mode:
            return self._bpm_behaviours.get(pedal_btn, None)

        self.set_play_mode()
        return self._play_behaviours.get(pedal_btn, None)

    def listen(self, stop_event, midi_connector: MidiInOutConnector):
        midi_connector.open_ports()

        if self._on_start:
            self._on_start(midi_connector)

        last_message_time = time.time()
        while not stop_event.is_set():
            time.sleep(0.001)

            message = midi_connector.get_input_message()
            if not message:
                continue
            if self._skip_message():
                continue

            _time = time.time()
            delta_seconds = round(_time - last_message_time)
            last_message_time = _time

            if self._on_event:
                self._on_event(message, delta_seconds)

            # (midi_msg, delta_seconds) = message
            (midi_msg, _) = message
            midi_msg_type = midi_msg[0]
            midi_msg_data = midi_msg[1] if len(midi_msg) >= 2 else -1
            # midi_msg_key = midi_msg[2] if len(midi_msg) >= 3 else -1
            try:
                midi_btn = PedalButton((midi_msg_type, midi_msg_data))
            except ValueError:
                logging.debug('Button not mapped: %s', (midi_msg_type, midi_msg_data))
                continue
            behaviour_callback = self._get_behavior_for_button(midi_btn)
            if behaviour_callback:
                behaviour_callback(midi_connector, midi_msg, delta_seconds)
            else:
                logging.debug('Nothing found for %s', midi_msg)
