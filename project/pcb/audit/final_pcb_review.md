# Revisión final de PCB Buck — 2026-10-27

**NO LIBERAR A FABRICACIÓN.** Limpieza gráfica terminada y tres escapes GND aplicados tras autorización humana. Quedan dos islas GND desconectadas y bloqueos eléctricos/mecánicos. No se promete funcionamiento ni se ha probado hardware.

## Estado y preservación

Proyecto vigente: `project/pcb/redesign/buck.kicad_pcb`, rama `Kicad-PCB`, Windows/PowerShell, KiCad **10.0.4**. Se identificó por el guardado del usuario a las 23:55:35 del 26-10, las bibliotecas y la interfaz NUCLEO actual; no se eligió por el nombre de carpeta. KiCad estaba cerrado al iniciar las correcciones. El repositorio ya tenía modificaciones y archivos sin seguimiento; se conservaron. No se ejecutaron generadores, commits, cambios de rama ni push.

Respaldo: [initial-cad.zip](../../../artifacts/pcb-final-20261026-235708/initial-cad.zip), **288 archivos**, comprobados releyendo cada entrada y comparando SHA-256. Incluye esquemáticos jerárquicos, proyectos, reglas, bibliotecas y modelos. [Manifiesto](final_review_evidence/backup-manifest.json). SHA-256 del ZIP: `471cc320bc2410afc24477f97e02a6c316692ab6a8131bb1e6373127b0c7a1ad`. Para recuperar, extraer primero a una carpeta separada y copiar únicamente los archivos elegidos con KiCad cerrado. Los intentos `backup`/`backup-verified` de artifacts son parciales; el ZIP es el respaldo canónico.

| Comprobación | Inicial | Final |
|---|---:|---:|
| DRC errores, incluidas conexiones incompletas | 5 | **2** |
| DRC advertencias | 5 | **3** |
| Paridad esquemático/PCB | 0 discrepancias | 0 discrepancias |
| Exclusiones DRC | 0 | 0 |
| ERC | 0 errores / 2 advertencias | 0 errores / 2 advertencias |
| Huellas / redes | 57 / 40 | 57 / 40 |
| Segmentos / vías / polígonos de cobre | 216 / 30 / 16 | 219 / 33 / 16 |

[Verificación por UUID y endpoints](final_review_evidence/verification.json): posiciones, rotaciones, geometría y redes de pads, las **246 pistas/vías originales** y todos los polígonos de cobre idénticos. Se añadieron exactamente tres pistas GND de 0,25 mm y tres vías de 0,80/0,40 mm autorizadas. Netlist antes/después idéntica en endpoints. No se eliminaron conexiones válidas; las desconexiones GND bajaron de cuatro a dos. Zonas existentes rellenadas y guardadas mediante KiCad. Esto acredita preservación CAD, no continuidad física.

El estado anterior a la autorización de cobre era 4 errores / 3 advertencias. Se creó un respaldo adicional en `artifacts/pcb-final-20261026-235708/ground-update/buck-before-ground.kicad_pcb` y se conservó la evidencia anterior en esa carpeta.

## Correcciones realizadas

- U6: dos líneas de la cruz central pasaron de `F.CrtYd` a `F.Fab`, conservando el rectángulo exterior cerrado. Misma corrección de dos líneas en la biblioteca local, sin modificar pads ni cuerpo.
- U3/U4: cada marcador de pin 1 duplicado pasó a `F.Fab` y quedó oculto; permanece un marcador de pin 1 en serigrafía.
- Se recolocaron referencias U3, U4, Q1, C1, C2, C4 y C5 fuera del cuerpo/pads. Se añadieron etiquetas VIN/GND, VOUT/GND y NUCLEO/USB externo en los conectores.
- Texto útil a **1 mm de altura y 0,15 mm de trazo**. Los textos ya eran mayoritariamente de ese tamaño; no se redujeron a un mínimo menos legible. Los valores estaban en `F.Fab`: no se borraron referencias, valores, MPN ni campos. Se conservaron polaridades, marca K y pin 1. `B.SilkS` no contenía texto útil que retirar.

