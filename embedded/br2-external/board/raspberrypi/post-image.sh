#!/bin/sh

BOOT_DIR="$BINARIES_DIR/rpi-firmware"

cat > "$BOOT_DIR/config.txt" <<EOF
disable_overscan=1

force_turbo=1
arm_freq=1000
core_freq=500
sdram_freq=500
over_voltage=6

hdmi_force_hotplug=1
EOF
