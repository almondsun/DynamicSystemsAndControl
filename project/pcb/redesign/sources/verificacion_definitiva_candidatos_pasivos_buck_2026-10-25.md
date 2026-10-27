# Informe de verificación de pasivos SMD — Buck 12 V / 10 kHz

**Fecha de revisión:** 25 de octubre de 2026  
**Proyecto:** `DynamicSystemsAndControl` — asignatura Sistemas Dinámicos y Control  
**Mandato:** analizar cada pasivo por corriente, potencia, tensión y temperatura, empleando **los candidatos preferidos como selección de trabajo final**. Se conserva el número de referencias originales: 35 componentes (L1/L2, C1–C17, R1–R15 y RS1).

**Dictamen ejecutivo: NO LIBERAR PARA FABRICACIÓN.** No porque todo esté mal, sino porque hay decisiones que afectan la integridad eléctrica y otros parámetros que los datos publicados no garantizan. **APROBADO (CC)** significa aprobado por corriente/potencia en régimen continuo dentro del presupuesto calculado; no es autorización de PCB completa. Los estados de selección integral son conservadores: **PENDIENTE** hasta cerrar información o pruebas faltantes. La selección de R10=30,9 kΩ y C16=220 nF son **adopciones técnicas propuestas**, explícitamente distintas del esquema histórico, no evidencia de cambios ya aplicados.

> **Evidencia y límites:** bases `passives_requirements.md`, `jlc_passives_candidates.md`, `Componentes_PCB_control.txt` y auditorías previas. Se consultaron documentos primarios de Murata, Panasonic, TA-I, Infineon, TI, ST, Samsung, Yageo y UNI-ROYAL. Para varios códigos de las familias aún no se obtuvo una curva garantizada de DC bias, ESR a 10 kHz, energía de pulso o curva térmica de PCB. Los cálculos algebraicos no reemplazan pruebas ni inspección del layout; **no se editó ningún archivo CAD**.

## 1. Alertas que deben comunicarse al diseñador ahora

1. **ADC en R14/R15:** divisor 3 kΩ/1 kΩ deja `VSENSE=VOUT/4`. A VOUT=20 V hipotéticos, ADC recibe aproximadamente 5 V (hasta ≈5,075 V por tolerancia ±1 %), incompatible con PA0 analógico del STM32F103 (entrada no FT). A 13,2 V, la relación máxima arroja ≈3,350 V, por encima de VDDA=3,3 V típica de la placa, aunque no necesariamente del máximo absoluto. Requiere definir el límite real de VOUT e incorporar una protección/ajuste *si* los transitorios pueden alcanzar ese nivel; un resistor en serie no garantiza que el pin sobreviva. **Bloqueante de seguridad de interfaz**.
2. **C6/C7/R2/D2, bootstrap:** la capacitancia efectiva de un Samsung 1 µF ±10 % 0805 bajo ~10–13 V no alcanza automáticamente 1 µF; consumo estático de R2 domina parte del balance. A duty 95 %, `Qboot≈0,259 µC` es presupuesto, no dato medido. VCC mínimo 10,8 V deja reserva estrecha para IR2110 (VBS recomendado ≥10 V), especialmente al arrancar y recargar en 5 µs OFF. **Reservar espacio para solución revisada antes de cerrar layout**.
3. **L1/L2 Murata:** la ficha 6000B existe y define 4 A como corriente limitada por caída de L hasta 75 % o elevación de 40 °C. El modelo exige Ltotal≥528 µH (**80 % de 660**). Por tanto, **4 A no demuestra el mínimo del modelo**. Cuerpo SMD hasta ~23,5×27×20 mm, patrón de pads Murata específico 3×14 mm y separación indicada de 20,8 mm. Incompatible con la huella THT provisional del repositorio publicado.
4. **RS1 TA-I:** el rating de 2 W se da bajo 105 µm cobre y 300 mm² de pads/trazas para RLP25; proyecto publicado propone 35 µm (1 oz). Aun con `P_falla≈0,316 W`, cerrar calor de PCB y conexiones Kelvin desde pads.
5. **C1/C2, C4/C5 Panasonic:** buena selección en tensión y ripple. Sin embargo, cambios de valor efectivo/ESR respecto al sistema original y montaje/polaridad deben aprobarse; en salida no se garantiza 16 µF *efectivos* solo por tener 2×10 µF ±20 % inicialmente.
6. **R1:** resistor de gate 0805 conserva 10 Ω; la potencia promedio simplificada de 13,2 mW **no** aprueba sus pulsos repetitivos. Confirmar perfil de pulsos con curva específica y gate real.
7. **R10:** ninguno de los archivos suministrados determina un MPN único de 31 kΩ. Se considera **una pieza** Vishay 30,9 kΩ/C844354 como alternativa verificable; cambia VOVP nominal 8,20→8,18 V y exige aceptación del diseñador. No sustituir silenciosamente el esquema.

## 2. Condiciones de dimensionamiento y cálculos replicables

**Guía docente, según expediente:** VIN=12 V, fSW=10 kHz, L=660 µH, COUT=20 µF, R=6 Ω, D=1−d′=0,5 nominal; pasos d′=0,4/0,6, referencias de 5/7 V y cargas 4,8/7,2 Ω. **Extensión propuesta del equipo, no impuesta por la guía:** VIN=10,8…13,2 V, VOUT=5…7 V, ambiente 25…45 °C, combinación adicional 7 V/4,8 Ω; pruebas de falla hasta 2,5 A y **ejemplo** de transitorio de salida de 20 V, no límite garantizado.

