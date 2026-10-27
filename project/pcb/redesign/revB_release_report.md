# Buck Rev B — informe de liberación del prototipo

**Estado: LISTO PARA PEDIR COMO PROTOTIPO DE LABORATORIO** — PCB con ensamblaje SMT superior de 62 piezas en JLCPCB; L1/L2 y las piezas THT se sueldan a mano (sección 7). Verificado en computador; no es un diseño validado térmica ni experimentalmente. No se accedió a cuentas, no se subió nada a JLCPCB ni se pagó: el pedido lo hace el usuario.

| Identificación | Valor |
|---|---|
| Revisión | B, 2026-10-27 (título de hojas «REV B PROTOTYPE») |
| Proyecto | `project/pcb/redesign/buck.kicad_pro` (KiCad 10.0.7) |
| PCB SHA-256 | `745381f255f3c3d0d3f8d2cd6daa28ff16a616c3eb416cacf81813b22210c963` |
| Paquete | `production/jlcpcb-revB-2026-10-27/` (hashes en `SHA256SUMS.txt`) |
| Revisión A preservada | `history/revA_quote_20261027/` (PCB `b36ae24a…`, idéntica a la cotización Rev A) y su paquete `production/jlcpcb-quote-2026-10/` sin cambios |
| Placa | 2 capas, FR-4 1,6 mm, 1 oz, contorno sin cambios 105,55 × 81,05 mm, sin orificios de fijación |

## 1. Requisitos conservados

12 V nominal, salida 5–7 V, 660 µH (2 × 330 µH en serie), 20 µF de salida (2 × 10 µF), PWM 10 kHz, NUCLEO-L432KC externa con la asignación de J3 de la revisión NUCLEO, inversión d′ = 1 − d en U3, protecciones por hardware independientes del firmware y `BUCK_BOARD_REVIEWED=0`. No se ejecutaron los generadores antiguos (`tools/generate.py`, `finish_board.py`); todo el trabajo Rev B está en `revb_tools/`.

## 2. Puerta 1

Detalle en [revB_gate1_components.md](revB_gate1_components.md). Herramientas y dibujos: **cerradas**. Suministro para ensamblaje JLCPCB: **cerrada por decisión** (sección 7): L1/L2 sin stock en JLCPCB/LCSC se montan a mano.

## 3. Cambios eléctricos

### Interfaz entre dominios (hoja nueva `buck_5.kicad_sch`, «Power-domain interface»)

| Función | Implementación |
|---|---|
| PWM, RUN, RESET | U7 SN74LV4T125PWR alimentado por +5V del Buck: MCU_PWM→R4→PWM_IN→1A→1Y=DPRIME; RUN→2A→2Y=RUN_5V; RESET→3A→3Y=RESET_5V. Canal 4 deshabilitado (4A a GND, 4OE a +5V). Ya no hay pull-ups de 5 V en nodos del MCU: R3 queda en DPRIME (salida del buffer). |
| Estado por defecto | Con U7 en alta impedancia: R3 mantiene DPRIME alto (Q1 apagado), R16/R17 mantienen RUN_5V/RESET_5V bajos (SD alto). En el lado MCU: R5/R6 bajan RUN/RESET y R18 sube PWM_IN a NUC_3V3 (no a 5 V). |
| Supervisión | U9 TPS3808G33 (VDD = +5V, SENSE = NUC_3V3 por R22 10 k + C21 1 nF, CT a VDD por R24 100 k: 180/300/420 ms). RESET̅ → NUC_PG (R19 22 k a +5V) → inversores libres de U3: BUF_OE_N (OE̅ de U7) y ADC_EN (SEL1 de U8). |
| ADC | Divisor R14/R15 → VSENSE_DIV; D3 BAT54WS (GND→nodo) y D4 BAT54WS (nodo→REF_2V5) limitan el nodo; R20 1 k → U8 TMUX1511 S1→D1 → VSENSE (C17, R21 100 k de descarga) → J3.7. U8 alimentado por NUC_3V3. |
| Referencia del limitador | U10 LM4040 2,5 V polarizado por R23 2,2 k desde +5V (1,00–1,27 mA ≥ IRMIN 65 µA) con C22. Independiente del raíl de 3,3 V. |
| Latch tras apagones | D5 BAT54WS de NTRIP a ADC_EN: mientras la interfaz está deshabilitada (NUC_3V3 bajo, arranque de +5V) el latch HCT00 queda en FALLA y requiere un pulso RESET explícito. |

