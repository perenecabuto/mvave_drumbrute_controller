import os
import logging

import fire
from simple_term_menu import TerminalMenu

from app import mvave_drumbrute
from app.data import StateStore
from devices import MidiInOutConnector


DEFAULT_DB_FILE_PATH = '/tmp/mvave_drumbrute_state.db'


def setup_logging():
    if 'OUTPUT_FILE_PATH' in os.environ:
        print("SET OUTPUT FILE PATH", os.environ['OUTPUT_FILE_PATH'])
        logging.basicConfig(
            level=os.environ.get('LOG_LEVEL', 'INFO'),
            filename=os.environ['OUTPUT_FILE_PATH'],
            filemode='a',
        )
    else:
        logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO'))


def select_midi_port_from_menu(
    available_ports: list[str],
    port: int | str | None,
    label: str = "midi",
) -> tuple[int, list[str]]:
    if port is not None and port >= len(available_ports):
        port = 0
    try:
        port = int(port)
    except:  # pylint: disable=bare-except
        port = 0

    return TerminalMenu(
        available_ports,
        cursor_index=port,
        title=f'Select a {label} port'
    ).show()


def main(
    input_port: int | None = None,
    output_port: int | None = None,
    db_file_path: str | None = DEFAULT_DB_FILE_PATH,
    quiet: bool = False,
    auto_select: bool = False,
    input_query: str | None = 'SINCO',
    output_query: str | None = 'Arturia',
):
    midi_connector = MidiInOutConnector()
    state_store = StateStore(db_file_path)

    if auto_select:
        logging.info("Auto-selecting MIDI ports...")
        input_port = midi_connector.query_input_port(input_query)
        output_port = midi_connector.query_output_port(output_query)
    else:
        if input_port is None and input_query is not None:
            input_port = midi_connector.query_input_port(input_query)
        if output_port is None and output_query is not None:
            output_port = midi_connector.query_output_port(output_query)

    available_inputs = midi_connector.get_input_ports()
    available_outputs = midi_connector.get_output_ports()

    if not quiet:
        input_port = select_midi_port_from_menu(
            available_inputs,
            state_store.input_port if input_port is None else input_port,
            label="midi input",
        )
        state_store.set_input_port(input_port)

        output_port = select_midi_port_from_menu(
            available_outputs,
            state_store.output_port if output_port is None else output_port,
            label="midi output",
        )
        state_store.set_output_port(output_port)

    assert input_port is not None, "Input port must be set"
    assert output_port is not None, "Output port must be set"
    midi_connector.set_ports(input_port, output_port)

    logging.info(
        'Selected MIDI ports:\nINPUT %d (%s)\nOUTPUT %d (%s)\nLAST PATTERN:%d BPM:%d',
        input_port, available_inputs[input_port],
        output_port, available_outputs[output_port],
        state_store.pattern + 1, state_store.bpm
    )

    mvave_drumbrute.run(
        midi_connector,
        state_store,
    )


if __name__ == '__main__':
    setup_logging()
    fire.Fire(main)
