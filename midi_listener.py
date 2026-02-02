import time
import logging


class MidiInListener():

    def __init__(self):
        self.behaviours = {}
        self._on_event = None

    def add_behaviour(self, in_code, callback):
        self.behaviours[in_code] = callback

    def on_event(self, callback):
        self._on_event = callback
        return self

    def run(self, stop_event, midi_in, input_port, midi_out, output_port):
        midi_in.open_port(input_port)
        midi_out.open_port(output_port)

        last_message_time = time.time()
        while not stop_event.is_set():
            message = midi_in.get_message()
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
                    if map_key in self.behaviours:
                        self.behaviours[map_key](midi_out, midi_msg, delta_seconds)
                    else:
                        logging.warn('Nothing found for %s', midi_msg)
                except Exception as e:
                    logging.error("Can't process message: %s", message, exc_info=True)

            time.sleep(0.001)
