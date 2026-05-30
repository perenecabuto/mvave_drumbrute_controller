include $(sort $(wildcard $(BR2_EXTERNAL_MVAVE_PATH)/package/*/*.mk))


LINUX_POST_CONFIGURE_HOOKS += FORCE_MIDI_BUILTIN

define FORCE_MIDI_BUILTIN

	$(LINUX_DIR)/scripts/config \
	--file $(LINUX_DIR)/.config \
	--enable SOUND \
	--enable SND \
	--enable SND_TIMER \
	--enable SND_PCM \
	--enable SND_RAWMIDI \
	--enable SND_SEQ \
	--enable SND_SEQUENCER \
	--enable SND_USB_AUDIO \
	--enable CONFIG_PREEMPT \
	--enable CONFIG_CPU_FREQ \
	--enable CONFIG_CPU_FREQ_DEFAULT_GOV_PERFORMANCE \
	--enable CONFIG_CPU_FREQ_GOV_PERFORMANCE

endef
