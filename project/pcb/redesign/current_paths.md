# Caminos de corriente y presupuesto Buck

Inspección de la netlist exportada del rediseño, 40 redes, sin cambios durante la fase de reglas. La [netlist posterior](validation/pcb_rules/post_rules.net.xml) conserva exactamente los endpoints de la anterior. No se dedujeron reconexiones para mejorar la topología.

## Conmutación

ON: banco de entrada C1/C2 y desacoplo C3 → VIN → Q1 drenador (pad 2) → Q1 fuente (pad 3) → SW → L1.1/L1.2 → LMID → L2.1/L2.2 → IP → RS1.1/RS1.2 → VOUT → carga J2 → GND → negativos de entrada. D1 queda inversamente polarizado. C4/C5 absorben/entregan la diferencia entre corriente del inductor y carga.

OFF: GND → D1 ánodo (pad 2) → D1 cátodo (pad 1) → SW → L1 → LMID → L2 → IP → RS1 → VOUT → carga/condensadores → GND. Es un Buck asíncrono; no existe un MOSFET inferior activo. El lazo de conmutación de alta di/dt es la diferencia entre estados: entrada C3/C1/C2, Q1, SW, D1 y retorno. Mantenerlo compacto en F.Cu, sin compartir su impedancia con medida.

RS1 está en el lado alto entre IP y VOUT, no en GND. U6 IN+ pad 3 mide IP y U6 IN− pad 4 mide VOUT: llevar derivaciones Kelvin a los terminales del shunt. ISENSE, VSENSE y VREF no deben cargar el retorno pulsante de potencia.

Bootstrap: VIN → D2 → BOOT/C6 VB, C6 entre BOOT (U1.7 VB) y SW (U1.6 VS). La carga de compuerta sale de C6 a través del driver U1, HO y R1 hacia GATE/Q1; R2 está en paralelo entre GATE y SW. La recarga depende de que SW baje lo suficiente. R2 descarga/polariza la compuerta y no es la resistencia serie de recarga. El PWM del MCU controla lógica/SN74HCT14/IR2110, no suministra la corriente principal de compuerta.

## Modelo de corrientes

CCM ideal: D=Vo/Vi, ΔIL=(Vi−Vo)·D/(L·f), Io=Vo/R, ILrms=√(Io²+ΔIL²/12). IQ1rms=√D·ILrms; ID1rms=√(1−D)·ILrms. Entrada media de potencia=D·Io; entrada desde el interruptor RMS=IQ1rms. ICin,rms=√(Io²D(1−D)+D·ΔIL²/12); ICout,rms=ΔIL/√12. Valores por banco, no por cada capacitor individual: el reparto depende de ESR, ESL y montaje.

Nominal 12→6 V, R=6 Ω, L=660 µH y 10 kHz: D=0.5, Io=1 A, ΔIL=0.4545 A, ILrms=1.0086 A, pico=1.2273 A; Q1 y D1 RMS=0.7132 A cada uno, media=0.5 A cada uno; entrada media=0.5 A más pérdidas y auxiliares, Cin RMS=0.5085 A, Cout RMS=0.1312 A.

Los presupuestos 1.458 A de salida, 1.470 A RMS y 1.775 A pico son compatibles aproximadamente con Vo=7 V, carga 4.8 Ω y L=528 µH. Son supuestos de tolerancia (−20% respecto a 6 Ω y 660 µH), no máximos garantizados; validar que la inductancia real bajo I/T se mantiene y que no satura. La capacitancia objetivo de salida 20 µF requiere validar C efectiva, ESR y reparto RMS.