Diferencia de netlist Rev A → Rev B verificada terminal a terminal con `revb_tools/netdiff.py`: solo cambian R4.2 (DPRIME→PWM_IN), U3.3/4/5/6 (GND/NC→NUC_PG, BUF_OE_N, ADC_EN), U4.1/U4.4 (RESET/RUN→RESET_5V/RUN_5V), R14.2/R15.1 (VSENSE→VSENSE_DIV) y se añaden 21 componentes. Escritas por `sch_revb.py`, `sch_lands.py` y `sch_review_fixes.py`.

### Correcciones por la revisión independiente

La revisión independiente de protección y alimentación (sin conocer mis conclusiones) encontró dos problemas altos y tres medios; disposición:

| Hallazgo | Disposición |
|---|---|
| H1: el LM4040 sobre el nodo de medida consume 5–35 µA por debajo de la ruptura (SNOS633N Fig. 5-4, verificado), error no lineal −0,3 V a 7 V | **Corregido**: U10 pasa a ser referencia polarizada; D4 hace el clamp. El nodo solo ve fugas de Schottky (≈ 0,05 µA a 25 °C ≈ 0,1 mV; hasta ≈ 2 µA a 75 °C ≈ 30 mV en VOUT, de signos opuestos en D3 y D4) |
| H2: escala ADC del firmware 2,9 % baja | **Corregido**: 6,4844 mV/cuenta en `calibration.h`, con prueba de host |
| M1: margen de liberación de U9 frente al LDO de la NUCLEO (≈ +32 mV en el peor caso) | **No cambiado** (TPS3808G33 fijado por el plan; G30 rompería el margen del clamp). Falla segura: interfaz deshabilitada. Comprobación en el paso 2 del protocolo |
| M2: rearranque al 95 % tras caída de NUC_3V3 o de VIN bajo UVLO | **Corregido**: D5 fija el latch con la interfaz deshabilitada; firmware dispara si VOUT < 50 % de la referencia > 2 ms |
| M3: estado indefinido del latch al encender | **Corregido** por D5 + retardo de U9 |
| L1: salida Hi-Z de U7 a +5V por R3 frente al máximo 4,6 V | Aceptado: SCLS749C §6.1 nota 2 permite exceder la tensión de salida respetando corriente (≤ 0,5 mA) y §6.3 recomienda VO ≤ VCC en Hi-Z |
| L3: R19 10 k en el mínimo del fabricante | **Corregido**: 22 k |
| L4–L8 | Documentados; L8 (UART solo en el conector) es intencional para un adaptador externo |

### Lands y huellas

Generadas desde el dibujo del fabricante (`revb_tools/footprints_revb.py`, biblioteca `Buck_RevB`): L1/L2 Murata 6000B; J1/J2 Same Sky TB002; J3 Würth WR-BHD (taladro 1,1); Q1 TO-220 taladro 1,4 (IPC-2222); C1/C2 y C4/C5 según Panasonic AAB8000COL10; RS1 según TA-I (pads 2,1 × 4,0, separación 4,1); U3/U4 D0014A, U5 D0008A **con courtyard** ±3,75 × ±2,75, U6 DBV0005A, U7/U8 PW0014A, U9 DBV0006A, U10 DBZ0003A, D3–D5 SOD323 Diodes. C4/C5 indican ahora 50 V y RS1 2 W, coherentes con sus MPN.

## 4. Layout

- Célula de conmutación: drenador de Q1 alimentado por un corredor VIN de 2,6 mm desde C1/C2 (C3 de 100 nF a 7,5 mm del drenador); fuente de Q1 unida directamente al cátodo de D1 (1,2 mm) y al pad 1 de L1; retorno por el plano B.Cu bajo la célula, sin señales en B.Cu en el rectángulo de la célula. La revisión independiente estimó ≈ 98 mm² de lazo de alta frecuencia por C3 antes de añadir el enlace directo S→K; aceptable a 10 kHz, mejorable en una próxima revisión con un cerámico ≥ 1 µF/50 V entre drenador y ánodo de D1.
- Lazo de puerta sin cambios de capa (≈ 70 mm², bootstrap ≈ 14 mm²): U1 a 9 mm de Q1, HO→R1→G y S→VS solo en F.Cu, HO pasa bajo el cuerpo de D2 y el cátodo THT de D2 queda dentro del lazo para alimentar C6 sin vías. **No hay vías en HO, GATE, BOOT ni SW** (las dos vías de HO de Rev A desaparecen).
- El único hueco relevante del plano B.Cu es el puente VIN a VCC de U1 (≈ 1,1 × 18 mm bajo el driver, no bajo la célula); el retorno de C7 lo rodea. Menor a 10 kHz.
- Kelvin según TA-I: la corriente entra a RS1 por los extremos exteriores; IN+/IN− de U6 salen de los bordes interiores en pistas dedicadas. C16 junto a VS de U6 con vía GND propia.
- L1–L2 unidos por un puente de 8 mm; salida RS1→C4/C5→J2 en 2–3,5 mm.
- Serigrafía: designadores en F.Fab (plano de montaje); en la serigrafía solo rótulos de polaridad, pin 1 de J3, puntos de prueba y la identificación de revisión.
- Vertidas GND en ambas caras con 266 vías de cosido y vías de abanico (4 en el ánodo de D1 y en la pestaña de U2).