\[
I_o=V_o/R,\quad \Delta I_L=\frac{(V_{in}-V_o)D}{Lf_s},\quad I_{L,\mathrm{RMS}}=\sqrt{I_o^2+\frac{\Delta I_L^2}{12}},\quad I_{pk}=I_o+\frac{\Delta I_L}{2}.
\]

\[
I_{COUT,\mathrm{RMS}}\approx \Delta I_L/\sqrt{12},\quad I_{CIN,\mathrm{RMS}}\approx\sqrt{I_o^2D(1-D)+D\Delta I_L^2/12},\quad P_R=I_{\mathrm{RMS}}^2R.
\]

| Magnitud | Nominal 12 V/6 V/6 Ω | Extremo de presupuesto ampliado |
|---|---:|---:|
| Corriente salida | 1,000 A | 1,458 A (7 V/4,8 Ω) |
| Rizado inductor ΔIL | 0,455 A pico a pico | ≤0,650 A pico a pico (modelo con pérdidas/tolerancias de expediente) |
| IL pico | 1,227 A | ≤1,775 A |
| IL RMS | 1,009 A | ≤1,470 A |
| ICIN RMS (banco) | 0,509 A | ≤0,740 A |
| ICOUT RMS (banco) | 0,131 A | ≤0,188 A |
| Corriente falla propuesta para ensayo | n/a | 2,5 A, **no** protección medida |

**C1/C2:** reparto conservador 60/40 y factor 1,25: `0,740 × 0,60 × 1,25 = 0,555 A` → especificación ≥0,60 A por pieza @10 kHz. **C4/C5:** `0,188 × 0,60 × 1,25=0,141 A` → ≥0,15 A por pieza. El fabricante Panasonic establece factor **0,7** a **10 kHz** frente al rating @100 kHz: `3,2×0,7=2,24 A` para 25SVPF100M y `2,5×0,7=1,75 A` para 50SVF10M **hasta 105 °C**. El rating ESR expresado a 100 kHz **no acredita ESR a 10 kHz**.

**Inductores:** DCR total máx catálogo a temperatura de referencia `2×0,08=0,16 Ω`, mejor que objetivo `≤0,20 Ω a 20 °C`. A 85 °C, usando incremento de resistencia del cobre `1+0,00393(85−20)=1,25545`, la DCR total de modelo ≈0,201 Ω. A 1,47 Arms: `P_Cu,total≈1,47²×0,201=0,434 W`, 0,217 W por pieza antes de pérdidas magnéticas. Con ambiente 45 °C y elevación admitida 40 °C, el valor hipotético `Rθ,efectiva≤40/0,217=184 °C/W` **ignora pérdidas núcleo**. La temperatura de 85 °C citada por el datasheet Murata es rango de *aire ambiente operativo*, no una clasificación inequívoca de temperatura máxima de cuerpo.

**Inductancia:** con tolerancia inicial −15 %, `L_total,0 = 660×0,85=561 µH`. Para sostener mínimo efectivo `528 µH`, la reducción adicional por DC/T/acoplamiento debe ser no mayor a `1−528/561=5,88 %`. Una ficha cuyo IDC permita reducir L al 75 % no garantiza esta condición. Medir Ltotal sobre piezas montadas a corriente y temperatura máximas de operación.

**Shunt:** `1,47²×0,0505≈0,109 W` en régimen; `2,5²×0,0505=0,316 W` a corriente falla supuesta. La tensión de sensado a 2,5 A es 126 mV. Un error de 1 mΩ en trayecto sense es aproximadamente 2 % frente a 50 mΩ; Kelvin en los pads importa más que escoger una ficha de muchos vatios.

**Derating de resistencias gruesa película UNI-ROYAL:** hoja de familia acredita 0603 **100 mW @70 °C** y disminución lineal hacia 0 W @155 °C: a 85 °C `100×(155−85)/(155−70)=82,35 mW`. Verificar que corresponde al sufijo/lote; las potencias de la matriz proceden de casos conservadores del expediente. La potencia de 0805 y energía por pulsos se evalúa aparte.

**Bootstrap:** usando `Qg=100 nC, Qls=5 nC, IQBS=230µA, Ileak=50µA+10µA, IR2≈1,333mA`, `ton=95µs` → `Q≈259 nC`. `ΔVBS=Q/Ceff≈0,259 V` para 1 µF real y **0,518 V** para 0,5 µF efectivo. Para recargar en 5µs se requiere corriente promedio ≈52 mA, sin incluir picos/arranque. Estos Qg/Qls, 95 % duty y fugas D2 son presupuestos del equipo, no garantías del IR2110 ni de UMW Q1. El rango **recomendado** de VBS del IR2110 es 10–20 V; que su UVLO esté por debajo de 10 V **no** elimina ese requisito.

**Divisores:** `VREF=5×10/(15+10)=2,0 V`. Con R10 original 31 kΩ y R11 10 kΩ, `V_OVP=2×(1+31/10)=8,20 V`. Si se adopta una sola 30,9 kΩ, `V_OVP=8,18 V` (−0,244 % nominal); tolerancias ±1 % de otras resistencias y offset comparador siguen dominando. Divisor ADC `VADC=VOUT×R15/(R14+R15)=VOUT/4`; con tolerancias opuestas de ±1 % se puede elevar a aproximadamente 0,25377 VOUT.

## 3. Matriz de aceptación individual de los 35 pasivos

