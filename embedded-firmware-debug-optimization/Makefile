# usage: make arm V=v1_buggy OPT=-O0        make host V=v2_fixed
V    ?= v2_fixed
OPT  ?= -O2
OUT  ?= build
CROSS = arm-none-eabi-
ARMF  = -mcpu=cortex-m3 -mthumb -ffunction-sections -fdata-sections -Wall -Wextra -g
SRC   = $(wildcard $(V)/*.c)
INC   = -I$(V) -Icommon
.PHONY: arm run stm32
arm:
	@mkdir -p $(OUT)
	$(CROSS)gcc $(ARMF) $(OPT) $(INC) $(SRC) common/startup.c common/hal_qemu.c \
	  -T common/lm3s.ld -nostartfiles --specs=nano.specs --specs=nosys.specs \
	  -Wl,--gc-sections -Wl,-Map=$(OUT)/$(V)$(OPT).map -o $(OUT)/$(V)$(OPT).elf -lm
	$(CROSS)size $(OUT)/$(V)$(OPT).elf
run:
	timeout 20 qemu-system-arm -M lm3s6965evb -nographic -semihosting -kernel $(OUT)/$(V)$(OPT).elf
# Real-hardware port (STM32F103C8, Cortex-M3): make stm32 V=v3_optimized OPT=-O2  -> build/stm32_<V><OPT>.{elf,bin}
stm32:
	@mkdir -p $(OUT)
	$(CROSS)gcc $(ARMF) $(OPT) $(INC) $(filter-out %/main.c,$(SRC)) $(V)/main.c common/startup.c ports/stm32f103/hal_stm32f103.c \
	  -T ports/stm32f103/stm32f103.ld -nostartfiles --specs=nano.specs --specs=nosys.specs -Wl,--gc-sections -o $(OUT)/stm32_$(V)$(OPT).elf -lm
	$(CROSS)objcopy -O binary $(OUT)/stm32_$(V)$(OPT).elf $(OUT)/stm32_$(V)$(OPT).bin
	$(CROSS)size $(OUT)/stm32_$(V)$(OPT).elf