## 5. Cálculos (`validation/revb/calculations.json`, `revb_tools/calc_revb.py`)

- ADC: ganancia 0,124277 (−2,84 % frente a Rev A), 6,4844 mV/cuenta; fuente ≤ 2,92 kΩ con C17: fc 54 kHz, −10,4° a 10 kHz, −1° a 1 kHz.
- Clamp: pin ADC ≤ 2,82 V hasta VOUT = 30 V y ≤ 2,90 V con 10 mA de clamp; U8 solo conduce con NUC_3V3 ≥ 3,02 V (umbral mínimo de U9) → sin inyección positiva. Negativo: ≥ −0,32 V hasta −12 V (≥ −0,40 V a −24 V), dentro de −0,5 V de TMUX1511. Techo de medida ≈ 21 V.
- Supervisión: disparo 3,02–3,12 V, liberación ≤ 3,20 V, latencia típica ≈ 30 µs (filtro 10 µs + 20 µs de U9 + lógica < 1 µs).
- Bootstrap a 12,0 V, VF(UF4004) = 1,0 V máx., VS = 0 V (sin el aporte de D1), Qg = 63 nC máx. (IRFZ44NPbF), R2 en paralelo: VBS mínimo 10,82–10,93 V para 5/6/7 V de salida aun con C6 reducida al 50 %; requiere VIN ≥ 11,18 V para VBS ≥ 10 V en el peor caso. **No se afirma operación a 10,8 V ni con salida precargada.**

### Estados de alimentación

| Estado | Resultado (análisis + revisión independiente) |
|---|---|
| Ambas presentes | Interfaz habilitada 180–420 ms después; latch en FALLA hasta RESET explícito |
| Solo Buck (NUCLEO ausente, apagada o cable desconectado) | U7 en Hi-Z, SD alto, DPRIME alto, U8 abierto; corriente hacia la NUCLEO ≈ 0 |
| Solo NUCLEO | U7 sin VCC (Ioff ≤ 5 µA por entrada), U8 abierto (ADC_EN = 0 y pull-down interno), retroalimentación total ≤ 16 µA |
| Arranques en cualquier orden y rampas lentas | Sin habilitación sin orden del MCU: SD alto por R16 y DPRIME alto por R3; UVLO de IR2110 (VIN ≥ 7 V) asegura +5V válido cuando HO puede conducir |
| Caída de NUC_3V3 | Interfaz deshabilitada en ≈ 30 µs y latch a FALLA (D5) |
| Caída de VIN bajo UVLO | Q1 apagado por UVLO; firmware dispara por colapso en 2 ms |

## 6. Verificación ejecutada

| Comprobación | Resultado |
|---|---|
| ERC (`--severity-all`) | 0 errores, 2 avisos `isolated_pin_label` UART_TX/RX: reservas del arnés sin circuito local (intencional, sin exclusiones) |
| DRC con zonas rellenadas y paridad | **0 errores, 0 pendientes, 0 discrepancias de paridad**, 3 avisos (abajo) |
| Reglas añadidas | Una: holgura 0,19 mm solo entre pads del mismo encapsulado U7/U8; el land TI PW0014A tiene 0,20 mm entre pads, menor que la holgura de clase. No relaja otras holguras ni oculta avisos |
| Gerbers | ZIP íntegro (CRC), 12 archivos; renderizados con pygerber 2.4.3 e inspeccionados: cobre, máscara (vías tapadas), pasta, serigrafía y contorno |
| Taladros | 415 PTH, 0 NPTH: vías 0,3 (43) y 0,4 (344), TP 1,0 (9), J3/D2 1,1 (12), J1/J2 1,3 (4), Q1 1,4 (3) |
| BOM/CPL | 31 líneas / 62 colocaciones en cara superior (L1/L2 fuera, montaje manual), conciliadas con netlist y posiciones nativas; sin duplicados ni MPN contradictorios |
| Stock JLCPCB del BOM final | 31/31 líneas con stock para ≥ 20 placas (`evidence/jlc_stock_revB.json`, 2026-10-27 18:29 UTC) |
| Firmware | Prueba de host (ASan/UBSan) en verde; imagen ARM **no compilada** (sin `arm-none-eabi-gcc` en este equipo) |
| Revisión independiente del layout | Sin hallazgos críticos; confirmó DRC/paridad, Kelvin, analógicas ≥ 30 mm de SW, ausencia de vías en el lazo de puerta, holguras taladro/pin (Q1 0,22 mm, J3 0,195 mm), vías tapadas e integridad del paquete. Aplicado: enlace S→K directo, centroide de U2 en la CPL (−42,84 mm), regla de radios térmicos restaurada a 2 |

