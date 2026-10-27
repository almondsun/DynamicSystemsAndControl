# Migración externa a NUCLEO-L432KC

Revisión documental y firmware de evaluación, no aprobación de conexión a potencia. NUCLEO-L432KC ya propiedad del usuario; permanece externa, **no se incluye para ensamblaje JLCPCB**. Referencia oficial: [UM1956 rev.6, tabla16 p.30, §§7.4/7.8–7.10](https://www.st.com/resource/en/user_manual/dm00231744.pdf). Las descargas directas ST terminaron en timeout; el manual y la ficha se consultaron con el navegador de documentación. No se presentan PDFs ST locales inexistentes.

## Cable J3,10 posiciones

Se conserva referencia/UUID y se usa símbolo adaptado `Buck_Redesign:J3_NUCLEO_L432KC`. Footprint provisional con polarización: `Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical`, copia local; MPN final y cableado mecánico pendientes. Numeración física según pad1 del IDC; no interpretar las dos columnas del símbolo como filas físicas del cable.

|J3 Buck|Red / dirección respecto al Buck|NUCLEO conector.pin|Pin placa / MCU|
|---|---|---|---|
|1|UART_TX, reserva del arnés; solo conector en PCB|CN3.1|D1 / PA9, USART1_TX|
|2|GND común|CN3.4 oCN4.2|GND|
|3|MCU_PWM, entrada|CN3.12|D9 / PA8, TIM1_CH1 AF1|
|4|RUN, entrada|CN3.6|D3 / PB0 GPIO|
|5|RESET, entrada al latch del Buck|CN3.9|D6 / PB1 GPIO|
|6|NFAULT_MCU, salida colector abierto|CN3.7|D4 / PB7 GPIO/EXTI7|
|7|VSENSE, entrada ADC|CN4.12|A0 / PA0, ADC1_IN5|
|8|GND común|CN3.4 oCN4.2|GND|
|9|NUC_3V3, alimentación solo para R13|CN4.14|+3V3 **salida** de NUCLEO|
|10|UART_RX, reserva del arnés; solo conector en PCB|CN3.2|D0 / PA10, USART1_RX AF7|

RESET del latch es PB1; **no es NRST** de la NUCLEO. USART1D1/D0 requiere adaptador externo3.3V cruzado TX↔RX, sin alimentar desde el adaptador. Las dos reservas UART no tienen otro terminal local: ERC conserva dos avisos `isolated_pin_label`, intencionales y sin exclusiones. El arnés puede derivarlas al adaptador; no implican circuitos UART añadidos al Buck.

## Puentes y alimentación

- **SB17 abierto**: PA0 reservado al ADC, sin MCO de ST-LINK. Reloj del prototipo usaHSI16, no PA0/CK_IN.
- **SB18 abierto** para PB7/D4 independiente; si cerrado comparte PA5/A4 y exige estado compatible. **SB16** compartePB6/D5 conPA6/A5; no se usan, mantenerlos sin conducir. Comprobar revisión MB1180/continuidad real, no se conoce el estado físico de la placa del usuario.
- USART1D1/D0 no es VCP ST-LINK: el VCP de esta placa usaPA2/PA15 medianteSB2/SB3. No se cambiaron puentes físicos.
- Configuración adoptada: NUCLEO porUSB, Buck por su fuente, GND común. **J3 ya no conecta5V niVIN** de la NUCLEO; su anterior pin1+5V esUART_TX. `+3V3` se renombra `NUC_3V3`, conservando R13 como única carga local (~0.33mA con10k y colector bajo). No hay otra fuente3.3V conectada.
- UM1956 permite5V externo4.75–5.25V con secuencia específica antes deUSB y condicionesSB1/SB9; alimentar por3V3 exigeSB14/SB9 abiertos y pierde alimentaciónST-LINK. Esas variantes **no se adoptan**. No conectar12–13.2V aVIN por analogía: el rango del manual es7–12V. No unir salidas de reguladores.

La revisión elimina el paralelo de fuentes5V, pero ADC/PWM/RUN/RESET siguen requiriendo evaluación de apagado y corrientes por señales. Ver [protección ADC](adc_protection_review.md). USB conectado no significa fuente presente permanentemente ni secuencia garantizada. La NUCLEO no entrega corriente de compuerta: PA8 alimenta lógica HCT14; IR2110 suministra/absorbe esa corriente de Q1.

## Firmware separado

[firmware_l432kc/](firmware_l432kc/) contiene fuente, linker y copia de dependencias oficiales ST CubeL4 **1.18.1**, con hashes en `dependencies.json`. GCCARM12.3.1 compiló y enlazó Cortex-M4F/hard-float. No se cambió `project/firmware/` ni `project/hardware/`; PI/runtime se copiaron, adaptando la ruta del header y nueva escala. No hay compatibilidad binaria/registros conF103. Las cabeceras específicasSTM32L432xx y startup oficial reemplazan los offsets/vectorF103.

**Imagen de revisión RUN bloqueado OFF por `BUCK_BOARD_REVIEWED=0`.** No se programó hardware. Desbloquear ese define exige cerrar protección, bootstrap, alimentación y revisión de banco; no es una instrucción para energizar el Buck ahora. UART `i` informa estado/conteos y `s` apaga. `r` y5/6/7 no habilitan nada en este build. No hay reinicio automático tras falla.

|Área|Implementación/plan verificable|Pendiente real|
|---|---|---|
|Reloj/PLL|HSI16MHz /M1 ×N10 /R2 →80MHz; rangoVOS1,FLASH4WS, AHB/APB÷1. LSI paraIWDG.|Medir frecuencia/deriva; HSI no es cristal calibrado por esta tarea.|
|PWM|TIM1_CH1 PA8AF1,PSC0,ARR7999 →10kHz; CCR1=8000 representa d′=1/alto continuo; preload habilitado.|Osciloscopio frecuencia, polaridad, estados de reset y latencia.|
|Polaridad|PWM1 alto=d′; HCT14 invierte; d=1−d′. RUN bajo es estado de seguridad.|Verificar habilitación/latch/driver reales; MCU no conmuta Q1 directamente.|
|ADC|PA0ASCR, ADC1_IN5,12bits,single-ended; calibración antes del arranque; clock80/4=20MHz;247.5ciclos.|CalibraciónVREF/divisor y protección, ruido/impedancia/cable.|
|Sincronización|TIM1_CH4 interno PWM2,CCR4=4000; TRGO2=OC4REF; flanco ascendente a50µs dispara ADCregular. Se evita TIM1_CC4 directo, que enL432 es opción de ADCinyectado, no regular.|Medir trigger/conversión~13µs+latencia; cambio respecto20 muestras/promedioF103.|
|DMA|DMA1Channel1,request0,halfwords,circular2; callbacksHT/TC procesan una muestra por100µs.|Confirmar mapeo/flags/frescura en silicio, ninguna pérdida/overrun.|
|Control|PI nominal copiado; cálculo en callbackDMA y CCRpreload al siguiente wrap; sinUARTenISR; DWTmáximo y corte>2000ciclos (~25µs).|La nueva fase no reproduce el promedioF103: validar/retunar si corresponde antes de habilitar. No afirmar ganancias validadas.|
|GPIO|PB0RUNbajo,PB1RESETbajo antes de modooutput;PB7entrada sinpull interno (R13 externo),EXTIflanco descendente dispara corte.|Resetfrío/brownout, polaridadNFAULT, SB18 y lógica conBuck apagado. PB7 no está cableado aBKIN.|
|UART|USART1PA9/PA10 AF7,1152008N1, diagnóstico fueraISR; sinstdio/heap.|Adaptador3.3V y protección/apagado. ST-LINKVCP no transporta esteUSART1.|
|Watchdog/fallas|IWDGprescaler32/reload31 (~32ms aLSI32k), refresco solo conDMAfresco; errorADC/EXTI/plazoexcedidoRUNbajo, deja de alimentarwatchdog. TIM1update detecta ausencia o exceso deframes.|Medir LSI/tiempo real; watchdog no reemplaza protección hardware y reset no descarga energía L/C.|
|Escala|3.3×17.2/2.2/4095 V/conteo; offset0 nominal. Saturación/medición>8.3V falla; protección física persiste independiente.|Dos puntosDMM/conteos, VREFreal y nueva función si se añade clamp/buffer.|

Una muestra de fase fija por periodo, no20 conversiones/promedio, es una diferencia deliberada del prototipo. No pretende equivalencia dinámica con la implementaciónF103. Se debe decidir si usar promedio/oversampling o ajustar fase tras observar rizado, conservando la tasa PI10kHz o recalculando ganancias si se cambia.

### Compilación y comprobación

`python firmware_l432kc/build.py` desde cualquier carpeta; admite `ARM_GCC_BIN`. DependenciasST copiadas localmente. Salidas en `artifacts/buck_nucleo_update_20261025/firmware_build/`: ELF,HEX,BIN,MAP yregistro de comandos. El script **no flashea**. En esta sesión se ejecutó con el Python incluido en Codex y el toolchainPlatformIO instalado.

Resultado: text13888B,data16B,bss6628B; linker usaFLASH256KiB/SRAM1 48KiB, reserva≥4KiBstack; SRAM216KiB no utilizada. `readelf` confirma ARMv7E-M/Thumb2/VFPv4/hard-float. Compilación de fuentes propias con `-Wall -Wextra -Werror`; HAL con advertencias activadas. Una primera vinculación falló por `_init` ausente; se añadió inicializaciónCRT bare-metal explícita y se retiróstdio innecesario. La compilación final terminó sin stderr. Esto no prueba temporización, DMA real ni estabilidad PI.

Validación de banco por etapas: fuente Buck desconectada → revisarSB/USB/3.3V yUART → medirPA8/RUN/RESET yfault → ADC con fuente limitada protegida y calibración → DMA/ISR/latencias/IWDG → interlocks condriver desconectado → solo después autorizar ensayo de potencia. No se ejecutaron esos pasos físicos.