**Lectura:** columna **eléctrica/térmica** califica las comprobaciones hechas, no los detalles no caracterizados; columna **selección integral** es la decisión para cerrar BOM y montar. **APROBADO (CC)** = tensión/corriente/potencia estacionarias cubiertas por cálculo, no aptitud de transitorios, huella ni estabilidad garantizada. La palabra PENDIENTE no significa que el componente esté defectuoso.

### 3.1 Inductores y shunt

| Ref. | Fabricante y MPN adoptado / JLC | Valor / presentación | Solicitud eléctrica y térmica calculada | Resultado parcial | Selección integral / falta cerrar |
|---|---|---|---|---|---|

| **L1** | Murata 60B334C / **C6823957** | 330 µH ±15 %, SMD 6000B | I_RMS ≤1,470 A; I_pk ≤1,775 A; P_Cu≈0,217 W a 85 °C; **rating:** 4 A bajo criterio L≥75 % o ΔT≤40 °C; DCR máx 80 mΩ, ambiente −40…85 °C | **PENDIENTE** | **PENDIENTE — CRÍTICO**. Inductancia efectiva por bobina debe sostener L_total≥528 µH; a −15 % inicial quedan 561 µH y solo 5,9 % de pérdida admisible. Curva L(I,T) y pérdidas núcleo ausentes; land Murata obligatorio. |

| **L2** | Murata 60B334C / **C6823957** | 330 µH ±15 %, SMD 6000B | Igual L1; las dos bobinas en serie conducen misma corriente; **rating:** Igual L1; DCR total máx 160 mΩ a referencia | **PENDIENTE** | **PENDIENTE — CRÍTICO**. Comprobar influencia de proximidad/acoplamiento: L_eq = L1+L2±2M. Validar I de saturación por condición de 80 % del nominal y temperatura. |

| **RS1** | TA-I RLP25FEER050 / **C160588** | 50 mΩ ±1 %, 2512, ±50 ppm/°C | P≤0,109 W normal; P≈0,316 W a 2,5 A; V≈0,126 V; **rating:** 2 W nominales *solo bajo cobre 105 µm/área 300 mm²*; Toper −55…170 °C | **APROBADO (potencia calculada, no térmica)** | **PENDIENTE — ALTO**. Con 1 oz (~35 µm) no atribuir 2 W. Demostrar derating y temperatura a 0,316 W; kelvin desde pads; land TA-I específico. |

### 3.2 Condensadores de potencia y auxiliares

| Ref. | Fabricante y MPN adoptado / JLC | Valor / presentación | Solicitud eléctrica y térmica calculada | Resultado parcial | Selección integral / falta cerrar |
|---|---|---|---|---|---|

| **C1** | Panasonic 25SVPF100M / **C136279** | 100 µF ±20 %, 25 V, OS-CON E7 Ø8×6,9 mm | I_C,RMS por unidad ≥0,60 A a 10 kHz; V≤13,2 V; **rating:** 2,24 A a 10 kHz/≤105 °C (3,2 A @100 kHz×0,7); ESR≤24 mΩ @100 kHz | **APROBADO (rizado y tensión)** | **PENDIENTE — MEDIO**. Margen I_ripple 3,73× y VDC 1,89×. Verificar C_banco efectiva≥160 µF con vida/temperatura y ESR @10k; land E7 y polaridad. 160 µF es mínimo por tolerancia inicial, no de vida. |

| **C2** | Panasonic 25SVPF100M / **C136279** | 100 µF ±20 %, 25 V, OS-CON E7 Ø8×6,9 mm | I_C,RMS por unidad ≥0,60 A a 10 kHz; V≤13,2 V; **rating:** 2,24 A a 10 kHz/≤105 °C (3,2 A @100 kHz×0,7); ESR≤24 mΩ @100 kHz | **APROBADO (rizado y tensión)** | **PENDIENTE — MEDIO**. Margen I_ripple 3,73× y VDC 1,89×. Verificar C_banco efectiva≥160 µF con vida/temperatura y ESR @10k; land E7 y polaridad. 160 µF es mínimo por tolerancia inicial, no de vida. |

| **C3** | Yageo CC0603KRX7R9BB104 / **C14663** | 100 nF ±10 %, 50 V X7R 0603 | Desacoplo VIN potencia; Vdc≤13,2 V; **rating:** 50 V; −55…125 °C nominales; C_min nominal 90 nF antes de DC/T/edad | **APROBADO (tensión/temperatura nominal)** | **PENDIENTE — BAJO**. Retención de ≥70 nF con DC/temperatura y proximidad Q1/D1; exigir evidencia capacitancia efectiva y ubicación. |

| **C4** | Panasonic 50SVF10M / **C454354** | 10 µF ±20 %, 50 V, OS-CON C6 Ø6,3×5,9 mm | I_C,RMS por unidad ≥0,15 A @10 kHz; V≤20 V transitorio supuesto; **rating:** 1,75 A @10 kHz y ≤105 °C (2,5 A @100k×0,7); ESR≤40 mΩ @100 kHz | **APROBADO (rizado y tensión)** | **PENDIENTE — ALTO**. Margen corriente 11,7× y tensión nominal ≥2,5× frente a 20 V hipotéticos. C_banco efectiva≥16 µF a vida/temperatura no demostrada; ESR @10 kHz y estabilidad PI; land C6 y polaridad. |

| **C5** | Panasonic 50SVF10M / **C454354** | 10 µF ±20 %, 50 V, OS-CON C6 Ø6,3×5,9 mm | I_C,RMS por unidad ≥0,15 A @10 kHz; V≤20 V transitorio supuesto; **rating:** 1,75 A @10 kHz y ≤105 °C (2,5 A @100k×0,7); ESR≤40 mΩ @100 kHz | **APROBADO (rizado y tensión)** | **PENDIENTE — ALTO**. Margen corriente 11,7× y tensión nominal ≥2,5× frente a 20 V hipotéticos. C_banco efectiva≥16 µF a vida/temperatura no demostrada; ESR @10 kHz y estabilidad PI; land C6 y polaridad. |

