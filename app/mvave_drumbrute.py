
import logging
import multiprocessing
import time

from app.actions import BehaviorController
from app.data import StateStore
from devices import MidiInOutConnector, MidiClock, Drumbrute, MVavePedalListener, PedalButton


def run(
    midi_connector: MidiInOutConnector,
    state_store: StateStore,
):
    clock = MidiClock()
    drumbrute = Drumbrute()
    actions = BehaviorController(
        drumbrute,
        state_store,
        clock,
        max_bpm=300,
    )

    pedal = MVavePedalListener(
        change_mode_threshold=3,
        change_mode_button=PedalButton.C_PRESS
    )
    pedal.on_start(actions.on_start_behaviour)
    # pedal.on_event(lambda msg, delta: logging.debug(
    #     "MIDI IN: message:%s, delta:%0.000f}s", msg, delta))
    pedal.add_play_behaviour(PedalButton.A_PRESS, actions.toggle_play_behaviour)
    pedal.add_play_behaviour(PedalButton.B_PRESS, actions.previous_pattern_behaviour)
    pedal.add_play_behaviour(PedalButton.C_RELEASE, actions.next_pattern_behaviour)
    pedal.add_bpm_behaviour(PedalButton.A_PRESS, actions.decrease_bpm_behaviour)
    pedal.add_bpm_behaviour(PedalButton.B_PRESS, actions.increase_bpm_behaviour)
    pedal.add_bpm_behaviour(PedalButton.C_RELEASE, actions.show_enter_bpm_behaviour)

    stop_event = multiprocessing.Event()
    clock_watcher = multiprocessing.Process(
        target=clock.run,
        args=(stop_event, midi_connector.new()))
    midi_watcher = multiprocessing.Process(
        target=pedal.listen,
        args=(stop_event, midi_connector.new()))

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