Avisos DRC justificados individualmente:

1. `SW and LMID width review` — pista SW de 0,5 mm (119,7; 89,9), 2,2 mm: es el retorno VS del driver (≈ 1 A de pico durante ≈ 100 ns, 0,63 mA medios), no el camino de la bobina; 2 mm no caben entre U1 y C6 sin agrandar el lazo de puerta.
2. `VIN width review` — VIN 0,5 mm en F.Cu (121,0; 96,9), 1,0 mm: alimentación VCC de U1 (≤ 1 mA medio).
3. `VIN width review` — VIN 0,5 mm en B.Cu (123,4; 96,9), 2,4 mm: mismo ramal VCC.

## 7. Decisiones para el pedido (2026-10-27)

Tomadas tras una segunda opinión externa (no formal) que señalaba la separación Q1–L1, el suministro de L1/L2, las condiciones de bootstrap, los transitorios de apagado y la revisión del pedido real:

| Punto | Decisión aplicada |
|---|---|
| Pestaña de Q1 (VIN) junto al terminal SW de L1 | Cadena L1→L2→RS1→salida desplazada 2 mm: separación **1,28 → 3,29 mm** con dimensiones máximas (E de Infineon, 23,5 mm de Murata); courtyards a 2,35 mm. Rerruteado; DRC 0/0/0 |
| L1/L2 sin stock JLCPCB/LCSC | **No los coloca JLCPCB**: fuera de BOM/CPL, comprar 60B334C (DigiKey 811-2464-ND) y soldar a mano; la pasta queda en sus pads |
| LM4040AIM3-2.5/NOPB sin stock | **Aceptada** la variante LM4040AIM3X-2.5/NOPB (C111866), mismo dispositivo según TI SNOS633N §11 |
| R10 con 5 unidades | **Cambiada** a UNI-ROYAL 0603WAF3092T5E (C23022): 30,9 kΩ 1 % 0603, ±100 ppm/°C como la anterior; el umbral OVP no cambia |
| Firmware ARM sin compilar | No bloquea la fabricación; compilar con `build.py` antes de programar |

Al pedir (pasos del usuario en el portal, ver `production/.../README.md`): revisar Gerbers en el visor, confirmar 31 líneas y 62 colocaciones sin sustituciones automáticas y comprobar las rotaciones en el visualizador (tabla en el README). Comprar aparte las piezas de `manual_assembly_revB.csv`.

## 7b. Uso previsto y límites de esta placa

Primera placa **exclusivamente para laboratorio**: entrada regulada de **12 V** con límite de corriente, **carga resistiva** (6 Ω del curso), pruebas de arranque y protección **supervisadas** según [revB_first_power_on.md](revB_first_power_on.md). Fuera de alcance: 10,8 V o menos (VBS < 10 V posible por debajo de ≈ 11,2 V), arranque con salida precargada y cargas electrónicas o sensibles. Al apagar Q1 por protección, la energía de L1/L2 (½·L·I² ≈ 1,3 mJ a 2 A) pasa a C4/C5; sin carga, una transferencia ideal daría ≈ 13 V de pico: dentro de los 50 V de C4/C5 y 40 V de D1, pero los transitorios reales no se han medido. Sin orificios de fijación: soporte aislante por los bordes; soldar Q1 perpendicular a la placa.

## 8. Entregables

`production/jlcpcb-revB-2026-10-27/`: `gerbers_revB.zip` (+ `gerbers/` y mapas de taladro PDF), `bom_jlcpcb_revB.csv`, `cpl_jlcpcb_revB.csv`, `manual_assembly_revB.csv`, `assembly_top_revB.pdf`, `schematic_revB.pdf`, `evidence/` (ERC/DRC JSON y RPT, netlist, posiciones, comandos, resumen, stock) y `SHA256SUMS.txt`. Editables: `buck.kicad_pro`, `buck*.kicad_sch`, `buck.kicad_pcb`, `buck.kicad_dru`, bibliotecas en `libraries/`.

Reproducir desde `revb_tools/`: `pcb_update.py` (netlist → PCB), `route_revb.py` (ruteo), `silk_revb.py`, `export_revb.py`, `jlc_stock.py`. El ruteo es determinista dado `placement.py` y las rutas manuales de `route_revb.py`.