| VIN V | VOUT V | D ideal | Io A | IL RMS A | IL pico A | Q1 RMS A | D1 RMS A | Cin RMS A | Cout RMS A |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10.8 | 5 | 0.4630 | 1.0417 | 1.0520 | 1.2959 | 0.7158 | 0.7709 | 0.5289 | 0.1468 |
| 10.8 | 6 | 0.5556 | 1.2500 | 1.2585 | 1.5025 | 0.9380 | 0.8390 | 0.6306 | 0.1458 |
| 10.8 | 7 | 0.6481 | 1.4583 | 1.4645 | 1.6916 | 1.1791 | 0.8687 | 0.7048 | 0.1347 |
| 12.0 | 5 | 0.4167 | 1.0417 | 1.0538 | 1.3179 | 0.6802 | 0.8049 | 0.5238 | 0.1595 |
| 12.0 | 6 | 0.5000 | 1.2500 | 1.2607 | 1.5341 | 0.8915 | 0.8915 | 0.6357 | 0.1640 |
| 12.0 | 7 | 0.5833 | 1.4583 | 1.4670 | 1.7345 | 1.1205 | 0.9470 | 0.7292 | 0.1595 |
| 13.2 | 5 | 0.3788 | 1.0417 | 1.0554 | 1.3358 | 0.6496 | 0.8318 | 0.5160 | 0.1698 |
| 13.2 | 6 | 0.4545 | 1.2500 | 1.2627 | 1.5599 | 0.8513 | 0.9326 | 0.6340 | 0.1789 |
| 13.2 | 7 | 0.5303 | 1.4583 | 1.4694 | 1.7697 | 1.0700 | 1.0070 | 0.7395 | 0.1798 |

Para la entrada física se reserva **2 A continuos de dimensionamiento**, incluyendo margen: no significa que VIN conduzca exactamente 2 A. En la tabla la entrada media ideal máxima es 0.945 A; faltan pérdidas, auxiliares y transitorios. En C1/C2/C3 y el tramo Q1 la corriente es pulsante. La salida y los inductores transportan corriente casi continua con rizado; el diodo conduce solo durante OFF. GND debe soportar el retorno local pulsante de Cin/D1 y la carga, separados geométricamente del sensado aunque sean la misma red.

## Auxiliares y gate

Presupuesto preliminar de +5V: 100 mA, pendiente de sumar consumos máximos reales; el ancho 0.5 mm no aprueba térmica del regulador. A 13.2 V y 100 mA, un regulador lineal disiparía aproximadamente (13.2−5)·0.1=0.82 W más su consumo propio. NUCLEO se alimenta por USB independiente y no de +5V Buck. NUC_3V3 alimenta principalmente pull-up R13; con 10 kΩ y nivel bajo, unos 0.33 mA, además de las corrientes de interfaz aún por cerrar.

Qg=100 nC es hipótesis conservadora de trabajo, no máximo acreditado de Q1. A 10 kHz resulta 1 mA medio de carga de gate y 2 mA de valor absoluto si se suman carga y descarga. Un ejemplo de pulso rectangular 1.33 A da Ig,rms≈√(2·1.33·100 nC·10 kHz)=51.6 mA; no es medición ni límite. El ancho de 0.5 mm se elige principalmente para lazo corto, inductancia y caída, no por corriente media. IR2110 puede entregar pulsos fuertes; faltan Q1 definitivo, resistencias, duración y formas de onda. La recarga bootstrap a duty 95% podría requerir ~52 mA medios en los 5 µs OFF del presupuesto: consultar [bootstrap_validation.md](bootstrap_validation.md).

## Riesgos sin cierre

El duty, arranque, salida precargada, recarga C6, sobretensión y cortocircuito no están acotados mediante ensayos. La conducción transitoria incluye recuperación del diodo y parásitos; no se suma una cifra inventada a la corriente RMS. El tiempo real de actuación de la protección determina energía e I²t. Los 2.5 A de evaluación no son un máximo absoluto ni una garantía de protección. El dimensionamiento térmico normal no valida SOA, saturación, soldaduras, conector, falla continua ni estabilidad del PI.

Permanecen los bloqueos de [open_issues.md](open_issues.md): bootstrap al mínimo de alimentación, ADC con MCU apagado, backfeeding de señales, puentes NUCLEO, Q1/D2/L1/L2/RS1 y revisión mecánica. Configurar reglas preliminares no resuelve ni aprueba esos puntos.
