# STM32F103C8: adaptador de control Buck

Implementación para Blue Pill externa con cristal HSE de 8 MHz. **Compilada
y probada en computador; programación y temporización física pendientes.**
El núcleo `project/hardware/buck_control.c/.h` mantiene su interfaz y ganancias.

## Compilar y programar

Desde la raíz del repositorio, con GCC ARM instalado:

```sh
make -C project/firmware CROSS=arm-none-eabi- all test
```

En este entorno, `make -C project/firmware all test` encuentra el compilador
local de `artifacts/buck-tools/cad-root/usr`. Los resultados se escriben en
`artifacts/buck-pcb-validation/firmware/`: ELF para depurar, BIN/HEX para
programar, MAP y ejecutables de pruebas. Se reservan al menos 4 KB de stack
mediante una aserción del linker; no se utiliza heap.

BOOT0 debe estar bajo. Conectar ST-LINK por SWD según el pinout real del
programador, inicialmente con la tarjeta de potencia desconectada. Ejemplo
para OpenOCD instalado en el equipo de laboratorio:

```sh
openocd -f interface/stlink.cfg -f target/stm32f1x.cfg \
  -c 'program artifacts/buck-pcb-validation/firmware/buck.elf verify reset exit'
```

Este comando **no se ejecutó contra hardware** aquí. Leer/verificar flash y
reloj en banco; no asumir 128 KB porque algunas placas económicas lo anuncien.
La compilación limita explícitamente flash a 64 KB y RAM a 20 KB.

## UART y operación

115200 baud, 8N1, PA9 TX / PA10 RX, lógica 3.3 V, GND común, sin unir el pin
de alimentación del adaptador. La USB-C de la placa comprada puede proporcionar
solo alimentación; no se utiliza como puerto de datos. Ver cable J3 en
`../pcb/docs/assembly-and-tests.md`.

| Comando de un carácter | Acción |
|---|---|
| `s` | Apagar inmediatamente por RUN y reiniciar estado PI |
| `r` | Apagar y solicitar borrado del latch; rechazar si persiste causa |
| `a`, `b`, `c` | Lazo abierto d′ = 0.5, 0.6, 0.4 |
| `5`, `6`, `7` | PI con referencia de 5, 6, 7 V |
| `v` | Capturar 512 medias consecutivas de periodo, 51.2 ms |
| `d` | Apagar y enviar captura completa; rechazar descarga mientras captura |
| `i` | `STATE,modo,falla,device_id,flash_KB,max_irq_cycles,adc_medio` |
| `?` | Ayuda |

Modos: 0 apagado, 1 rampa, 2 abierto, 3 PI, 4 falla. Iniciar desde apagado
produce una rampa de duty de 0.0001 por periodo. Cambiar `a/b/c` estando en
abierto, o `5/6/7` estando en PI, aplica el escalón solicitado. Para cambiar
entre abierto y PI se debe apagar. La rampa PI termina cerca de la referencia
y ajusta el integrador para continuidad; una realimentación que no alcanza
el objetivo en 1.2 s genera falla. No hay reinicio automático después de falla.

## Temporización implementada

HSE 8 MHz → PLL ×9 → CPU y temporizadores 72 MHz. APB1 = 36 MHz, APB2 =
72 MHz, ADC = 12 MHz. TIM1_CH1/PA8: ARR=7199, PSC=0, PWM 10 kHz,
CCR1 precargado. `dprime=1` se representa con CCR1=7200, no 7199.

TIM1 TRGO en modo enable arranca TIM3 mediante ITR0 y modo esclavo trigger.
TIM3 ARR=359, PSC=0 y CNT inicial=324: primer trigger a 0.5 µs, siguientes
cada 5 µs. ADC1 canal 0 usa 13.5 ciclos de adquisición + 12.5 de conversión:
resultado tras 2.167 µs. La muestra 20 termina alrededor de 97.667 µs.
DMA1 canal 1 circular almacena dos mitades de 20 muestras. No hay ISR de DMA.

En cada actualización TIM1, se verifica exactamente el flag DMA esperado,
se promedian las 20 muestras del periodo anterior y se ejecuta el controlador.
El CCR escrito se aplica en **la siguiente** actualización TIM1: hay un periodo
completo entre el cierre de la ventana ADC y la aplicación del comando.
No se registra por UART durante este cálculo. La duración se mide con DWT;
6000 ciclos es el límite de software, inferior a los 7200 disponibles.
Confirmar con osciloscopio latencia, frecuencia y fase reales; los valores de
registro no prueban comportamiento temporal del silicio.

La captura marca el tiempo del final de cada ventana ADC; d′ corresponde al
comando aplicado en esa ventana, no al nuevo comando en cola. La referencia
es la vigente cuando se procesa la ventana. Los flags permiten descartar
apagado, rampa y falla. Un apagado hardware dentro de la ventana invalida
la interpretación de su duty normal.

## Calibración y capturas

Los coeficientes de `calibration.h` son nominales. Con RUN bajo y el montaje
de calibración aprobado, aplicar dos tensiones conocidas a VOUT, registrar
el conteo ADC mediante `i` y la lectura del DMM. Usar:

`ganancia = (V2−V1)/(N2−N1)`; `offset = V1−ganancia*N1`.

Recompilar, verificar y registrar esos pares junto con VDDA, tolerancias y
fecha. Los conteos de 12 bits y la resolución nominal de salida de 3.22 mV
no acreditan exactitud absoluta de 3.22 mV. La captura conserva milivoltios.

Para automatizar referencia/PWM después de aprobar la puesta en marcha:

```sh
python -m pip install 'pyserial>=3.5,<4'
python project/firmware/capture.py --port /dev/ttyUSB0 --case ref_up \
  --load-ohm 6.02 --output project/data/ref_up_repeticion_1.csv
```

Reemplazar el puerto y **6.02 por la resistencia medida**, no copiarla como
medición. El script habilita el convertidor: usarlo solo con la conexión y
los límites de laboratorio verificados. Conserva UART original y exporta
el CSV del curso; no sobrescribe mediciones existentes. El evento se ubica
con las columnas registradas, no solo con el `sleep` del computador. Adjuntar
el JSON experimental requerido por `project/data/README.md`.

Para los cambios de carga manuales usar pretrigger del osciloscopio. La RAM
no almacena las 20 conversiones crudas, sino sus medias: el rizado debe
medirse por separado. Hacer tres repeticiones por escenario.