| **C6** | Samsung CL21B105KBFNNNE / **C28323** | 1 µF ±10 %, 50 V X7R 0805 | Q_boot≈259 nC por pulso de 95 µs (hipótesis); ΔVBS=0,259 V si Ceff=1µF; **rating:** 1µF solo nominal; límite −10 % ya es 0,9µF a 0 V; sesgo DC resta más | **PENDIENTE** | **PENDIENTE — CRÍTICO**. No se demuestra objetivo Ceff≥1 µF. Evaluar C6 en 10–13 V DC, tiempos off de 5µs, carga inicial y VBS/VGS; reservar posibilidad segundo MLCC sin poblar a ciegas. |

| **C7** | Yageo CC0603KRX7R9BB104 / **C14663** | 100 nF ±10 %, 50 V X7R 0603 | Desacoplo VCC driver IR2110; Vdc≤13,2 V; **rating:** 50 V; −55…125 °C nominales; C_min nominal 90 nF antes de DC/T/edad | **APROBADO (tensión/temperatura nominal)** | **PENDIENTE — CRÍTICO**. 100 nF no demuestra reserva de carga de bootstrap; ver eventual C18 local; exigir evidencia capacitancia efectiva y ubicación. |

| **C8** | Yageo CC0603KRX7R9BB104 / **C14663** | 100 nF ±10 %, 50 V X7R 0603 | Desacoplo VDD IR2110; Vdc≤5,25 V; **rating:** 50 V; −55…125 °C nominales; C_min nominal 90 nF antes de DC/T/edad | **APROBADO (tensión/temperatura nominal)** | **PENDIENTE — BAJO**. Retención ≥70 nF, pines reales del SOIC-16; exigir evidencia capacitancia efectiva y ubicación. |

| **C9** | Samsung CL21B334KBFNNNE / **C73142** | 330 nF ±10 %, 50 V X7R 0805 | VIN≤13,2 V; CI del esquema 78M05=330 nF nominal; **rating:** 50 V nominal, X7R; DC bias y vida sin límite garantizado recuperado | **APROBADO (valor nominal/tensión)** | **PENDIENTE — MEDIO**. No trasladar CI nominal de aplicación de UMW a mínimo efectivo garantizado; revisar necesidad de ESR/localidad. |

| **C10** | Yageo CC0603KRX7R9BB104 / **C14663** | 100 nF ±10 %, 50 V X7R 0603 | Desacoplo salida 78M05; Vdc≤5,25 V; **rating:** 50 V; −55…125 °C nominales; C_min nominal 90 nF antes de DC/T/edad | **APROBADO (tensión/temperatura nominal)** | **PENDIENTE — BAJO**. Estabilidad con C11 y ESR del regulador UMW no demostrada; exigir evidencia capacitancia efectiva y ubicación. |

| **C11** | Samsung CL21A106KAYNNNE / **C15850** | 10 µF ±10 %, 25 V X5R 0805 | V5 máximo supuesto 5,25 V; objetivo Ceff≥5µF; **rating:** 25 V, X5R; a mínima tolerancia 9µF, requiere retención adicional ≥55,6 % | **APROBADO (tensión nominal)** | **PENDIENTE — MEDIO**. Curva de DC bias del MPN y ESR/estabilidad del UMW 78M05 no certificadas para todo el rango. |

| **C12** | Yageo CC0603KRX7R9BB104 / **C14663** | 100 nF ±10 %, 50 V X7R 0603 | Bypass SN74HCT14; Vdc≤5,25 V; **rating:** 50 V; −55…125 °C nominales; C_min nominal 90 nF antes de DC/T/edad | **APROBADO (tensión/temperatura nominal)** | **PENDIENTE — BAJO**. Posición y retorno para conmutación HCT14; exigir evidencia capacitancia efectiva y ubicación. |

| **C13** | Yageo CC0603KRX7R9BB104 / **C14663** | 100 nF ±10 %, 50 V X7R 0603 | Bypass SN74HCT00; Vdc≤5,25 V; **rating:** 50 V; −55…125 °C nominales; C_min nominal 90 nF antes de DC/T/edad | **APROBADO (tensión/temperatura nominal)** | **PENDIENTE — BAJO**. Posición y retorno para latch NAND; exigir evidencia capacitancia efectiva y ubicación. |

| **C14** | Yageo CC0603KRX7R9BB104 / **C14663** | 100 nF ±10 %, 50 V X7R 0603 | Bypass LM393B; Vdc≤5,25 V; **rating:** 50 V; −55…125 °C nominales; C_min nominal 90 nF antes de DC/T/edad | **APROBADO (tensión/temperatura nominal)** | **PENDIENTE — BAJO**. Posición y retorno para comparador real; exigir evidencia capacitancia efectiva y ubicación. |

| **C15** | Yageo CC0603KRX7R9BB104 / **C14663** | 100 nF ±10 %, 50 V X7R 0603 | Filtro VREF; Vdc≤2,13 V; **rating:** 50 V; −55…125 °C nominales; C_min nominal 90 nF antes de DC/T/edad | **APROBADO (tensión/temperatura nominal)** | **PENDIENTE — BAJO**. τ = (15k||10k)×100nF =0,600 ms nominal; referencia tarda ~3ms en asentarse; exigir evidencia capacitancia efectiva y ubicación. |

