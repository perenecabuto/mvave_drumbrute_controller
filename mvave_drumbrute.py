import os
import time
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import multiprocessing

from simple_term_menu import TerminalMenu
import fire
import rtmidi


class MVaveDrumbrute():
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
            logging.info("DEACTIVATE BPM MODE")
            self.change_mode_start = None
            return
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


def main(
    input_port: int | None = None,
    output_port: int | None = None,
):
    midi_out = rtmidi.MidiOut()
    midi_in = rtmidi.MidiIn()

    available_inputs = midi_in.get_ports()
    inputs_menu = TerminalMenu(available_inputs, title="Select midi input")
    if input_port is None:
        input_port = inputs_menu.show()

    available_outputs = midi_out.get_ports()
    outputs_menu = TerminalMenu(available_outputs, title="Select midi output")
    if output_port is None:
        output_port = outputs_menu.show()

    logging.info(
        'Selected MIDI ports:\nINPUT %d (%s)\nOUTPUT %d (%s)\n',
        input_port, available_inputs[input_port],
        output_port, available_outputs[output_port],
    )


    manager = multiprocessing.Manager()
    global_bpm = manager.Value('current_bpm', 120)

    midi_connector = MVaveDrumbrute(change_bpm_callback=global_bpm.set)

    behaviour = defaultdict(lambda: lambda *args: logging.warn(
        f'Nothing found for {[a for a in args if "MidiOut" not in a.__class__.__name__]}'))
    behaviour[(185, 0)] = lambda *args: None
    behaviour[(201, 0)] = midi_connector.toggle_play_behaviour
    behaviour[(193, 1)] = midi_connector.previous_pattern_behaviour
    behaviour[(153, 42)] = midi_connector.next_pattern_behaviour
    behaviour[(153, 49)] = midi_connector.change_mode_behaviour

    def clock_task():
        clock_tick = 0xF8
        midi_out.open_port(output_port)
        while True:
            bpm = global_bpm.value
            pulse_rate = 60.0 / (bpm * 24)
            midi_out.send_message([clock_tick, 255, 255])
            t1 = time.perf_counter()
            if bpm <= 3000:
                time.sleep(pulse_rate * 0.8)
            t2 = time.perf_counter()
            while (t2 - t1) < pulse_rate:
                t2 = time.perf_counter()

    def midi_listener_task():
        midi_out.open_port(output_port)
        midi_in.open_port(input_port)

        last_message_time = time.time()
        while True:
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
                    behaviour[(midi_msg_type, midi_msg_data)](midi_out, midi_msg, delta_seconds)
                except ValueError as e:
                    logging.error("Can't process message: %s", message, exc_info=True)

            time.sleep(0.001)


    clock_watcher = multiprocessing.Process(target=clock_task)
    midi_watcher = multiprocessing.Process(target=midi_listener_task)

    midi_watcher.start()
    logging.info("Starting to send clock...")
    clock_watcher.start()
    logging.info("Starting MIDI message processing loop...")

    while True:
        pass


if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO'))
    fire.Fire(main)

