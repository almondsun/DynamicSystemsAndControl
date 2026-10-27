# Firmware L432KC de revisión

Ver [migración](../nucleo_l432kc_migration.md). Compilar con `python build.py`; opcional `ARM_GCC_BIN`. Salidas bajo artifacts; nunca flashea. RUN bloqueado en apagado. Las dependenciasST se conservan con cabeceras y hashes en dependencies.json; el paquete local no incluyó archivosLICENSE independientes, revisar licencia antes de redistribuir. Firmware originalF103 intacto.

## Rev B (2026-10-27)

- `calibration.h`: escala ADC de la placa Rev B. El divisor 15k/2.2k ahora carga R20 (1k), RON de TMUX1511 (2 Ω típ.) y R21 (100k) en el pin ADC: ganancia 0.124277, **6.4844 mV de VOUT por cuenta** (Rev A: 6.3004). Sigue siendo nominal: calibrar con dos pares DMM/cuentas.
- `runtime.c`: en modo cerrado, VOUT < 50 % de la referencia durante más de 20 ticks (2 ms) es falla. Evita que el PI se sature mientras VIN está bajo el UVLO del IR2110 o la interfaz está deshabilitada y rearranque al 95 %.
- Hardware Rev B: tras cada encendido del Buck o caída de NUC_3V3 el latch queda en FALLA (D5); `fault_active()`/EXTI en PB7 lo ven y hace falta un pulso RESET explícito ('r', solo en una compilación revisada).
- `BUCK_BOARD_REVIEWED` sigue en 0.

Prueba de host (sin HAL), desde esta carpeta:

```sh
gcc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -g runtime.c buck_control.c test_runtime_host.c -lm -o /tmp/test_runtime_host && /tmp/test_runtime_host
```

La imagen ARM de Rev B no se compiló en esta sesión: el equipo no tiene `arm-none-eabi-gcc`. Ejecutar `python build.py` antes de programar.
