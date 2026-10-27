# Revisión de medición y protección ADC

**Divisor15k/2.2k incorporado para evaluación; protección NO cerrada.** No se añadió limitador, level shifter digital ni diodo a3.3V. Los escenarios20V y24V son puntos de análisis, no límites garantizados de falla. Persisten riesgos de transitorios y secuencia de alimentación.

## Transferencia y tolerancias

R14=15kΩ±1%, UNI-ROYAL0603WAF1502T5E/C22809; R15=2.2kΩ±1%,0603WAF2201T5E/C4190. [Familia fabricante](https://www.royalohm.com/assets/pdf/products/smd/1.pdf), [identidad comercial R15](https://www.lcsc.com/product-detail/C4190.html). Se mantienen huellas0603 no polarizadas. Solo cambiaron valores/MPN, no redes: R14 VOUT–VSENSE, R15 VSENSE–GND, C17 VSENSE–GND y J3.7 VSENSE.

`k=2.2/(15+2.2)=0.127906976744`; `VADC=k×VOUT`. Es una señal lineal de realimentación para PI dentro del rango válido, no una conversión de nivel digital. Esquinas: `kmin=R15min/(R14max+R15min)` y `kmax=R15max/(R14min+R15max)`.

k±1%=[0.125692521, 0.130154639]. La columna85°C añade coeficientes opuestos de±100ppm/°C desde25°C (±0.6% extra multiplicativo), como presupuesto conservador de piezas independientes. No supone seguimiento térmico entre resistores.

| VOUT V | ADC nominal V | ADC min1% V | ADC max1% V | ADC max presupuesto85°C V | Código nominal3.3V /4095 |
| --- | --- | --- | --- | --- | --- |
| 5 | 0.639535 | 0.628463 | 0.650773 | 0.657596 | 793.6 |
| 6 | 0.767442 | 0.754155 | 0.780928 | 0.789116 | 952.3 |
| 7 | 0.895349 | 0.879848 | 0.911082 | 0.920635 | 1111.0 |
| 8.18 | 1.046279 | 1.028165 | 1.064665 | 1.075828 | 1298.3 |
| 12 | 1.534884 | 1.508310 | 1.561856 | 1.578231 | 1904.7 |
| 13.2 | 1.688372 | 1.659141 | 1.718041 | 1.736054 | 2095.1 |
| 20 | 2.558140 | 2.513850 | 2.603093 | 2.630385 | 3174.4 |
| 24 | 3.069767 | 3.016620 | 3.123711 | 3.156462 | 3809.3 |

## Límites STM32L432KC y alimentación

PA0 es **ADC1_IN5**, estructuraFT_a. ADC12_IN5 en UM1956 es nomenclatura de familia; este MCU solo implementa ADC1. Conversión válida0…VREF+. DS11451 rev.4 tablas18/19 separan máximos absolutos de conversión y fijan inyección positiva permitida0mA para estas entradas; no se usa “±5mA” como permiso de inyección positiva. PA0 tolerante en modo digital no significa que el ADC activo admita5V. [Ficha STM32L432KC](https://www.st.com/resource/en/datasheet/stm32l432kc.pdf).

AN4899 rev.4 §5.2 aclara que, con la función analógica activada, el límite operativo es `min(VDDA,VREF+)+0.3V`; eso es un límite de entrada, **no rango de conversión**, ni permiso para usar el diodo interno como protección. [AN4899](https://www.st.com/resource/en/application_note/dm00315319-stm32-gpio-configuration-for-hardware-settings-and-lowpower-consumption-stmicroelectronics.pdf). Distinguir GPIO MODER del interruptor analógico ASCR. No copiar los límites del STM32F103 anterior.

| VREF+ supuesto V | VOUT a escala completa nominal V | VOUT a escala completa conkmax V | Código teórico24V/kmax |
| --- | --- | --- | --- |
| 3.0 | 23.455 | 23.050 | 4263.9 |
| 3.135 | 24.510 | 24.087 | 4080.3 |
| 3.3 | 25.800 | 25.354 | 3876.2 |
| 3.465 | 27.090 | 26.622 | 3691.7 |

A3.3V,24V produce como máximo3.123711V con tolerancia inicial: margen≈176mV para conversión, antes de ruido/desplazamiento GND. A3.135V queda≈11mV; con el presupuesto térmico desaparece. A3.0V,24V **satura** aunque no necesariamente exceda un máximo absoluto. Durante rampa/brownout,1.8V de referencia ya no permite medir20V. Firmware debe rechazar datos fuera de rango y deshabilitar RUN, no interpretar saturación como VOUT menor.

### NUCLEO apagada

VDD/VDDA=0 y Buck energizado no son una condición de adquisición válida. El FT_a con interruptor analógico abierto puede tolerar tensión bajo sus condiciones digitales; no se afirma que siempre exista un clamp aVDD+0.3V. Tampoco se depende de ese estado durante caída lenta de alimentación, ADC previamente activo, software fallando o múltiples dominios apagándose. La transición, las fugas y la realimentación de rails requieren garantía o aislamiento.

Para exponer el riesgo, modelo CONTRAEJEMPLO con un clamp conductor a0.3V (no es caracterización del silicio): `I=(k×VOUT−0.3)/Rth`. A20V≈1.177mA; a24V≈1.444mA. Si se agregara un Schottky hacia3.3V, esa corriente entraría al rail apagado; el regulador de la NUCLEO no se ha acreditado como sumidero. En funcionamiento a3.135V y señal3.124V no conduce ese clamp; un transitorio mayor sí podría hacerlo. Eliminar la conexión5V de J3 evita unir fuentes, pero **no elimina las rutas por señales**.

La entrada PWM también requiere revisión: con MCU apagado y su salida alta impedancia, R3=10k a5V y R4=1k llevan el pin hacia5V, no lo reducen a3.3V sin carga. Si apareciera un clamp0.3V, corriente≈(5−.3)/11k=0.427mA,≈0.455mA con5.25V/−1%; sin clamp el nivel puede exceder el límite FT apagado. No se declara seguro por ser baja corriente. En sentido contrario, NUCLEO encendida/Buck apagado puede alimentar HCT por sus entradas; mantener RUN bajo no sustituye protección de todos los pines. No está autorizado conectar ambas etapas en cualquier secuencia hasta cerrar este punto.

## Alternativas concretas, aún no incorporadas

|Opción|Qué resuelve|Qué falta / decisión|
|---|---|---|
|Solo divisor15k/2.2k +C17|Escala5–7V adecuadamente y mejora margen respecto3k/1k|No limita fallas sin cota, tensión negativa, ni transición apagado. Implementado solo como candidato.|
|Añadir1k serie +BAT54S hacia GND/rail|Limita corriente y puede desviar pulsos|No hace cero la inyección positiva; el rail3.3V debe absorber corriente y no realimentarse. Fuga y VF dependen de T/I. NO seleccionado. [Nexperia](https://assets.nexperia.com/documents/data-sheet/BAT54S.pdf)|
|BZT52C3V3 aGND o TVS genérico|Puede descargar energía de algunos transitorios|El valor3.3V no garantiza clamp por debajo del límite ADC, especialmente a corrientes sub-mA o en pulsos. Hace falta curva I/V, fuga y energía; no es aprobación.|
|1k serie +shunt LM4040-N2.5V aGND +aislamiento TMUX1511|Shunt independiente de rail3.3; switch con protección apagado puede separar ADC del sensor|Arquitectura preferida para estudiar, NO poblada. LM4040 recortaría mediciones altas (~19.5V nominal); hay que justificar corriente mínima, dinámica/fuga, tolerancia, energía y errores. SEL debe depender de power-good con estado bajo por defecto. No confiar solo en firmware.|
|ADG5412F/5413F como front-end protegido|Protección de fallas y apagado especificada hasta±55V dentro de sus condiciones|Requiere≥8V de alimentación simple; no es sustituto3.3V ni limita por sí mismo la salida a rango ADC. Requiere divisor/aislamiento y presupuesto de errores adicionales. Menos simple para este montaje. [Analog Devices](https://www.analog.com/media/en/technical-documentation/data-sheets/ADG5412F_5413F.pdf)|

[TMUX1511 TI](https://www.ti.com/lit/ds/symlink/tmux1511.pdf) admite señal de0–3.6V con VDD<1.5V y tiene fuga apagado especificada hasta±2µA en su tabla correspondiente. Eso **no** garantiza ADC seguro ante un VOUT sin límite: conkmax inicial,3.6V corresponde≈27.66V; a temperatura el techo se reduce. Además, el switch conduce señales por encima de su alimentación, por lo que NO es un clamp de sobretensión encendido. [LM4040-N](https://www.ti.com/lit/ds/symlink/lm4040-n.pdf) requiere escoger grado/encapsulado/corriente y validar el circuito completo; no se asignó MPN ni footprint definitivo nuevo.

Un pull-down100k en el lado MCU de un switch apagado produciría≤0.2V con2µA de fuga, solo si aplica esa especificación y sin acoplos. Carga el divisor cuando el switch cierra:2.2k||100k≈2.153k y cambia ganancia≈1.9%; habría que actualizar escala/calibración. Una resistencia serie sola reduce la corriente de fallo pero no crea una garantía de0mA de inyección. Un amplificador buffer tampoco aporta automáticamente tolerancia apagado.

Se debe definir primero VOUT máximo/transitorio, impedancia/energía y duración de falla, tensión negativa y secuencia de fuentes. Después seleccionar clamp/aislamiento con tolerancias, fugas a85°C, tiempo de corte y GND estable. No se incorporó ningún componente adicional a una BOM definitiva.

## Impedancia, C17, adquisición y precisión

Rth=1918.605Ω; C17=1nF C0G±5%; τ=1.9186µs; fc=82.953kHz. A10kHz, |H|=0.992812 y fase=-6.874°. El filtro no elimina rizado10kHz ni es anti-alias suficiente para muestreo10kS/s. La muestra síncrona tiene sesgo de fase/rizado que debe compararse con el promedio previo de20 muestras.


El prototipo L432 usa ADC20MHz,247.5 ciclos de adquisición=12.375µs,12.5 de conversión=0.625µs:13µs total más latencia de trigger. Tabla64 de DS11451, PA0 canal rápido, permite12kΩ con247.5 ciclos a80MHz; se elige una adquisición más larga a20MHz, como opción conservadora. Rth≈1.92k y una eventual serie1k quedan por debajo de esa referencia; cable, capacitancia y fugas deben entrar en el modelo final. CADC típico5pF es típico, no máximo de producción.

C17 se carga continuamente; ante un escalón externo de escala completa el asentamiento RC a½LSB requiere≈17.3µs, no se debe confundir con la adquisición del sample-and-hold. Colocar la reserva de carga cerca del ADC del lado protegido y verificar su topología al elegir protección/cable; no se movió C17 en esta fase. Evitar seleccionar canales ADC previos con gran salto; calibrar ADC después de estabilizar su regulador, antes de iniciar triggers.

Escala de firmware nominal: `VOUT=count×3.3×(17.2/2.2)/4095`, **6.300366mV de salida/conteo**, offset0 provisional. El modelo de endpoints4095 conserva la convención del firmware; un LSB físico ideal usa4096 (~0.0244% de diferencia). Resistencia1% da error de ganancia aproximado±1.75%, no exactitud total. Sumando VREF±5% sin calibración, el error de escala por esquinas es -6.41%…+7.11% antes de ADC/temperatura. Una fuga de1µA produce1.919mV en ADC (~15mV referidos aVOUT).


La tabla65 da error ADC bajo condiciones limitadas de prueba, no exactitud universal de la aplicación. Usar medición VREF+ y calibración con dos pares DMM/conteos, registrar tolerancias térmicas y carga de protección. No inferir precisión absoluta de la resolución nominal.

Ensayos pendientes: barrido5/6/7/8.18V;20/24V con MCU desacoplado/protegido; rampas de alimentación, Buck encendido/NUCLEO apagada y viceversa; pulsos/negativos con energía controlada; rizado/acopleGND y fase de muestreo; adquisición y error. No se realizaron contra hardware.