DRC final sin infracciones de serigrafía. Se inspeccionaron [cara superior](../../../artifacts/pcb-final-20261026-235708/ground-update/top-final.png), [inferior](../../../artifacts/pcb-final-20261026-235708/ground-update/bottom-final.png) y la [3D previa a los escapes](../../../artifacts/pcb-final-20261026-235708/after-3d.png). No se movieron componentes. La placa conserva algunas líneas de huella de 0,12 mm: confirmar su reproducción, pues la guía estándar de JLCPCB pide trazos de 0,15 mm y altura de texto de 1 mm. No se confía en el recorte automático de fábrica. [Guía JLCPCB](https://jlcpcb.com/help/article/instructions-for-ordering).

## Pendientes DRC y propuesta local

Inventario original con coordenadas y causas: [final_drc_before.md](final_drc_before.md). Informes nativos completos en [evidencia](final_review_evidence/).

| Prioridad | Objeto | Resultado / acción propuesta, no aplicada |
|---|---|---|
| INFO | U4.7 GND, (166,215; 64,7862) mm | Corregido: escape lateral F.Cu a vía GND (165,0; 64,7862) mm. El candidato inicial invadía el pad; el lateral pasa DRC. |
| INFO | R6.2 GND, (177,625; 66,4362) mm | Corregido: escape y vía GND (177,625; 67,5) mm. Pull-down RESET con retorno CAD restaurado. |
| INFO | C16.2 GND, (183,25; 71,275) mm | Corregido: escape y vía GND (183,25; 72,5) mm. |
| BLOCKER | GND zona–zona: U3 | Isla F.Cu con U3.3/.5/.7/.9/.11/.13. Incluye la alimentación GND del HCT14. Caja X=175,1845…192,2245; Y=44,7261…54,8754 mm. Pendiente de conexión. |
| BLOCKER | GND zona–zona: ADC | Isla F.Cu con R15.2 y C17.2. Caja X=184,1883…190,6745; Y=66,23…77,9786 mm. El divisor carece de retorno y puede exponer PA0 a una tensión excesiva. Pendiente de conexión. |
| WARNING | HO, vías (148,8; 55,8) y (157,45; 60,8) mm | Mantener visibles los dos avisos; revisar lazo driver–gate–source y posible recorrido local alternativo. |
| WARNING | U5, (160,6; 72,4) mm | Courtyard ausente; calificar encapsulado/land y crear envolvente con dimensiones verificadas. |

Los tres escapes se aplicaron con pista **0,25 mm** y vía pasante **0,80/0,40 mm**, sin vía en pad. DRC confirma que los tres pads ya no aparecen desconectados, sin nuevas infracciones. Un análisis geométrico de colisiones de cobre encontró tres grupos GND: principal y las dos islas indicadas; coincide con dos conexiones pendientes en el ratsnest nativo. Evidencia: [ground-components.json](final_review_evidence/ground-components.json).

Propuesta adicional, aún no aplicada: escape desde U3.9 a vía (181,065; 43,8) mm y vía de cosido en la isla ADC en (188,7; 68,2) mm, ambas 0,80/0,40 mm. La segunda posición está dentro de la isla según la geometría rellena. Falta comprobar despejes y conexión mediante DRC con esas adiciones; no equivalen a una aprobación eléctrica.

La revisión automática rechazó la ejecución que añadía estas pistas/vías por interpretar que necesita aprobación de cambios eléctricos. Después el usuario autorizó expresamente los tres escapes, que ya están aplicados y validados; las dos islas adicionales solo se reevaluaron. No se modificaron reglas, anchos mínimos, clearances, exclusiones ni netlist. Se conservan las tres comprobaciones DRC ignoradas y las cuatro ERC ignoradas de origen, enumeradas en el informe inicial; un DRC futuro sin errores tampoco sustituiría su revisión.

## Auditoría eléctrica conjunta

| Prioridad | Área | Evidencia y decisión necesaria |
|---|---|---|
| INFO | Topología Buck | Q1.1=GATE, .2=VIN/drain, .3=SW/source; D1.1=SW/cátodo, .2=GND/ánodo. L1 SW–LMID, L2 LMID–IP, RS1 IP–VOUT, J2.1=VOUT/.2=GND. C1/C2 positivos VIN; C4/C5 positivos VOUT. Concuerda con netlist; comprobar marcas del componente comprado. Pinout IRFZ44N TO-220 confirmado en [Infineon](https://www.infineon.com/assets/row/public/documents/24/49/infineon-irfz44n-datasheet-en.pdf). |
| BLOCKER | L1/L2 | Candidato Murata **60B334C SMD** con huellas actuales THT `Inductor_25mm_P10mm_VERIFY`, paso 10 mm. Incompatibilidad pendiente de resolver; no se cambia huella sin aprobación. Catálogo oficial: envolvente de serie Ø23,5 × 27 × 20 mm, 330 µH/4 A/80 mΩ para esta referencia. Los círculos CAD de 25 mm no acreditan terminales ni volumen. [Murata, pág. 8](https://www.murata.com/-/media/webrenewal/support/library/catalog/products/power-products/power-magnetics.ashx?cvid=20260202011237000000&la=en-gb). |
| BLOCKER | Selección Q1/D2 | Q1 real en CAD **IRFZ44N TO-220**, candidato IRFZ44NS/C5199867 aún sin aprobar. D2 real **UF4004 DO-41**, candidato US1G/C3034075 bloqueado. No comprar candidatos SMD contra estas huellas THT. |
| BLOCKER | Kelvin RS1/INA180 | U6.IN+ deriva desde L2.2, antes de unos **11,75 mm de cobre de potencia de 2 mm** hasta RS1.1. Mide también caída de pista. U6.IN− llega por un polígono VOUT compartido, sin par Kelvin independiente desde RS1. Proponer tomas separadas en ambos terminales del shunt; requiere revisar ruteo. |
| BLOCKER | Bootstrap | C6 sí es **2,2 µF, CL31B225KBHNNNE, C50254, 1206**, entre BOOT/VB y SW/VS. D2 cátodo BOOT/ánodo VIN, R1 HO–GATE, R2 GATE–SW: coherentes. Pero el cálculo existente muestra techo de 9,9 V con VCC=10,8 V y VF supuesto=0,9 V, antes de descarga; no garantiza VBS≥10 V. Arranque con salida precargada y capacitancia efectiva siguen abiertos. Ver [cálculo específico](../redesign/bootstrap_validation.md) y [Samsung](https://product.samsungsem.com/mlcc/CL31B225KBHNNN.do). |
| BLOCKER | ADC / secuencia de fuentes | R14=15 kΩ VOUT–VSENSE; R15=2,2 kΩ a GND; J3.7 a PA0. Ganancia 0,127907: a 7/13,2/24 V produce nominalmente 0,895/1,688/3,070 V. No limita negativos, transitorios ni alimentación apagada. Con VREF bajo puede saturar. R3 a +5 V/R4 tampoco aíslan el PWM de un MCU apagado; riesgo inverso con Buck apagado. Elegir protección/aislamiento con límites de falla definidos. [Análisis existente](../redesign/adc_protection_review.md), [DS11451](https://www.st.com/resource/en/datasheet/stm32l432kc.pdf). |
| WARNING | Driver y lazo caliente | C3.VIN–Q1.D está a unos 5,3 mm entre pads; Q1.S–D1.K a 12,8 mm en línea recta, con mayor recorrido real. D1.A–C3.GND ronda 20 mm. La separación y retorno distribuido no constituyen un lazo compacto acreditado. Revisar sobretensiones/EMI sin recolocar automáticamente. |
| WARNING | Gate y desacoplos | HO tiene 14,91 mm de pista y dos vías; GATE incluye 9,12 mm a 0,20 mm frente al objetivo 0,50 mm. C6–VB mide 4,30 mm y D2–C6 5,325 mm. C7 está a ~7 mm de VCC del driver, con retorno por vías. Revisar inductancia y oscilación; no aprobar por frecuencia PWM baja. C16 está ~17,9 mm del centro de U6 y su GND ya se conectó: la distancia aún no acredita desacoplo local del INA180. |

U1 SOIC-16 conserva todos los pines: 1 LO sin uso, 2 COM=GND, 3 VCC=VIN, 4/5 NC, 6 VS=SW, 7 VB=BOOT, 8 HO, 9/10 NC, 11 VDD=+5V, 12 HIN, 13 SD, 14 LIN=GND, 15 VSS=GND, 16 NC. Correspondencia verificada contra la asignación SOIC, no la DIP-14. VBS debe respetar el rango recomendado de la ficha, independientemente del layout. [IR2110, págs. 2 y 5](https://www.infineon.com/assets/row/public/documents/24/49/infineon-ir2110-datasheet-en.pdf).

U6 usa pinout A: 1 OUT=ISENSE, 2 GND, 3 IN+=IP, 4 IN−=VOUT, 5 VS=+5V; ganancia A1=20 V/V. [TI INA180, pág. 4](https://www.ti.com/lit/ds/symlink/ina180.pdf). U5 LM393B: salidas 1/7 unidas en NTRIP con pull-up R7; entradas negativas ISENSE/OVSENSE y positivas VREF; alimentación 8/4. Con R8/R9=15k/10k, VREF nominal=2 V, Itrip nominal=2 A con RS1=50 mΩ y OVP nominal=8,18 V con R10/R11=30,9k/10k. Son valores nominales sin tolerancias completas, errores Kelvin ni tiempo máximo garantizado de corte. [TI LM393B](https://www.ti.com/lit/ds/symlink/lm393.pdf).

Lógica según netlist HCT00/HCT14: `NRESET=¬(RESET·NTRIP)`, `FAULT=¬(NTRIP·NFAULT)`, `NFAULT=¬(NRESET·FAULT)`, `SD=¬(RUN·NFAULT)`, `HIN=¬DPRIME`. RUN bajo mantiene SD alto; una falla NTRIP baja impide borrado por RESET. RESET es activo alto; no es NRST del MCU. El estado inicial del latch no está garantizado, pero RUN debe mantener apagado durante arranque. El retorno de R6 ya quedó conectado en CAD; el estado inicial del latch y la secuencia de fuentes siguen requiriendo ensayo. No se verificaron brownout, retardo ni funcionamiento transitorio en banco.

## NUCLEO y firmware

La interfaz vigente es **NUCLEO-L432KC externa**, no Blue Pill. J3: 1 UART_TX/PA9, 2 GND, 3 PWM/PA8, 4 RUN/PB0, 5 RESET/PB1, 6 NFAULT_MCU/PB7, 7 ADC/PA0, 8 GND, 9 NUC_3V3, 10 UART_RX/PA10. Coincide con `redesign/firmware_l432kc/main.c` y la escala de `calibration.h`; PA0 usa ADC1_IN5. Las carpetas antiguas F103 siguen existiendo: no utilizar su imagen para esta interfaz. Firmware actual conserva `BUCK_BOARD_REVIEWED=0`, RUN bloqueado y PWM complementario d′=1−d. No se compiló ni programó firmware durante esta auditoría.

J3 no une +5 V Buck con USB; NUC_3V3 solo alimenta el pull-up R13. GND común obligatorio; la separación de fuentes no resuelve alimentación por señales. Revisar SB17 abierto para PA0 y SB18 abierto para PB7, revisión física y arnés con pin 1. USART1 reservado no es el VCP ST-LINK de esta NUCLEO. [UM1956, tabla de conectores](https://www.st.com/resource/en/user_manual/dm00231744.pdf). J3 sigue sin MPN y cable definitivo.

## Cobre, retornos y térmica

Se inspeccionaron las once netclasses y sus asignaciones reales. Objetivos: VIN 3 mm; SW/LMID/IP/VOUT 2 mm; BOOT/HO/GATE y +5V 0,50 mm; NUC_3V3 0,35 mm; analógico/control 0,25 mm. Los anchos de clase no imponen mínimos universales: existen señales a 0,20 mm y el escape GATE citado. VIN se realiza mediante polígonos, por lo que la regla de ancho para objetos Track no detecta sus cuellos. El acceso a Q1.D tiene ~1,85 mm de altura local frente al objetivo de 3 mm; requiere revisión de sección efectiva, no solo lectura de netclass.

| Red | Pistas reales | Revisión |
|---|---|---|
| SW | 47,41 mm acumulados, 2 mm, sin vías | Incluye ramas a driver y L1; no es longitud única serie. Su extensión merece revisión EMI; DRC SW–analógico no detecta cercanía entre capas. |
| LMID | 24,45 mm, 2 mm | Tramo de potencia largo entre inductores. |
| IP | 28,69 mm acumulados, 2 mm | Incluye rama al INA180; toma de medida no Kelvin. |
| VOUT | Polígonos + 13,62 mm de pistas de 2 mm | Dos vías de 2/1 mm están en la rama de medida/OVP; no son una matriz acreditada de transferencia de potencia. |
| GND | Planos ambas caras, escapes 0,25 mm | 13 polígonos rellenos F.Cu y 4 B.Cu, no todos eléctricamente aislados entre sí; persisten dos islas desconectadas según DRC. Tres islas B.Cu pequeñas se concentran junto a J3. |

De las 33 vías, 21 son 0,80/0,40 mm, 10 son 0,60/0,30 mm y 2 son 2/1 mm. B.Cu mantiene gran área de retorno, interrumpida localmente por señales; no se acredita por ello un retorno pulsante de baja impedancia. La zona GND usa separación/térmico de 0,50 mm y radios de 0,50 mm, con regla heredada de un solo radio mínimo: revisar especialmente D1 y condensadores de entrada. No se cambió para aprobar DRC.

Presupuesto del proyecto: nominal 12→6 V/6 Ω, 1 A; caso de evaluación 1,47 A RMS y ~1,77 A pico, no límites garantizados de falla. Cálculo resistivo de sensibilidad a 55 °C, cobre de 30 µm y ancho efectivo 80%: LMID≈9,99 mΩ, caída≈14,7 mV a 1,47 A. El tramo IP compartido≈4,80 mΩ, equivalente a **9,6% de RS1 de 50 mΩ**, antes del resto de errores. Es cálculo algebraico, no extracción electromagnética ni medición. [Parámetros reproducibles](final_review_evidence/verification.json).

RS1 disipa nominalmente 0,05 W a 1 A, 0,108 W a 1,47 A y 0,313 W a 2,5 A; no se acredita energía de cortocircuito ni potencia nominal del MPN sin su land/derating. U2 lineal puede disipar 0,82 W con 13,2 V/100 mA, supuesto pendiente de presupuesto real. Para Q1, pérdidas de conmutación dependen del VGS y tiempos reales; para D1 faltan VF/temperatura/ciclo efectivo. Los planos no sustituyen térmica. Saturn 8.48 está instalado, pero el intento no produjo ventana controlable: **sin resultados Saturn, simulación térmica ni ensayos físicos**.

## Mecánica y fabricación

Dos capas, FR-4, **1,60 mm**, cobre modelado **35 µm por cara**, núcleo 1,51 mm, máscaras 0,01 mm; son configuración CAD, no stackup contratado. Contorno rectangular cerrado 105,55 × 80,30 mm; caja incluyendo trazo 105,60 × 80,35 mm. Acabado configurado `None`: decidir acabado de fabricación. Sin orificios de montaje; aprobar sujeción y retención de inductores antes del pedido.

DRC no reporta clearances, cortos, máscara, taladros, borde o courtyard solapado entre las reglas activas. Persisten U5 sin courtyard y las huellas provisionales. L1/L2 no tienen modelos reales en la vista 3D; no se verificó altura libre, fijación, acoplamiento magnético ni espacio de herramientas. Acceso J1/J2/J3 visible en CAD; el volumen real de cable, llave, tornillos y disipador está pendiente. Tab de Q1 está a VIN: cualquier disipador requiere analizar aislamiento/contacto.

Máscara y pasta se conservan como las define cada huella; vías tentadas en ambas caras. No se hizo CAM independiente ni inspección de stencil. No se acredita el land de RS1, Panasonic C1/C2/C4/C5, J1/J2 ni J3 solo por similitud del encapsulado. Deben conciliarse valores de ficha y campos: C4/C5 muestran 35 V mientras el candidato es 50SVF10M; no se cambió su valor.

Se generaron [BOM de revisión, 57 referencias](final_review_evidence/bom-review-only.csv) y [posiciones SMD, 41 referencias](final_review_evidence/positions-review-only.csv). No son archivos JLC aprobados: separar Candidate_MPN de MPN aprobado, cerrar códigos LCSC, agrupación y rotaciones/pin 1 contra librería de ensamblaje. Permanecen 16 referencias con taladros: L1/L2, Q1, D2, J1/J2/J3 y TP1–TP9. Montaje manual/THT debe definirse. No se exportaron Gerbers nuevos ni se realizó pedido.

## Acciones antes de JLCPCB

1. Los tres escapes autorizados ya pasan DRC. Autorizar y conectar las dos islas localizadas (U3 y ADC); repetir DRC completo con paridad y relleno, sin errores nuevos.
2. Elegir L1/L2, Q1, D2 y sus huellas físicas definitivas; aprobar cualquier cambio de ruteo necesario y land RS1. Completar courtyard U5.
3. Aprobar corrección Kelvin y revisión del lazo gate/retorno caliente/desacoplos. Verificar cobre, térmica y corrientes de falla con geometría definitiva.
4. Cerrar bootstrap, ADC y aislamiento de señales/secuencias de alimentación. No conectar potencia con la NUCLEO hasta cerrar estos bloqueos y plan de prueba.
5. Verificar arnés J3, puentes NUCLEO, polaridades, encapsulados, altura, fijación y posible disipador; revisar serigrafía de líneas finas.
6. Cerrar BOM/MPN/LCSC, componentes de montaje manual, stackup/acabado; exportar Gerbers, taladros, pasta y BOM/CPL definitivos desde el CAD aprobado. Inspeccionar CAM y orientación de ensamblaje antes de cualquier pedido.

## Actualización autorizada de GND

Tras la respuesta «si, adelante», se ejecutaron las tres adiciones descritas, relleno/guardado, DRC con paridad, ERC, exportación de netlist y vistas de ambas caras. Resultado: **2 errores GND, 3 advertencias DRC, 0 discrepancias; ERC 0 errores/2 advertencias**. No se modificaron los 246 elementos de ruteo originales, posiciones, pads, polígonos, netlist o reglas. El inventario actual es 219 segmentos y 33 vías. La comparación por UUID permite exclusivamente los seis objetos nuevos registrados en [authorized-changes.json](final_review_evidence/authorized-changes.json).

Los informes finales de esta ampliación están en `artifacts/pcb-final-20261026-235708/ground-update/drc-final.json`, `erc-final.json` y en las copias actualizadas de `final_review_evidence/`. La primera posición de vía U4 produjo una infracción de agujero a pad; se corrigió con el escape lateral documentado. La firma de `GetUnconnectedCount` requirió el parámetro booleano; la consulta corregida confirmó dos conexiones pendientes.

## Reproducción y límites de validación

Alcance de validación: completo para integridad CAD y reglas disponibles; incompleto para funcionamiento/térmica. Desde la raíz, PowerShell, salidas aisladas:

```powershell
$cli = 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
$out = 'artifacts/pcb-final-20261026-235708'
& $cli pcb drc project/pcb/redesign/buck.kicad_pcb --schematic-parity --refill-zones --severity-all --all-track-errors --format json --output "$out/drc-after.json"
& $cli sch erc project/pcb/redesign/buck.kicad_sch --severity-all --format json --output "$out/erc-after.json"
& $cli sch export netlist project/pcb/redesign/buck.kicad_sch --format kicadxml --output "$out/schematic-after.xml"
& $cli pcb export pos project/pcb/redesign/buck.kicad_pcb --format csv --units mm --smd-only --exclude-fp-th --exclude-dnp --output "$out/positions-review-only.csv"
& $cli pcb render project/pcb/redesign/buck.kicad_pcb --output "$out/after-3d.png" --rotate '35,0,35' --width 1600 --height 1200 --quality basic --background opaque
& 'C:/Program Files/KiCad/10.0/bin/python.exe' project/pcb/audit/final_review_evidence/verify_evidence.py
```

Estos comandos se ejecutaron; el relleno guardado se realizó adicionalmente con `--save-board` durante la corrección. Sin `--exit-code-violations`, el código 0 de CLI significa informe generado, **no reglas aprobadas**; los JSON determinan el resultado. No aparecieron errores ni advertencias finales nuevos respecto al inicio. Pruebas físicas, osciloscopio, SOA, inmunidad/EMI, térmica, estabilidad PI y CAM de producción: no realizadas.

Incidencias de herramientas: CLI inicialmente falló por acceso a configuración bajo sandbox; funcionó al ejecutarla con acceso autorizado. La primera lectura de vías invocó GetWidth sin capa y produjo una aserción, corregida antes de obtener el inventario. Un guardado de biblioteca devolvió None, interpretado inicialmente como fallo; se comprobó y luego se conservó el formato original con solo dos cambios de capa. La conversión SVG auxiliar no estuvo disponible; se usaron renders nativos KiCad y planos analíticos de cobre. La extracción PDF con pypdf emitió avisos fontTools y falló por AES; PyMuPDF instalado completó los 13 documentos, incluido el enunciado. El primer intento 3D con argumento `--rotate=` no fue compatible; la forma separada anterior sí terminó correctamente. No se ocultaron resultados de estas incidencias como éxitos.

Los únicos CAD modificados son la PCB vigente y `redesign/libraries/footprints/Buck_SMD.pretty/DBV0005A_N.kicad_mod`. Se añadieron este informe, el inventario inicial y `final_review_evidence/`; los intermedios y respaldo quedan en artifacts. El resto de los 288 archivos respaldados conserva su hash. La comprobación reproducible de preservación terminó en PASS. Se ejecutaron `git diff --stat`, `git diff --check` y `git status`; sin errores de whitespace. Git advierte conversión LF→CRLF en `project/pcb/buck.kicad_pro`, archivo previamente modificado por el usuario. Como `redesign/` y `audit/` ya estaban sin seguimiento, `git diff --stat` no incluye estos cambios; el alcance propio se acredita mediante hashes, sin añadir archivos al índice. **Pendiente de aprobación humana; no liberada.**