| **C16** | Yageo CC0603KRX7R9BB224 / **C107083** | 220 nF ±10 %, 50 V X7R 0603 (cambio del original 100 nF) | Bypass INA180A1; recomendación TI 100 nF local; **rating:** 220nF inicial; min tolerancia 198nF; X7R ±15 % rango T | **APROBADO (valor nominal/tensión)** | **PENDIENTE — MEDIO**. Valor elegido 220 nF difiere de esquema histórico 100nF. Ceff≥100nF no demostrada: DC bias/edad/posición; confirmar aceptación del cambio. |

| **C17** | Fenghua 0603CG102J500NT / **C1636** | 1 nF ±5 %, 50 V C0G 0603 | VADC≤~3,35 V a VOUT=13,2 V y tolerancias; τ=0,75µs; **rating:** 50 V, C0G; variación muy baja frente a X7R | **APROBADO (tensión/estabilidad nominal)** | **PENDIENTE — MEDIO**. El filtro atenúa 10kHz solo 0,11 %; revisar adquisición ADC y seguridad frente a sobrevoltaje, independiente del rating del capacitor. |

### 3.3 Resistencias de compuerta, señal, protecciones y medición

| Ref. | Fabricante y MPN adoptado / JLC | Valor / presentación | Solicitud eléctrica y térmica calculada | Resultado parcial | Selección integral / falta cerrar |
|---|---|---|---|---|---|

| **R1** | UNI-ROYAL 0805W8F100JT5E / **C17415** | 10 Ω ±1 %, 0805; 0,125 W | ≈1,33 A pico ideal; ≈17,6 W pico; 13,2 mW de energía gate total; **rating:** Resistencias 0603: 0,1 W @70 °C, ≈0,082 W @85 °C; 0805 0,125 W (curva distinta según serie) | **PENDIENTE** | **PENDIENTE — ALTO**. Curva de pulsos repetitivos no contrastada; 13,2 mW es potencia total simplificada, no la que disipa necesariamente R1. |

| **R2** | UNI-ROYAL 0603WAF1002T5E / **C25804** | 10 kΩ ±1 %, 0603; 0,1 W | ≤1,333 mA; ≤17,60 mW; **rating:** Resistencias 0603: 0,1 W @70 °C, ≈0,082 W @85 °C; 0805 0,125 W (curva distinta según serie) | **APROBADO (CC)** | **PENDIENTE — ALTO**. Su descarga gate agrega consumo al bootstrap en cada ciclo; validar VBS. |

| **R3** | UNI-ROYAL 0603WAF1002T5E / **C25804** | 10 kΩ ±1 %, 0603; 0,1 W | ≤0,483 mA; ≤2,31 mW; **rating:** Resistencias 0603: 0,1 W @70 °C, ≈0,082 W @85 °C; 0805 0,125 W (curva distinta según serie) | **APROBADO (CC)** | **PENDIENTE — BAJO**. Revisión inyección hacia MCU apagado. |

| **R4** | UNI-ROYAL 0603WAF1001T5E / **C21190** | 1 kΩ ±1 %, 0603; 0,1 W | ≤5,303 mA; ≤27,84 mW; **rating:** Resistencias 0603: 0,1 W @70 °C, ≈0,082 W @85 °C; 0805 0,125 W (curva distinta según serie) | **APROBADO (CC)** | **PENDIENTE — MEDIO**. Corriente interfaz con MCU desconectado o sin alimentación. |

| **R5** | UNI-ROYAL 0603WAF1002T5E / **C25804** | 10 kΩ ±1 %, 0603; 0,1 W | ≤0,350 mA; ≤1,21 mW; **rating:** Resistencias 0603: 0,1 W @70 °C, ≈0,082 W @85 °C; 0805 0,125 W (curva distinta según serie) | **APROBADO (CC)** | **PENDIENTE — BAJO**. Pull-down RUN y estado arranque. |

| **R6** | UNI-ROYAL 0603WAF1002T5E / **C25804** | 10 kΩ ±1 %, 0603; 0,1 W | ≤0,350 mA; ≤1,21 mW; **rating:** Resistencias 0603: 0,1 W @70 °C, ≈0,082 W @85 °C; 0805 0,125 W (curva distinta según serie) | **APROBADO (CC)** | **PENDIENTE — BAJO**. Pull-down RESET y estado arranque. |

| **R7** | UNI-ROYAL 0603WAF4701T5E / **C23162** | 4,7 kΩ ±1 %, 0603; 0,1 W | ≤1,128 mA; ≤5,92 mW; **rating:** Resistencias 0603: 0,1 W @70 °C, ≈0,082 W @85 °C; 0805 0,125 W (curva distinta según serie) | **APROBADO (CC)** | **PENDIENTE — BAJO**. VOL salida open collector LM393B. |

| **R8** | UNI-ROYAL 0603WAF1502T5E / **C22809** | 15 kΩ ±1 %, 0603; 0,1 W | ≤0,214 mA; ≤0,679 mW; **rating:** Resistencias 0603: 0,1 W @70 °C, ≈0,082 W @85 °C; 0805 0,125 W (curva distinta según serie) | **APROBADO (CC)** | **PENDIENTE — MEDIO**. Umbral VREF influido por tolerancia y TCR pareja R8/R9. |

