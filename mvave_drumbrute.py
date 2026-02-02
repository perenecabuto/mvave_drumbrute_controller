import os
import logging
import multiprocessing

from simple_term_menu import TerminalMenu
import fire
import rtmidi
import sqlitedict

from midi_clock import MidiClock
from midi_listener import MidiInListener
from controller import DrumbruteController


DEFAULT_DB_FILE_PATH = 'mvave_drumbrute_state.db'


def main(
    input_port: int | None = None,
    output_port: int | None = None,
    db_file_path: str | None = DEFAULT_DB_FILE_PATH,
):
    midi_out = rtmidi.MidiOut()
    midi_in = rtmidi.MidiIn()

    db = sqlitedict.SqliteDict(db_file_path, autocommit=True)

    available_inputs = midi_in.get_ports()
    if input_port is None:
        input_port = db.get('input_port', None)
        inputs_menu = TerminalMenu(
            available_inputs,
            cursor_index=input_port,
            title="Select midi input")
        input_port = inputs_menu.show()

    db['input_port'] = input_port

    available_outputs = midi_out.get_ports()
    if output_port is None:
        output_port = db.get('output_port', None)
        outputs_menu = TerminalMenu(
            available_outputs,
            cursor_index=output_port,
            title="Select midi output")
        output_port = outputs_menu.show()

    db['output_port'] = output_port

    logging.info(
        'Selected MIDI ports:\nINPUT %d (%s)\nOUTPUT %d (%s)\n',
        input_port, available_inputs[input_port],
        output_port, available_outputs[output_port],
    )

    manager = multiprocessing.Manager()
    global_bpm = manager.Value('current_bpm', 120)

    drumbrute = DrumbruteController(change_bpm_callback=global_bpm.set)

    listener = MidiInListener()
    listener.add_behaviour((185, 0), lambda *args: None)
    listener.add_behaviour((201, 0), drumbrute.toggle_play_behaviour)
    listener.add_behaviour((193, 1), drumbrute.previous_pattern_behaviour)
    listener.add_behaviour((153, 42), drumbrute.next_pattern_behaviour)
    listener.add_behaviour((153, 49), drumbrute.change_mode_behaviour)

    midi_clock = MidiClock(get_bpm_fn=lambda: global_bpm.value)

    clock_watcher = multiprocessing.Process(
        target=midi_clock.run,
        args=(midi_out, output_port))
    midi_watcher = multiprocessing.Process(
        target=listener.run,
        args=(midi_in, input_port, midi_out, output_port))

    midi_watcher.start()
    logging.info("Starting MIDI listener...")
    clock_watcher.start()
    logging.info("Starting MIDI clock...")

    while True:
        pass


if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO'))
    fire.Fire(main)

