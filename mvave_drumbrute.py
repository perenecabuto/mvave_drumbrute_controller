import os
import logging
import multiprocessing
import time

from simple_term_menu import TerminalMenu
import fire
import rtmidi

from state_store import StateStore
from midi_clock import MidiClock
from midi_listener import MidiInListener, \
    PEDAL_BUTTON_A_PRESS, PEDAL_BUTTON_A_RELEASE, PEDAL_BUTTON_B_PRESS, PEDAL_BUTTON_C_RELEASE
from controller import DrumbruteController
from actions import BehaviorController


DEFAULT_DB_FILE_PATH = 'mvave_drumbrute_state.db'


def main(
    input_port: int | None = None,
    output_port: int | None = None,
    db_file_path: str | None = DEFAULT_DB_FILE_PATH,
):
    midi_out = rtmidi.MidiOut()
    midi_in = rtmidi.MidiIn()

    state_store = StateStore(db_file_path)

    available_inputs = midi_in.get_ports()
    if input_port is None:
        inputs_menu = TerminalMenu(
            available_inputs,
            cursor_index=state_store.input_port,
            title="Select midi input")
        input_port = inputs_menu.show()
    state_store.set_input_port(input_port)

    available_outputs = midi_out.get_ports()
    if output_port is None:
        outputs_menu = TerminalMenu(
            available_outputs,
            cursor_index=state_store.output_port,
            title="Select midi output")
        output_port = outputs_menu.show()
    state_store.set_output_port(output_port)

    logging.info(
        'Selected MIDI ports:\nINPUT %d (%s)\nOUTPUT %d (%s)\n',
        input_port, available_inputs[input_port],
        output_port, available_outputs[output_port],
    )

    logging.info(
        'LAST PATTERN:%d BPM:%d',
        state_store.pattern + 1, state_store.bpm
    )

    clock = MidiClock()
    clock.set_bpm(state_store.bpm)
    drumbrute = DrumbruteController()
    # drumbrute.change_pattern(midi_out, state_store.pattern)

    actions = BehaviorController(
        drumbrute,
        state_store,
        clock,
        max_bpm=300,
    )

    listener = MidiInListener(change_mode_threshold=3)
    # listener.on_event(lambda *args: logging.info(str(list(sqlitedict.SqliteDict(db_file_path).items()))))
    listener.add_play_behaviour(PEDAL_BUTTON_A_RELEASE, actions.null_behaviour)
    listener.add_play_behaviour(PEDAL_BUTTON_A_PRESS, actions.toggle_play_behaviour)
    listener.add_play_behaviour(PEDAL_BUTTON_B_PRESS, actions.previous_pattern_behaviour)
    listener.add_play_behaviour(PEDAL_BUTTON_C_RELEASE, actions.next_pattern_behaviour)
    #
    listener.add_bpm_behaviour(PEDAL_BUTTON_A_PRESS, actions.increase_bpm_behaviour)
    listener.add_bpm_behaviour(PEDAL_BUTTON_B_PRESS, actions.decrease_bpm_behaviour)

    stop_event = multiprocessing.Event()

    clock_watcher = multiprocessing.Process(
        target=clock.run,
        args=(stop_event, midi_out, output_port))
    midi_watcher = multiprocessing.Process(
        target=listener.run,
        args=(stop_event, midi_in, input_port, midi_out, output_port))

    midi_watcher.start()
    logging.info("Starting MIDI listener...")
    clock_watcher.start()
    logging.info("Starting MIDI clock...")

    try:
        while midi_watcher.is_alive() or clock_watcher.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()
        stop_event.set()
        print("Main process: caught keyboard interrupt, terminating workers,")

    midi_watcher.join()  # Wait for the worker process to finish
    clock_watcher.join()  # Wait for the worker process to finish
    logging.info("Main process: workers joined, exiting.")


if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO'))
    fire.Fire(main)