| **R9** | UNI-ROYAL 0603WAF1002T5E / **C25804** | 10 kΩ ±1 %, 0603; 0,1 W | ≤0,215 mA; ≤0,456 mW; **rating:** Resistencias 0603: 0,1 W @70 °C, ≈0,082 W @85 °C; 0805 0,125 W (curva distinta según serie) | **APROBADO (CC)** | **PENDIENTE — MEDIO**. Umbral VREF influido por tolerancia y TCR pareja R8/R9. |

| **R10** | Vishay CRCW060330K9FKEA / **C844354** | 30,9 kΩ ±1 %, 0603; 0,1 W (alternativa adoptada) | <0,33 mA; ≤3,3 mW a 13,2 V, ≈7,5mW a 20 V; **rating:** Resistencias 0603: 0,1 W @70 °C, ≈0,082 W @85 °C; 0805 0,125 W (curva distinta según serie) | **APROBADO (CC)** | **PENDIENTE — MEDIO**. Valor no es original 31kΩ; V_OVP nominal=8,18 V en vez de 8,20 V, diferencia 0,24 %; requiere aceptar funcionalmente cambio. |

| **R11** | UNI-ROYAL 0603WAF1002T5E / **C25804** | 10 kΩ ±1 %, 0603; 0,1 W | ≤0,330 mA; ≤1,08 mW a 13,2 V; **rating:** Resistencias 0603: 0,1 W @70 °C, ≈0,082 W @85 °C; 0805 0,125 W (curva distinta según serie) | **APROBADO (CC)** | **PENDIENTE — MEDIO**. Tolerancia/TCR y valor final R10 afectan umbral OVP. |

| **R12** | UNI-ROYAL 0603WAF1002T5E / **C25804** | 10 kΩ ±1 %, 0603; 0,1 W | ≤0,480 mA; ≤2,28 mW; **rating:** Resistencias 0603: 0,1 W @70 °C, ≈0,082 W @85 °C; 0805 0,125 W (curva distinta según serie) | **APROBADO (CC)** | **PENDIENTE — BAJO**. Corriente de base y pinout Q2 SMD. |

| **R13** | UNI-ROYAL 0603WAF1002T5E / **C25804** | 10 kΩ ±1 %, 0603; 0,1 W | ≤0,350 mA; ≤1,21 mW; **rating:** Resistencias 0603: 0,1 W @70 °C, ≈0,082 W @85 °C; 0805 0,125 W (curva distinta según serie) | **APROBADO (CC)** | **PENDIENTE — BAJO**. Pull-up NFAULT_MCU a 3,3 V, no a 5 V. |

| **R14** | UNI-ROYAL 0603WAF3001T5E / **C4211** | 3 kΩ ±1 %, 0603; 0,1 W | 33,3 mW a 13,2 V; ≈76,5 mW a 20 V; **rating:** Resistencias 0603: 0,1 W @70 °C, ≈0,082 W @85 °C; 0805 0,125 W (curva distinta según serie) | **APROBADO (CC ≤13,2V)** | **PENDIENTE — CRÍTICO**. A 20V la potencia equivalente continua casi agota derating; determinar energía de pulso. Además VSENSE≈5,0V pone en riesgo PA0. |

| **R15** | UNI-ROYAL 0603WAF1001T5E / **C21190** | 1 kΩ ±1 %, 0603; 0,1 W | 11,33 mW a 13,2 V; ≈26mW a 20 V; **rating:** Resistencias 0603: 0,1 W @70 °C, ≈0,082 W @85 °C; 0805 0,125 W (curva distinta según serie) | **APROBADO (CC)** | **PENDIENTE — CRÍTICO**. El componente soporta potencia, pero el divisor R14/R15 no protege el ADC en transitorios. |


## 4. Dictámenes por familia, comparación de alternativas y cambios a PCB

### Potencia

- **C1/C2 Panasonic 25SVPF100M:** elegidos frente a Nichicon EMZR250ARA101MF61G porque el EMZR declara solo 0,300 Arms a 100 kHz cada uno y el banco no cubre el caso de 0,632 A a 10 kHz con margen; los Panasonic sí tienen factor explícito a 10 kHz. La baja ESR @100 kHz no sustituye medir rizado. **Conservar selección**, cerrar C efectiva total ≥160 µF, polaridad y patrón E7.
- **C4/C5 Panasonic 50SVF10M:** elegidos frente al BXJ35V10UF05*05 (ESR 0,8 Ω por pieza @100 kHz y montaje wave): dos en paralelo implican 0,4 Ω de ESR nominal y exceden el objetivo de ESR banco ≤0,15 Ω del equipo. COT/PI debe validarse con nuevo perfil ESR. **Conservar selección condicional**.
- **L1/L2 Murata 60B334C:** mejores en catálogo que Bourns SRR1260-331K (I_rms 1,15 A, Isat típico 1,10 A, DCR hasta 0,58 Ω por pieza, ambos insuficientes). **No declarar aprobadas**: se necesita curva L(I,T) y ensayos a 1,47 Arms y ~2,5 A transitorios. Huella SMD Murata, no huella THT histórica.
- **RS1 TA-I 50 mΩ:** conserva magnitud y precisión, pero requiere cobre/land/derating. Alternativa conservadora Vishay **WSL2512R0500FEA/C413486**, 1 W y TCR ±75 ppm/°C, se estudiaría si el diseñador no puede justificar montaje TA-I. No sustituir sin actualizar presupuesto de protección.

### Alimentación y protección

