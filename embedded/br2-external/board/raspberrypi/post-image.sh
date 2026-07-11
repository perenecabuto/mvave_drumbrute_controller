#!/bin/bash

set -e

BOOT_DIR="$BINARIES_DIR/rpi-firmware"

cat > "$BOOT_DIR/config.txt" <<EOF
start_file=start.elf
fixup_file=fixup.dat

kernel=zImage
disable_overscan=1

force_turbo=1
arm_freq=1000
core_freq=500
sdram_freq=500
over_voltage=6

hdmi_force_hotplug=1
dtparam=spi=on
dtoverlay=piscreen,speed=32000000
EOF


BOARD_DIR="$BINARIES_DIR/../../board/raspberrypi"
CMD_LINE="$(cat ${BOARD_DIR}/cmdline.txt | grep 'root=')"
CMD_LINE="${CMD_LINE} fbcon=map:10 fbcon=font:VGA8x8 vt.global_cursor_default=0 loglevel=0"
echo "$CMD_LINE" > "$BOOT_DIR/cmdline.txt"

GENIMAGE_CFG="${BUILD_DIR}/genimage.cfg"
GENIMAGE_TMP="${BUILD_DIR}/genimage.tmp"

# generate genimage from template if a board specific variant doesn't exists
FILES=()
for i in "${BINARIES_DIR}"/*.dtb "${BINARIES_DIR}"/rpi-firmware/*; do
    if [ -n "${i}" ]; then
        FILES+=( "${i#${BINARIES_DIR}/}" )
    fi
done

KERNEL=$(sed -n 's/^kernel=//p' "${BINARIES_DIR}/rpi-firmware/config.txt")
if [ -z "${KERNEL}" ]; then
    echo "Error: kernel not found in ${BINARIES_DIR}/rpi-firmware/config.txt"
    exit 1
fi
FILES+=( "${KERNEL}" )

BOOT_FILES=$(printf '\\t\\t\\t"%s",\\n' "${FILES[@]}")
sed \
    -e "s|#BOOT_FILES#|${BOOT_FILES}|" \
    -e "s|size = .*|size = ${BOOT_SIZE:-128M}|" \
    "${BOARD_DIR}/genimage.cfg.in" \
    > "${GENIMAGE_CFG}"

# Pass an empty rootpath. genimage makes a full copy of the given rootpath to
# ${GENIMAGE_TMP}/root so passing TARGET_DIR would be a waste of time and disk
# space. We don't rely on genimage to build the rootfs image, just to insert a
# pre-built one in the disk image.

trap 'rm -rf "${ROOTPATH_TMP}"' EXIT
ROOTPATH_TMP="$(mktemp -d)"

rm -rf "${GENIMAGE_TMP}"

genimage \
	--rootpath "${ROOTPATH_TMP}"   \
	--tmppath "${GENIMAGE_TMP}"    \
	--inputpath "${BINARIES_DIR}"  \
	--outputpath "${BINARIES_DIR}" \
	--config "${GENIMAGE_CFG}"

exit $?
