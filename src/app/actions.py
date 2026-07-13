from functools import cache

from devices import MidiInOutConnector, Drumbrute, MidiClock
from app.data import StateStore
import pyfiglet


@cache
def render(text, font):
    return pyfiglet.figlet_format(text, font=font, width=80)


class BehaviorController():
    # pylint: disable=unused-argument

    def __init__(
        self,
        drumbrute: Drumbrute,
        state_store: StateStore,
        midi_clock: MidiClock,
        max_bpm: int = 300,
    ):
        self.drumbrute = drumbrute
        self.state_store = state_store
        self.midi_clock = midi_clock
        self.max_bpm = max_bpm

        self.change_mode_start = None

    def on_start_behaviour(self, midi_connector: MidiInOutConnector, midi_msg, delta, is_bpm_mode: bool):
        self._change_pattern(midi_connector, self.state_store.pattern)
        self._update_bpm(self.state_store.bpm)
        if self.state_store.playing:
            self.drumbrute.play(midi_connector)
        else:
            self.drumbrute.stop(midi_connector)
        self._print_status(is_bpm_mode=is_bpm_mode)

    def on_change_mode_behaviour(self, midi_connector: MidiInOutConnector, midi_msg, delta, is_bpm_mode: bool):
        self._print_status(is_bpm_mode=is_bpm_mode)

    def on_press_change_mode_button_behaviour(self):
        print("PRESSED CHANGE MODE BUTTON", flush=True)

    def previous_pattern_behaviour(self, midi_connector: MidiInOutConnector, midi_msg, delta, is_bpm_mode: bool):
        self._change_pattern(midi_connector, self.state_store.pattern - 1)
        self._update_bpm(self.state_store.bpm)
        self._print_status(is_bpm_mode=is_bpm_mode)

    def next_pattern_behaviour(self, midi_connector: MidiInOutConnector, midi_msg, delta, is_bpm_mode: bool):
        self._change_pattern(midi_connector, self.state_store.pattern + 1)
        self._update_bpm(self.state_store.bpm)
        self._print_status(is_bpm_mode=is_bpm_mode)

    def toggle_play_behaviour(self, midi_connector: MidiInOutConnector, midi_msg, delta, is_bpm_mode: bool):
        playing = not self.state_store.playing
        if playing:
            self.drumbrute.play(midi_connector)
        else:
            self.drumbrute.stop(midi_connector)
        self.state_store.set_playing(playing)
        self._print_status(is_bpm_mode=is_bpm_mode)

    def increase_bpm_behaviour(self, midi_connector: MidiInOutConnector, midi_msg, delta, is_bpm_mode: bool):
        self._update_bpm(self.state_store.bpm + 1)
        self._print_status(is_bpm_mode=is_bpm_mode)

    def decrease_bpm_behaviour(self, midi_connector: MidiInOutConnector, midi_msg, delta, is_bpm_mode: bool):
        self._update_bpm(self.state_store.bpm - 1)
        self._print_status(is_bpm_mode=is_bpm_mode)

    def show_enter_bpm_mode_behaviour(self, midi_connector: MidiInOutConnector, midi_msg, delta, is_bpm_mode: bool):
        self._print_status(is_bpm_mode=is_bpm_mode)

    def _change_pattern(self, midi_connector: MidiInOutConnector, pattern_num: int):
        pattern_num = max(0, min(pattern_num, self._max_pattern_num() - 1))
        drumbrute_bank = pattern_num // self.drumbrute.max_patterns
        drumbrute_pattern = pattern_num % self.drumbrute.max_patterns

        self.drumbrute.change_bank(midi_connector, drumbrute_bank)
        self.drumbrute.change_pattern(midi_connector, drumbrute_pattern)
        self.state_store.set_pattern(pattern_num)

    def _update_bpm(self, bpm: int):
        bpm = max(0, min(bpm, self.max_bpm))
        self.midi_clock.set_bpm(bpm)
        self.state_store.set_bpm(bpm)

    def _max_pattern_num(self):
        return self.drumbrute.max_patterns * self.drumbrute.max_banks

    def _print_status(
        self,
        is_bpm_mode: bool,
        font: str = "ansi_shadow",
    ):
        bpm_text = f"BPM:{self.state_store.bpm:03d}"
        pattern_text = f"PTRN:{self.state_store.pattern + 1:02d}"
        bank_text = f"BNK:{self.state_store.pattern // self.drumbrute.max_patterns + 1:02d}"
        label = "SET BPM" if is_bpm_mode \
            else "PLAYING" if self.state_store.playing \
            else "STOPPED"
        text = f"{label}\n{bpm_text}\n{pattern_text}\n{bank_text}"
        print("\033[H\033[J\n", end="")
        print(render(text, font), flush=True)
