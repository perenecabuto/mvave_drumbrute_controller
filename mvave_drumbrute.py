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


def select_midi_port(
    state_store: StateStore | None,
    midi: rtmidi.MidiIn | rtmidi.MidiOut,
    port: int | str | None,
    name: str = "midi",
    quiet: bool = False,
) -> tuple[int, list[str]]:
    available_ports = midi.get_ports()
    if port is None:
        port = state_store.input_port
        try:
            port = int(port)
        except TypeError:
            port = None
        except ValueError:
            port = None
    if not quiet:
        port = TerminalMenu(
            available_ports,
            cursor_index=port,
            title=f'Select a {name} port'
        ).show()

    assert port is not None, f"could not select {name} port"
    state_store.set_input_port(port)

    return port, available_ports


def main(
    input_port: int | None = None,
    output_port: int | None = None,
    db_file_path: str | None = DEFAULT_DB_FILE_PATH,
    quiet: bool = False,
):
    midi_out = rtmidi.MidiOut()
    midi_in = rtmidi.MidiIn()
    state_store = StateStore(db_file_path)

    input_port, available_inputs = select_midi_port(
        state_store,
        midi_in, input_port,
        name="midi input",
        quiet=quiet,
    )

    output_port, available_outputs = select_midi_port(
        state_store,
        midi_out, output_port,
        name="midi output",
        quiet=quiet,
    )

    logging.info(
        'Selected MIDI ports:\nINPUT %d (%s)\nOUTPUT %d (%s)\nLAST PATTERN:%d BPM:%d',
        input_port, available_inputs[input_port],
        output_port, available_outputs[output_port],
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
