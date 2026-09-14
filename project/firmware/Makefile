ROOT := ../..
OUT ?= $(ROOT)/artifacts/buck-pcb-validation/firmware
TOOLROOT := $(abspath $(ROOT)/artifacts/buck-tools/cad-root/usr)
CROSS ?= $(TOOLROOT)/bin/arm-none-eabi-
HOST_CC ?= cc
CC := $(CROSS)gcc
CFLAGS := -std=gnu11 -Os -g3 -Wall -Wextra -Werror -mcpu=cortex-m3 -mthumb -ffunction-sections -fdata-sections -fno-common
SOURCES := stm32f103.c runtime.c ../hardware/buck_control.c
.PHONY: all test clean
all: $(OUT)/buck.bin $(OUT)/buck.hex
$(OUT):
	mkdir -p $@
$(OUT)/buck.elf: $(SOURCES) runtime.h calibration.h stm32f103.ld ../hardware/buck_control.h | $(OUT)
	$(CC) $(CFLAGS) $(SOURCES) -T stm32f103.ld -nostartfiles --specs=nosys.specs -Wl,--gc-sections,-Map=$(OUT)/buck.map -lm -o $@
	$(CROSS)size $@
$(OUT)/buck.bin: $(OUT)/buck.elf
	$(CROSS)objcopy -O binary $< $@
$(OUT)/buck.hex: $(OUT)/buck.elf
	$(CROSS)objcopy -O ihex $< $@
test: | $(OUT)
	$(HOST_CC) -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -g runtime.c ../hardware/buck_control.c test_runtime.c -lm -o $(OUT)/test_runtime
	$(OUT)/test_runtime
	$(HOST_CC) -std=c11 -Wall -Wextra -Werror ../hardware/buck_control.c ../hardware/test_buck_control.c -lm -o $(OUT)/test_control
	$(OUT)/test_control
clean:
	@echo 'Use a fresh OUT directory; build evidence is retained.'