- **C6/R2/C7:** no añadir C6A/C6B/C18 al netlist sin consentimiento. El diseñador debería **dejar espacio de reserva** para un bypass VCC adicional junto al driver y alternativa de bootstrap, dado que si más adelante falla el balance de carga habrá cambio de PCB.
- **C9/C10/C11 alrededor de UMW 78M05:** el circuito de aplicación del 78M05 utiliza 0,33 µF de entrada y 0,1 µF de salida nominales; C11 de 10 µF X5R se suma. No hay análisis de estabilidad/ESR y disipación real del regulador (no pasivo); **comprobarlo en el banco**. UMW TO-252 a 100 mA de carga + consumo interno puede disipar del orden de 0,8–0,9 W bajo la extensión de tensión; puede calentar pasivos vecinos.
- **C16 Yageo 220 nF:** se adopta como preferido para aportar margen al desacoplo INA180. El original era C16=100 nF: **debe aprobarse el cambio de valor**. La ficha TI muestra 100 nF local en su aplicación; ello no garantiza que 220 nF nominal mantenga 100 nF bajo sesgo/temperatura, aunque es más favorable que 100 nF sin reserva.
- **R10 30,9 kΩ:** la alternativa de una sola pieza **Vishay CRCW060330K9FKEA C844354** conserva footprint 0603, evita R10A+R10B y aproxima 31k. El umbral se modifica ligeramente; necesita aceptación formal.
- **R14/R15 + PA0:** **alerta de seguridad** independiente de que el chip de resistencia soporte su potencia. A sobrevoltaje de salida, el pin no acepta 5 V analógicos. Priorizar protección y medición de transitorios; no recomendar un zéner sin cálculo de su fuga, corriente, VDD apagado y dinámica ADC.
- **R1 gate:** curva/ensayo de energía por impulso repetitivo, 100 nC y VGS 13,2 V generan presupuesto máximo global 13,2 mW de carga gate a 10 kHz, pero no se puede calcular disipación real de R1 sin impedancia driver/gate y tiempos. **Pendiente**.
- **C17 filtro ADC:** 1 nF C0G es bueno para reproducibilidad; `Rth≈750 Ω`, `τ≈0,75µs`, `fc≈212 kHz`. Magnitud a 10 kHz ≈0,9989: no filtra sustancialmente rizado de salida. Verificar intervalo de adquisición del ADC y tratamiento digital, no atribuir al capacitor una protección contra sobrevoltaje.

## 5. Verificación de temperatura y criterios de aceptación

| Familia | Evidencia disponible | Límite comprobable | Qué impide aprobación final |
|---|---|---|---|
| UNI-ROYAL 0603 resistores | Rating de 100 mW / curva de derating 70–155 °C | 82,35 mW @85 °C de ambiente del resistor (interpolación familia); R4 27,84 mW, R2 17,60 mW, R14 33,33 mW @13,2 V | Temperatura real de PCB, pulso de R1 y R14, exactitud y tensión ADC |
| Murata 60B334C | DC current 4 A, DCR 80 mΩ y temperatura de aire −40…85 °C | Pcu ~0,217 W por pieza a 85 °C supuesta | Pcore, elevación térmica real y L(I,T) con un requisito mínimo más estricto que el criterio de 4 A |
| TA-I RLP25FEER050 | 2 W bajo condiciones especiales de 3oz/300mm² | P=0,316 W a ensayo 2,5 A, lejos del valor nominal listado | En PCB 1oz no se acredita disipación de 2 W; medir temperatura y validar Kelvin |
| Panasonic SVPF y SVF | Corriente corregida a f=10kHz y temperaturas hasta 105 °C | 2,24 A/pieza entrada, 1,75 A/pieza salida, superiores a exigidas | ESR a 10kHz, aumento térmico/vida, capacitancia efectiva y control |
| Cerámicos Yageo/Samsung | Tensión, encapsulado, tolerancia, familia X7R/X5R | Estructuralmente aptos por V nominal y clasificación térmica | Curvas MPN exacto de Ceff con VDC/T/edad; disposición física/regulador |
| C17 C0G | 1 nF, 50 V, ±5 % y dieléctrico de estabilidad alta | Margin nominal de tensión suficiente | Comportamiento de adquisición ADC y transitorios, no rating del cerámico |

**Térmica ≠ voltaje o potencia de catálogo:** para pasivos comunes la potencia calculada permite descartar riesgo evidente de sobrecarga en régimen; para bobina/shunt y elementos calientes el caso de 45 °C ambiente debe contrastarse con ensayo o curva térmica aplicable. Las fichas suelen dar rating a 70/105 °C bajo condiciones concretas, no predicción de temperatura dentro de una placa cualquiera.

## 6. Geometría/ensamblaje: advertencia al diseñador

- **Murata 60B334C:** cuerpo máximo 23,5×27×20 mm (orientación según dibujo); pad recomendado **3×14 mm** por terminal y dimensión indicada **20,8 mm**. Comprobar dibujo con orientación/rotación antes del land real; ninguna huella THT 25 mm / paso 10 mm lo reemplaza.
- **Panasonic SVPF E7:** diámetro 8 mm, altura 6,9 mm; KiCad `CP_Elec_8x6.9` geométricamente comparable al land Panasonic documentado. Confirmar pad1 positivo y banda negativa, y rotación para ensamblaje.
- **Panasonic SVF C6:** diámetro 6,3 mm y altura 5,9 mm; KiCad `CP_Elec_6.3x5.9` comparable con land C6 oficial. Igual control de polaridad.
- **Resistencias y MLCC 0603/0805:** tamaño genérico KiCad coincide en formato nominal, pero no constituye certificación de pad/cobre JLC o de que estén **ya colocados** en un PCB SMD más nuevo.
- **Shunt TA-I 2512:** formato de cuerpo 6,4×3,2 mm; su diseño térmico y 4 pistas Kelvin exige revisión real del cobre y pads, incluso si el símbolo usa dos terminales.

