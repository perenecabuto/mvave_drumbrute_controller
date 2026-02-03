import os
import logging
import multiprocessing
import time

from simple_term_menu import TerminalMenu
import fire

from state_store import StateStore
from midi_clock import MidiClock
from midi_connector import MidiInOutConnector
from midi_listener import MidiInListener, \
    PEDAL_BUTTON_A_PRESS, PEDAL_BUTTON_A_RELEASE, PEDAL_BUTTON_B_PRESS, PEDAL_BUTTON_C_RELEASE
from controller import DrumbruteController
from actions import BehaviorController


DEFAULT_DB_FILE_PATH = 'mvave_drumbrute_state.db'


def select_midi_port(
    available_ports: list[str],
    port: int | str | None,
    label: str = "midi",
    query: str | None = None,
    quiet: bool = False,
) -> tuple[int, list[str]]:
    if port >= len(available_ports):
        port = 0
    try:
        port = int(port)
    except:  # pylint: disable=bare-except
        port = 0

    if not port and query:
        port = next((
            i for i, port_name in enumerate(available_ports)
            if query.lower() in port_name.lower()), 0)

    if not quiet:
        port = TerminalMenu(
            available_ports,
            cursor_index=port,
            title=f'Select a {label} port'
        ).show()

    assert port is not None, f"could not select {label} port"
    return port, available_ports


def main(
    input_port: int | None = None,
    output_port: int | None = None,
    db_file_path: str | None = DEFAULT_DB_FILE_PATH,
    quiet: bool = False,
):
    midi_connector = MidiInOutConnector(
        input_port if input_port is not None else 0,
        output_port if output_port is not None else 0,
    )
    state_store = StateStore(db_file_path)

    input_port, available_inputs = select_midi_port(
        midi_connector.get_input_ports(),
        state_store.input_port if input_port is None else input_port,
        label="midi input",
        query='SINCO',
        quiet=quiet,
    )
    state_store.set_input_port(input_port)

    output_port, available_outputs = select_midi_port(
        midi_connector.get_output_ports(),
        state_store.output_port if output_port is None else output_port,
        label="midi output",
        query='Arturia',
        quiet=quiet,
    )
    state_store.set_output_port(output_port)

    logging.info(
        'Selected MIDI ports:\nINPUT %d (%s)\nOUTPUT %d (%s)\nLAST PATTERN:%d BPM:%d',
        input_port, available_inputs[input_port],
        output_port, available_outputs[output_port],
        state_store.pattern + 1, state_store.bpm
    )

    clock = MidiClock()
    drumbrute = DrumbruteController()

    actions = BehaviorController(
        drumbrute,
        state_store,
        clock,
        max_bpm=300,
    )

    listener = MidiInListener(change_mode_threshold=3)
    listener.on_start(actions.on_start_behaviour)
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
        args=(stop_event, midi_connector))
    midi_watcher = multiprocessing.Process(
        target=listener.run,
        args=(stop_event, midi_connector))

    midi_watcher.start()
    logging.info("Starting MIDI listener...")
    clock_watcher.start()
    logging.info("Starting MIDI clock...")

    try:
        while midi_watcher.is_alive() and clock_watcher.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()
        stop_event.set()
        print("Main process: caught keyboard interrupt, terminating workers,")

    midi_watcher.join()  # Wait for the worker process to finish
    clock_watcher.join()  # Wait for the worker process to finish
    logging.info("Main process: workers joined, exiting.")


if __name__ == '__main__':
    if 'OUTPUT_FILE_PATH' in os.environ:
        print("SET OUTPUT FILE PATH", os.environ['OUTPUT_FILE_PATH'])
        logging.basicConfig(
            level=os.environ.get('LOG_LEVEL', 'INFO'),
            filename=os.environ['OUTPUT_FILE_PATH'],
            filemode='a',
        )
    else:
        logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO'))

    fire.Fire(main)
