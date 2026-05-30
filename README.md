# MVave Drumbrute Controller

A Python-based MIDI controller for the Arturia Drumbrute synthesizer with Raspberry Pi embedded support.

## Description

This project provides a Python application to control the Arturia Drumbrute drum machine via MIDI. It runs on Linux systems and can be embedded directly on a Raspberry Pi using a Buildroot-based custom image. The application connects to MIDI input and output devices to manage drum patterns, BPM, and playback control through a SINCO foot pedal or similar MIDI controller.

### Key Features

- **MIDI Control**: Full MIDI in/out support for real-time drum machine control
- **Pattern Management**: Switch between drum patterns seamlessly
- **BPM Control**: Adjust tempo in real-time with MIDI synchronization
- **Persistent State**: Saves the last used pattern and BPM settings
- **Foot Pedal Support**: Control via SINCO pedals or other MIDI input devices
- **Quiet Mode**: Run without interactive prompts for automated setups
- **Embedded Support**: Pre-built Raspberry Pi images for plug-and-play deployment

## Requirements

- Python 3.13 or later
- MIDI hardware devices (input and output)
- Dependencies:
  - `fire>=0.7.1` - CLI framework
  - `python-rtmidi>=1.5.8` - MIDI I/O
  - `simple-term-menu>=1.6.6` - Terminal UI
  - `sqlitedict>=2.1.0` - State persistence

## Installation

### Quick Start

Install dependencies and run:

```bash
make setup
make run
```

### Using Poetry/UV

```bash
uv sync
uv run python src/main.py --help
```

## MIDI Connection

The application manages MIDI connections through an interactive menu or automated port selection.

### How MIDI Connection Works

1. **Port Discovery**: The application detects all available MIDI input and output ports on your system
2. **Port Selection**: When running in interactive mode, you'll see a menu to select:
   - **MIDI Input Port**: Usually your controller/pedal (searches for "SINCO" by default)
   - **MIDI Output Port**: Usually your drum machine (searches for "Arturia" by default)
3. **State Persistence**: Selected ports are saved in a SQLite database (`~/.mvave_drumbrute.db`) for next run
4. **Connection Establishment**: Once ports are selected, the application opens bidirectional MIDI connections

### MIDI Messages

The application communicates with devices using standard MIDI messages:

- **Control Changes (CC)**: Adjust parameters like tempo and mode
- **Program Changes (PC)**: Switch between drum patterns  
- **MIDI Clock**: Synchronizes tempo with connected devices
- **Note Messages**: Trigger drum sounds

### Auto-Selection

Automatically detect and connect to devices by name:

```bash
uv run python src/main.py \
  --auto-select \
  --input-query="SINCO" \
  --output-query="Arturia"
```

## Quiet Mode

The quiet mode bypasses interactive prompts and uses saved settings or auto-selection, ideal for embedded systems and automation.

### Running in Quiet Mode

```bash
make run-quiet
```

Or directly:

```bash
uv run python src/main.py \
  --quiet \
  --db-file-path=$HOME/.mvave_drumbrute.db
```

### How Quiet Mode Works

1. **Skips Interactive Menus**: No terminal prompts for port selection
2. **Uses Saved State**: Loads previously selected MIDI ports from the database
3. **Fallback to Auto-Selection**: If ports aren't saved, automatically searches using `--input-query` and `--output-query`
4. **Direct Startup**: Application starts immediately with MIDI listening active

### Quiet Mode with Custom Ports

```bash
uv run python src/main.py \
  --quiet \
  --input-port=0 \
  --output-port=1
```

## Embedded Raspberry Pi Image

The project includes a complete embedded Buildroot configuration for creating a standalone Raspberry Pi image.

### Building the Image

```bash
make build-image
```

This command:

1. Downloads Buildroot (version 2026.02.2)
2. Copies the Python application source
3. Exports Python dependencies
4. Configures a custom Raspberry Pi distribution
5. Compiles the complete SD card image

### Flashing to SD Card

```bash
make flash-image
```

The flash target:

1. **Detects available devices**: Shows USB drives and SD cards
2. **Prompts for device selection**: Select your SD card number
3. **Confirms before writing**: Prevents accidental data loss
4. **Flashes the image**: Writes the compiled image with progress indication
5. **Syncs and verifies**: Ensures data integrity

### Image Features

- Minimal Raspberry Pi distribution based on Buildroot
- Pre-installed Python 3.13 runtime
- All application dependencies included
- Boot directly into the MVave Drumbrute Controller
- Automatic MIDI port detection on startup
- Persistent storage for configuration

### Embedded Setup

After flashing and booting the Raspberry Pi:

1. Connect MIDI input device (pedal) to Raspberry Pi
2. Connect MIDI output to Drumbrute
3. System auto-starts the controller in quiet mode
4. Settings are saved for subsequent boots

### Build Requirements

For building embedded images on Linux:

- `wget` - Download Buildroot
- `tar` - Extract archives
- Build tools: `gcc`, `make`, `cmake`
- 4GB+ free disk space
- 30+ minutes build time (first build)

## Usage Examples

### Interactive Mode (Default)

Start with menu-based port selection:

```bash
make run
```

### Automated Setup

Connect to devices automatically:

```bash
uv run python src/main.py \
  --auto-select \
  --input-query="SINCO" \
  --output-query="Arturia"
```

### Specific Port Selection

Connect to specific MIDI ports directly:

```bash
uv run python src/main.py \
  --input-port=0 \
  --output-port=1
```

### Debug Logging

Enable detailed logging:

```bash
LOG_LEVEL=DEBUG make run
```

### Custom Database Location

```bash
make run DB_FILE_PATH=/path/to/custom.db
```

## Architecture

The application uses a multi-process design:

- **Main Process**: Orchestrates startup and monitoring
- **MIDI Listener**: Monitors foot pedal input in a subprocess
- **MIDI Clock**: Synchronizes timing in another subprocess
- **State Store**: Persistent configuration in SQLite

## Development

### Project Structure

```
.
├── src/
│   ├── main.py              # Entry point and CLI
│   ├── app/
│   │   ├── mvave_drumbrute.py  # Main app orchestration
│   │   ├── actions.py         # Behavior handlers
│   │   └── data.py            # State persistence
│   └── devices/
│       ├── midi_connector.py   # MIDI I/O abstraction
│       ├── midi_clock.py       # Tempo synchronization
│       ├── drumbrute.py        # Drumbrute-specific control
│       └── mvave_pedal.py      # Pedal event handling
├── embedded/                # Buildroot configuration
│   └── Makefile            # Build and flash commands
└── Makefile                # Development targets
```

### Development Commands

```bash
make setup           # Install dependencies
make run            # Run in interactive mode
make run-quiet      # Run in quiet mode
make build-image    # Build Raspberry Pi image
make flash-image    # Flash image to SD card
```

## Troubleshooting

### MIDI Ports Not Detected

1. Verify devices are connected and powered on
2. Check system MIDI devices: `aconnect -l` (Linux)
3. Run with debug logging: `LOG_LEVEL=DEBUG make run`

### Connection Issues

1. Try specifying ports manually: `--input-port=0 --output-port=1`
2. Check device names match query strings
3. Ensure no other applications are using the MIDI ports

### Embedded Build Issues

1. Ensure sufficient disk space and build time
2. Check internet connection for downloading Buildroot
3. Verify build tools are installed: `gcc`, `make`, `cmake`

## License

See the repository for license information.

## Author

Created for controlling Arturia Drumbrute synthesizer via MIDI-enabled foot pedals.