## 7. Acciones concretas, responsables y condición de cierre

| Prioridad | Acción sin necesidad de esperar otra BOM | Responsable sugerido | Cierre comprobable |
|---|---|---|---|
| **P0** | Informar incompatibilidad ADC 3k/1k; reservar protección | Diseñador PCB + responsable de protección | Simulación/cálculo transitorio documentado y V_PA0 dentro de rango al encendido/apagado |
| **P0** | Reservar huella alternativa de bootstrap y bulk driver; revisar D2 | Diseñador PCB + responsable pasivos | Hoja exacta C6 DC bias, caída D2, VBS/VGS mínima durante ON/recarga OFF y arranque |
| **P0** | Definir footprint y espacio para 2×Murata 60B334C | Diseñador PCB | Land recomendado y volumen libre; luego L(I,T) ≥528 µH total y temperatura/ruido aceptables |
| **P1** | Verificar disipación/kelvin y pads RS1 con espesor real cobre | Diseñador PCB + responsable pasivos | T resistor en peor caso y error de medición aceptables |
| **P1** | Aceptar R10 30,9k y C16 220nF como revisiones del valor original | Coordinación equipo | Nuevo valor/umbral documentado antes de emitir BOM de fabricación |
| **P1** | Cerrar Ceff de C4/C5, rizado y respuesta del PI | Responsable control / laboratorio | Medida o datasheet aplicable de Ceff≥16µF con ESR/temperatura y ensayos de escalones |
| **P2** | Confirmar proveedor JLC y geometría 0603/0805/fugas | Responsable pasivos | Comprobación de MPN/código, lote, clasificación/stock y dimensiones para pedido |
| **P2** | Validar R1 con perfil real gate y curva de pulsos | Responsable pasivos + laboratorio | Criterio energía/pulso repetitivo y T resistor adecuados |

## 8. Fuentes oficiales y fuentes comerciales de consulta

**Primarias:**

- [Murata Power Solutions, serie 6000B, ficha completa 3 páginas, contiene 60B334C](https://datasheet.lcsc.com/datasheet/pdf/270cd1d11a03508ca6429acbb65e165b.pdf?productCode=C6700033) (su URL lleva código de otra entrada comercial; **NO** atribuir `C6700033` al 60B334C).
- [Panasonic SVPF, pág. 2 — 25SVPF100M y factor 0,7](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000C177.pdf).
- [Panasonic SVF, pág. 2 — 50SVF10M y factor 0,7](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000C211.pdf).
- [TA-I RLP, pág. 4 — condiciones cobre 105 µm y 300 mm² para 2–3 W](https://www.tai.com.tw/files/uploads/Prod_spec/RLP.pdf).
- [Infineon IR2110 datasheet, págs. 1–3 — rango VBS/VCC, IQBS, UVLO](https://www.infineon.com/assets/row/public/documents/24/49/infineon-ir2110-datasheet-en.pdf).
- [TI INA180 datasheet, pág. 1 — ganancia y Cbypass=100 nF](https://www.ti.com/lit/ds/symlink/ina180.pdf).
- [UNI-ROYAL resistencias SMD, pág. 1 — derating por formato](https://www.royalohm.com/assets/pdf/products/smd/1.pdf).
- [ST STM32F103x8/xB, tablas de límites eléctricos y ADC](https://www.st.com/resource/en/datasheet/stm32f103v8.pdf).
- [Yageo CC0603KRX7R9BB104, datos MPN exacto](https://yageogroup.com/download/specsheet/CC0603KRX7R9BB104).
- [Yageo CC0603KRX7R9BB224, datos MPN exacto](https://yageogroup.com/download/specsheet/CC0603KRX7R9BB224).
- [Samsung CL21B105KBFNNN, serie y geometría; gráfica Ceff NO publicada en consulta](https://weblib.samsungsem.com/mlcc/mlcc-ec-data-sheet.do?partNumber=CL21B105KBFNNN).

**Comerciales, MPN-códigos cotejados puntualmente:** [RLP25FEER050 C160588](https://jlcpcb.com/partdetail/ta_iTech-RLP25FEER050/C160588), [Yageo 100nF C14663](https://jlcpcb.com/partdetail/YAGEO-YAGEOCC0603KRX7R9BB104/C14663), [Samsung 1µF C28323](https://jlcpcb.com/partdetail/C28323), [Samsung 10µF C15850](https://jlcpcb.com/partdetail/C15850), [UNI-ROYAL 10k C25804](https://jlcpcb.com/partdetail/C25804), [UNI-ROYAL 4,7k C23162](https://jlcpcb.com/partdetail/23889-0603WAF4701T5E/C23162), [Vishay 30,9k C844354](https://jlcpcb.com/partdetail/VishayIntertech-CRCW060330K9FKEA/C844354). El resto de códigos permanece **según fichero de candidatos**; disponibilidad y monto de pedido **no certificados en tiempo real**.

**Interpretación final:** los **valores eléctricos de la mayoría de las resistencias sí pasan** el cálculo estacionario y los **cuatro Panasonic pasan la corriente RMS** con márgenes importantes. No hay base para afirmar que la selección integral de las 35 referencias esté aprobada: los puntos decisivos son **ADC, bootstrap, inductancia bajo carga, curva térmica RS1 y C efectiva de salida**, además del montaje. El diseñador puede seguir con la PCB si **reserva espacios y adopta decisiones ahora**; no debería enviar Gerbers a fabricación sin cerrar los bloqueos de esta sección.
