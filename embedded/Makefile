BUILDROOT_VERSION ?= 2026.05
BUILDROOT_TGZ := buildroot-$(BUILDROOT_VERSION).tar.gz

APP_ROOT := $(shell basename $(PWD))/src

BUILDROOT_DIR := buildroot-$(BUILDROOT_VERSION)
BUILDROOT_CMD := cd $(BUILDROOT_DIR) && BR2_EXTERNAL=../br2-external
BUILDROOT_IMAGE := $(BUILDROOT_DIR)/output/images/sdcard.img
BOOT_SIZE ?= 128M

copy-source:
	cd ..; \
	rm -rf $(APP_ROOT); \
	mkdir -p $(APP_ROOT); \
	uv export --no-dev --prune python-rtmidi > $(APP_ROOT)/requirements.txt; \
	cp -r src/* $(APP_ROOT)

get-buildroot:
	wget -c https://buildroot.org/downloads/$(BUILDROOT_TGZ)
	tar zxf $(BUILDROOT_TGZ)
	#rm $(BUILDROOT_TGZ)

#	--enable BR2_TARGET_ROOTFS_TAR \
#	--enable BR2_TARGET_ROOTFS_EXT2_XZ \

setup: copy-source get-buildroot
	$(BUILDROOT_CMD) make --version
	$(BUILDROOT_CMD) make raspberrypi_defconfig

	$(BUILDROOT_CMD) ./utils/config \
	--enable BR2_PACKAGE_MVAVE_DRUMBRUTE_CONTROLLER \
	--enable BR2_PACKAGE_PYTHON3_PYC_ONLY \
	--enable BR2_STRIP_strip \
	--disable BR2_HAVE_DOCUMENTATION \
	--enable BR2_ROOTFS_DEVICE_CREATION_DYNAMIC_DEVTMPFS \
	--enable BR2_PACKAGE_KMOD \
	\
	--enable BR2_PACKAGE_RPI_FIRMWARE \
	--enable BR2_PACKAGE_RPI_FIRMWARE_INSTALL_DTBS \
	--enable BR2_PACKAGE_RPI_FIRMWARE_INSTALL_DTB_OVERLAYS \
	--enable BR2_PACKAGE_FB_TEST_APP \
	--enable BR2_PACKAGE_SPI_TOOLS \
	\
	--set-str BR2_ROOTFS_POST_IMAGE_SCRIPT \
	"../br2-external/board/raspberrypi/post-image.sh"

	$(BUILDROOT_CMD) make olddefconfig

	$(BUILDROOT_CMD) ./utils/config \
	--enable BR2_LINUX_KERNEL_CONFIG_FRAGMENT_FILES \
	--set-str BR2_LINUX_KERNEL_CONFIG_FRAGMENT_FILES "../br2-external/board/raspberrypi/linux-lcd.fragment"


build: setup
	$(BUILDROOT_CMD) make mvave-drumbrute-controller-dirclean
	$(BUILDROOT_CMD) BOOT_SIZE=$(BOOT_SIZE) make



flash: SHELL := /bin/bash
flash:
	@echo ""
	@echo "Available devices:"
	@echo ""; \
	ROOT_DEV=$$(lsblk -dpno NAME | xargs -I{} sh -c 'grep -o "{}.* / " /proc/mounts >/dev/null && echo -n {}'); \
	lsblk -dpno NAME,SIZE,MODEL | grep -v $$ROOT_DEV | nl -w2 -s") "; \
	echo ""; \
	read -p "Select device number: " choice; \
	DEV=$$(lsblk -dpno NAME | grep -v $$ROOT_DEV | sed -n "$${choice}p"); \
	\
	if [ -z "$$DEV" ]; then \
		echo "Invalid selection"; \
		exit 1; \
	fi; \
	\
	echo ""; \
	echo "Selected: $$DEV"; \
	lsblk $$DEV; \
	echo ""; \
	read -p "FLASH $$DEV ? ALL DATA WILL BE LOST [yes/NO]: " confirm; \
	\
	if [ "$$confirm" != "yes" ]; then \
		echo "Cancelled"; \
		exit 1; \
	fi; \
	\
	echo "Unmounting partitions..."; \
	for p in $$(lsblk -ln -o NAME $$DEV | tail -n +2); do \
		sudo umount /dev/$$p 2>/dev/null || true; \
	done; \
	\
	echo "Writing image..."; \
	sudo dd \
		if=$(BUILDROOT_IMAGE) \
		of=$$DEV \
		bs=4M \
		status=progress \
		conv=fsync; \
	\
	sync; \
	echo ""; \
	echo "Flash complete!"
