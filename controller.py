from midi_connector import MidiInOutConnector


class DrumbruteController():

    PC = 0xC0
    START = 0xFA
    STOP = 0xFC

    def __init__(
        self,
        channel: int = 10,
    ):
        self.channel = channel

        self.max_patterns = 16
        self.change_mode_threshold = 5

        self.change_mode_start = None

    def change_pattern(self, midi_connector: MidiInOutConnector, pattern_num: int) -> int:
        cmd = self.PC + (self.channel - 1)
        pattern_num = max(0, min(pattern_num, self.max_patterns - 1))
        midi_connector.send_message([cmd, 0, pattern_num])
        return pattern_num

    def stop(self, midi_connector: MidiInOutConnector):
        midi_connector.send_message([self.STOP, 255, 255])

    def play(self, midi_connector: MidiInOutConnector):
        midi_connector.send_message([self.START, 255, 255])
