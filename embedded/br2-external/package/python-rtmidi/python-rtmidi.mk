################################################################################
#
# python-rtmidi
#
################################################################################

PYTHON_RTMIDI_VERSION = 1.5.8
PYTHON_RTMIDI_SOURCE = python_rtmidi-$(PYTHON_RTMIDI_VERSION).tar.gz
PYTHON_RTMIDI_SITE = https://files.pythonhosted.org/packages/source/p/python-rtmidi
#PYTHON_RTMIDI_SETUP_TYPE = pep517
PYTHON_RTMIDI_SETUP_TYPE = setuptools
PYTHON_RTMIDI_DEPENDENCIES = \
	host-python3 \
	host-openssl \
	host-python-pip \
	host-python-meson-python \
	host-pkgconf \
	alsa-lib


define PYTHON_RTMIDI_INSTALL_HOST_PY_DEPS
	$(HOST_DIR)/bin/python3 -m pip install \
		--upgrade \
		ninja \
		cython \
		wheel \
		pyproject-metadata
endef

PYTHON_RTMIDI_PRE_BUILD_HOOKS += \
	PYTHON_RTMIDI_INSTALL_HOST_PY_DEPS

# Create Meson cross file
define PYTHON_RTMIDI_CREATE_CROSS_FILE

	echo "[binaries]" > $(@D)/cross.ini
	echo "c = '$(TARGET_CC)'" >> $(@D)/cross.ini
	echo "cpp = '$(TARGET_CXX)'" >> $(@D)/cross.ini
	echo "ar = '$(TARGET_AR)'" >> $(@D)/cross.ini
	echo "strip = '$(TARGET_STRIP)'" >> $(@D)/cross.ini
	echo "pkg-config = '$(PKG_CONFIG_HOST_BINARY)'" >> $(@D)/cross.ini

	echo "" >> $(@D)/cross.ini
	echo "[host_machine]" >> $(@D)/cross.ini
	echo "system = 'linux'" >> $(@D)/cross.ini
	echo "cpu_family = 'arm'" >> $(@D)/cross.ini
	echo "cpu = 'arm1176jzf-s'" >> $(@D)/cross.ini
	echo "endian = 'little'" >> $(@D)/cross.ini

endef

PYTHON_RTMIDI_PRE_BUILD_HOOKS += \
	PYTHON_RTMIDI_CREATE_CROSS_FILE

# Tell meson-python this is cross compilation
PYTHON_RTMIDI_BUILD_OPTS = \
	-Csetup-args=--cross-file=$(@D)/cross.ini


$(eval $(python-package))
