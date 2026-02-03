import time
import logging

from midi_connector import MidiInOutConnector


PEDAL_BUTTON_A_PRESS = (201, 0)
PEDAL_BUTTON_A_RELEASE = (185, 0)
PEDAL_BUTTON_B_PRESS = (193, 1)
PEDAL_BUTTON_C_PRESS = (153, 49)
PEDAL_BUTTON_C_RELEASE = (153, 42)


class MidiInListener():

    def __init__(
        self,
        change_mode_threshold: int = 5,
        change_mode_button: tuple = PEDAL_BUTTON_C_PRESS,
    ):
        self.change_mode_threshold = change_mode_threshold
        self.change_mode_button = change_mode_button
        self._play_behaviours = {}
        self._bpm_behaviours = {}

        self._on_event = lambda *args: None
        self._on_start = lambda midi_connector: None
        self._change_mode_start = None

    @property
    def is_in_bpm_mode(self) -> bool:
        if not self._change_mode_start:
            return False
        elapsed_time = time.time() - self._change_mode_start if self._change_mode_start else 0
        return elapsed_time >= self.change_mode_threshold

    def add_play_behaviour(self, in_code, callback):
        if in_code == self.change_mode_button:
            raise ValueError("Change mode button cannot be used for play behaviour")

        self._play_behaviours[in_code] = callback

    def add_bpm_behaviour(self, in_code, callback):
        self._bpm_behaviours[in_code] = callback

    def on_start(self, callback):
        self._on_start = callback
        return self

    def on_event(self, callback):
        self._on_event = callback
        return self

    def run(self, stop_event, midi_connector: MidiInOutConnector):
        midi_connector.open_ports()

        if self._on_start:
            self._on_start(midi_connector)

        ignore_next = False
        last_message_time = time.time()
        while not stop_event.is_set():
            message = midi_connector.get_input_message()
            if ignore_next:
                ignore_next = False
                continue
            if message:
                _time = time.time()
                delta_seconds = round(_time - last_message_time)
                last_message_time = _time
                try:
                    # (midi_msg, delta_seconds) = message
                    (midi_msg, _) = message
                    midi_msg_type = midi_msg[0]
                    midi_msg_data = midi_msg[1] if len(midi_msg) >= 2 else -1
                    midi_msg_key = midi_msg[2] if len(midi_msg) >= 3 else -1
                    logging.debug(
                        "MIDI IN: type:%s, data:%s, key:%s, delta:{%f:0.000f}s",
                        midi_msg_type, midi_msg_data, midi_msg_key, delta_seconds,
                    )

                    if self._on_event:
                        self._on_event(message)

                    map_key = (midi_msg_type, midi_msg_data)
                    if map_key == self.change_mode_button:
                        if not self.is_in_bpm_mode:
                            self.start_bpm_mode()
                        else:
                            self.set_play_mode()
                            ignore_next = True
                        continue

                    if not self.is_in_bpm_mode:
                        self.set_play_mode()

                    behaviours = self._play_behaviours \
                        if not self.is_in_bpm_mode else self._bpm_behaviours
                    if map_key in behaviours:
                        behaviours[map_key](midi_connector, midi_msg, delta_seconds)
                    else:
                        logging.warning('Nothing found for %s', midi_msg)
                except Exception:  # pylint: disable=broad-except
                    logging.error("Can't process message: %s", message, exc_info=True)

            time.sleep(0.001)

    def start_bpm_mode(self):
        logging.info("ACTIVATE BPM MODE %s", self.change_mode_threshold)
        if not self._change_mode_start:
            self._change_mode_start = time.time()

    def set_play_mode(self):
        logging.info("DEACTIVATE BPM MODE")
        self._change_mode_start = None
