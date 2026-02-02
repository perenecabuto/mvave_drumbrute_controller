import os
import logging
import multiprocessing

from simple_term_menu import TerminalMenu
import fire
import rtmidi

from midi_clock import MidiClock
from midi_listener import MidiInListener
from controller import DrumbruteController


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

