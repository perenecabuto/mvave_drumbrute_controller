
import rtmidi


class MidiInOutConnector:
    def __init__(self, input_port: int = None, output_port: int = None):
        self._input_port = input_port
        self._output_port = output_port
        self._midi_in = None
        self._midi_out = None

    @property
    def midi_in(self) -> rtmidi.MidiIn:
        if not self._midi_in:
            self._midi_in = rtmidi.MidiIn()
        return self._midi_in

    @property
    def midi_out(self) -> rtmidi.MidiOut:
        if not self._midi_out:
            self._midi_out = rtmidi.MidiOut()
        return self._midi_out

    def query_input_port(self, query: str = None):
        return self._query_port(self.get_input_ports(), query)

    def query_output_port(self, query: str = None):
        return self._query_port(self.get_output_ports(), query)

    def open_ports(self):
        if self._input_port is None or self._output_port is None:
            raise ValueError("Input and output ports must be set before opening ports")

        if self.midi_in.is_port_open():
            self.midi_in.close_port()
        self.midi_in.open_port(self._input_port)
        if self.midi_out.is_port_open():
            self.midi_out.close_port()
        self.midi_out.open_port(self._output_port)

    def get_input_ports(self) -> list[str]:
        return self.midi_in.get_ports()

    def get_output_ports(self) -> list[str]:
        return self.midi_out.get_ports()

    def get_input_message(self):
        return self.midi_in.get_message()

    def send_message(self, message: list[int]):
        self.midi_out.send_message(message)

    def set_ports(self, input_port: int, output_port: int):
        self._input_port = input_port
        self._output_port = output_port

    def _query_port(self, available_ports: list[str], query: str = None) -> int | None:
        if query is None:
            return None
        return next((
            i for i, port_name in enumerate(available_ports)
            if query.lower() in port_name.lower()), None)

    def new(self):
        return MidiInOutConnector(self._input_port, self._output_port)
