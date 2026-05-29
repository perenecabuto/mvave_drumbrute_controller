################################################################################
#
# mvave-drumbrute-controller
#
################################################################################

MVAVE_DRUMBRUTE_CONTROLLER_SITE = \
    $(TOPDIR)/../src

MVAVE_DRUMBRUTE_CONTROLLER_SITE_METHOD = local

MVAVE_DRUMBRUTE_CONTROLLER_DEPENDENCIES = \
    python3 \
    host-python-pip \
    python-rtmidi

define MVAVE_DRUMBRUTE_CONTROLLER_INSTALL_TARGET_CMDS

    mkdir -p \
        $(TARGET_DIR)/opt/mvave-drumbrute-controller

    cp -r $(@D)/* \
        $(TARGET_DIR)/opt/mvave-drumbrute-controller/

    mkdir -p \
        $(TARGET_DIR)/etc/init.d

    cp \
        $(BR2_EXTERNAL_MVAVE_PATH)/package/mvave-drumbrute-controller/S99mvave \
        $(TARGET_DIR)/etc/init.d/S99mvave

    $(HOST_DIR)/bin/pip3 install \
        --no-cache-dir \
        --no-compile \
        --target=$(TARGET_DIR)/usr/lib/python$(PYTHON3_VERSION_MAJOR)/site-packages \
        -r $(@D)/requirements.txt

endef

$(eval $(generic-package))
