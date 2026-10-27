# Protocolo de primer encendido — Buck Rev B

**Prototipo pendiente de puesta en marcha. No es un diseño validado térmica ni experimentalmente.** Este protocolo no autoriza energizar la etapa de potencia ni desbloquear RUN: `BUCK_BOARD_REVIEWED=0` se mantiene hasta completar y registrar los pasos 1–5 con revisión del equipo.

Equipo mínimo: fuente de banco con límite de corriente, DMM, osciloscopio de 2 canales (una sonda diferencial o aislada para VB–VS), carga resistiva de 6 Ω ≥ 15 W, NUCLEO-L432KC con SB17 y SB18 **abiertos** (comprobar continuidad), adaptador USB-UART de 3,3 V para USART1 (D1/D0), cable WR-BHD de 10 vías con la banda roja en el pin 1.

Registrar en cada paso: fecha, placa (número de serie escrito a mano), valor medido, instrumento y quién midió.

## 0. Sin alimentación

1. Inspección visual con lupa: pin 1 de U1–U9 y de U10 (SOT-23, cátodo = pin 1), banda de D1–D5, polaridad «+» de C1/C2/C4/C5, orientación de Q1 (G-D-S, pestaña hacia L1), banda de D2 hacia C6/U1, llave de J3 hacia el interior de la placa, entrada de cable de J1 (borde superior) y J2 (borde inferior).
2. Resistencias a GND (DMM, sin cables): VIN > 1 kΩ tras cargar C1/C2, +5V > 1 kΩ, VOUT ≈ 12 kΩ (divisores 17,2 kΩ ‖ 40,9 kΩ), NUC_3V3 abierto o > 100 kΩ, SW sin corto a VIN ni GND.
3. Bobinas: L1 y L2 entre 300 y 380 µH cada una con LCR a 10 kHz si hay medidor; resistencia ≤ 80 mΩ.

## 1. Buck solo (sin cable J3), sin carga

Fuente a 12,0 V, límite 100 mA, subir lentamente desde 0 V.

| Punto | Esperado | Motivo |
|---|---|---|
| Corriente de entrada | < 40 mA estable | Lógica + 78M05; mayor indica corto |
| +5V (C11) | 4,75–5,25 V | Regulador U2 |
| REF_2V5 (C22) | 2,48–2,52 V | U10 polarizado por R23 |
| NUC_PG (R19) | ≤ 0,4 V | U9 sin NUC_3V3 |
| BUF_OE_N | ≈ +5V | Interfaz deshabilitada |
| ADC_EN | ≤ 0,4 V | TMUX1511 abierto |
| NTRIP (TP8) | ≤ 0,8 V | D5 fuerza el latch a FALLA |
| SD (TP7) | ≈ +5V | Driver apagado |
| GATE (TP4) / SW (TP3) | ≈ 0 V | Q1 apagado |
| VOUT (TP5) | ≈ 0 V | Sin conmutación |

Si cualquier valor sale de rango: cortar la fuente y no continuar.

## 2. NUCLEO sola por USB, cable conectado, Buck sin VIN

| Punto | Esperado |
|---|---|
| NUC_3V3 en J3.9 | ≥ 3,22 V (umbral de liberación de U9 ≤ 3,20 V en el peor caso) |
| +5V del Buck | < 0,3 V (sin retroalimentación significativa desde la NUCLEO) |
| VSENSE en J3.7 | ≈ 0 V (R21) |
| Consola UART `i` | `locked=1`, modo OFF |

Si NUC_3V3 < 3,22 V la interfaz puede no habilitarse nunca (falla segura). Registrar y evaluar TPS3808G30 junto con una referencia de clamp menor antes de cambiar nada.

## 3. Ambas fuentes, RUN bloqueado

1. Con la NUCLEO alimentada, aplicar 12,0 V al Buck (límite 100 mA).
2. Tras 0,18–0,42 s: NUC_PG ≈ +5V, BUF_OE_N ≤ 0,4 V, ADC_EN ≈ +5V.
3. El latch permanece en FALLA (NFAULT_MCU = J3.6 bajo, PB7 lo lee) hasta un pulso RESET. Con la compilación bloqueada no hay pulso: comprobar que SD sigue alto.
4. Desconectar el USB de la NUCLEO con el Buck encendido: SD debe seguir alto; NUC_PG bajo en < 50 µs (osciloscopio en NUC_3V3 y SD).

## 4. Bootstrap y puerta sin potencia en la salida

Requiere una compilación de revisión **solo en banco** acordada por el equipo, con la carga desconectada y la fuente limitada a 200 mA.

1. Sonda diferencial VB–VS (C6). En reposo VBS ≥ 10,5 V a VIN = 12,0 V (cálculo: 10,82–10,93 V con UF4004 a VF máx. y C6 reducida al 50 %).
2. PWM en lazo abierto d = 0,4 / 0,5 / 0,6 durante 1 s: VBS mínimo ≥ 10,0 V, VGS de Q1 ≈ VBS, sin oscilaciones > 2 V en GATE.
3. No ensayar a 10,8 V ni con salida precargada: Rev B no lo garantiza.

## 5. Calibración ADC y protección

1. Con el convertidor en lazo abierto y carga de 6 Ω, medir VOUT con DMM y las cuentas ADC (consola) en dos puntos (≈ 5 V y 7 V). Actualizar `BUCK_ADC_VOLTS_PER_COUNT`/`BUCK_ADC_OFFSET_VOLTS`; el valor nominal es 6,4844 mV/cuenta.
2. Disparo por corriente: verificar el umbral del comparador sobre ISENSE (TP6) con corriente limitada por la fuente; tiempo SD-alto < 10 µs.
3. Disparo por tensión: OVSENSE contra VREF (umbral nominal 8,18 V de VOUT, 7,56–8,83 V por tolerancias).
4. Solo entonces revisar la autorización de `BUCK_BOARD_REVIEWED=1` para los ensayos del curso (12 V, 5–7 V, 6 Ω, 10 kHz) con temperatura de L1/L2, Q1, D1 y RS1 registrada a los 10 min.

## Notas de seguridad

- Calibrar inyectando tensión externa en J2 con VIN desconectado polariza el diodo interno de Q1 y alimenta C1/C2 y U2: no hacerlo.
- La placa no tiene orificios de fijación: sujetar por los bordes sobre soporte aislante; L1/L2 (37 g c/u) requieren fijación mecánica si se transporta montada.
