# PlatformIO extra script: build and link for the Cortex-M4F hardware FPU.
# The nucleo_l432kc board defaults to soft-float; flags must reach the compiler,
# the assembler and the linker (multilib selection), so they cannot live in build_flags.
Import("env")  # noqa: F821  (SCons global)

FPU_FLAGS = ["-mfloat-abi=hard", "-mfpu=fpv4-sp-d16"]
env.Append(CCFLAGS=FPU_FLAGS, ASFLAGS=FPU_FLAGS, LINKFLAGS=FPU_FLAGS)  # noqa: F821
