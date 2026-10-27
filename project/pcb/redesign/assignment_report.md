> **HISTÓRICO: estado anterior a la actualización NUCLEO.** Para valores, conectividad y decisiones vigentes consulte [design_changes.md](design_changes.md), [open_issues.md](open_issues.md) y [el informe de migración](nucleo_l432kc_migration.md). Las tablas siguientes preservan la trazabilidad anterior; no describen la revisión vigente.

# Informe de asignación SMD para revisión humana

Fecha: 2026-10-25. **REVISIÓN CAD; NO LIBERAR PARA FABRICACIÓN.**

Se preparó [buck.kicad_pro](buck.kicad_pro) y [buck.kicad_sch](buck.kicad_sch), con sus cuatro hojas subordinadas, sin PCB ni ruteo. Las asignaciones están en las instancias del esquemático, no en una placa. La [matriz previa](component_mapping.md) se escribió antes de editar símbolos e incluye los 57 componentes, MPN, códigos, clases, funciones y redes pin por pin. Fuentes principales copiadas sin cambios: [informe de pasivos](sources/verificacion_definitiva_candidatos_pasivos_buck_2026-10-25.md) y [matriz Excel](sources/matriz_verificacion_pasivos_buck_legible.xlsx), hoja Matriz, filas 2–36.

## Resultado de la migración

|Concepto|Cantidad|
|---|---:|
|Referencias físicas originales y nuevas|57|
|Asignadas a candidato SMD, incluidas provisionales|39|
|FOOTPRINT_ONLY (símbolo funcional conservado)|37|
|SYMBOL_REPLACEMENT|2|
|Campos Footprint efectivamente distintos|38|
|Sustituciones que requieren decisión/información humana|6|
|Conectores/puntos de prueba THT conservados, sin nueva selección SMD|12|
|Sin nueva asignación SMD, incluyendo esos J/TP|18|
|PENDING / BLOCKED|17 / 1|
|Pasivos asignados / pasivos con aprobación integral|31 / 0|

**39 asignaciones no equivalen a 39 piezas aprobadas.** Las 57 referencias siguen sometidas a revisión del conjunto; los 35 pasivos tienen selección integral pendiente según la fuente. RS1 ya usaba la misma huella 2512: se conservó esa geometría provisional y se documentó el candidato TA-I, por eso hay 39 asignaciones pero 38 cambios de campo Footprint.

Los seis casos sin sustitución nueva son **L1, L2, R10, C16, Q1 y D2**. Los 12 conservados por decisión de alcance son J1–J3 y TP1–TP9. No se interpreta un footprint histórico conservado como huella apta del nuevo candidato.

## Preparación y preservación

- Ruta local: `C:/dev/7mo/control/DynamicSystemsAndControl`; remoto `https://github.com/almondsun/DynamicSystemsAndControl.git`; rama `Kicad-PCB`, conservada.
- Git tenía cambios locales previos en esquemáticos, biblioteca Buck, proyecto, tablas, README y carpetas de auditoría/bibliotecas. Se tomó el estado real del directorio de trabajo; no se revirtió nada ni se usó HEAD para sustituirlo. Estado inicial y SHA-256 en `../../../artifacts/buck_smd_assignment_20261025/baseline.json`.
- Versión **ejecutada**: KiCad CLI y SDK **10.0.4** (el README histórico dice 10.0.6). Se usó el ejecutable de `C:/Program Files/KiCad/10.0/bin`.
- [original/](original/) conserva los cinco esquemáticos, proyecto, símbolos, tablas y bibliotecas de partida; [netlist original](original/original.net.xml). Son copias binarias de partida, salvo la netlist que es una exportación nativa. El PCB original se protegió por hash, no se importó a esta revisión.
- Todos los archivos activos de símbolos y footprints son locales a esta copia. Las huellas estándar utilizadas se copiaron con su nombre de biblioteca, licencia/atributos originales y geometría intacta. Solo se localizaron rutas 3D en las copias. [Procedencia](validation/applied.json).
- Las fuentes originales de Downloads no se modificaron. La comparación final de SHA-256 conserva **259 archivos preexistentes** del proyecto fuera de redesign, incluidos CAD, bibliotecas y documentos protegidos. No hubo commit, push ni cambio de rama.
- No se ejecutó `tools/generate.py`, el organizador de descargas ni generadores previos de CAD. Los scripts auxiliares nuevos solo escriben en redesign y en artifacts de esta revisión.

## Conectividad y símbolos

La comparación nativa cubre **57 referencias y 38 redes**. Se preservan nombres de redes, UUID de instancias y pines, referencias, posiciones, cableado, etiquetas, marcadores NC y estructura jerárquica. No se añadió ni eliminó ningún componente o pin del esquemático. **Cero diferencias funcionales no previstas.**

|Referencia / función|Original|Nuevo|Red conservada|
|---|---|---|---|
|Q2 base B|pin 2|pin 1|FB|
|Q2 emisor E|pin 1|pin 2|GND|
|Q2 colector C|pin 3|pin 3|NFAULT_MCU|

Esas dos diferencias numéricas están expresamente autorizadas por el mapeo de funciones. Se verificaron contra Changjing MMBT3904, ficha local p.1; no se usó como evidencia comercial el símbolo Diotec descargado. El adaptador `Buck_Redesign:MMBT3904_C20526` conserva los puntos de conexión de cada función, renumera los pines y conserva sus UUID. No se movieron cables.

C11 se reemplaza por `Buck_Redesign:CL21A106KAYNNNE`, un símbolo no polar adaptado del capacitor local. Se mantiene 10uF 25V, terminales 1/2 y sus redes +5V/GND; solo desaparece la indicación gráfica de polaridad. Pinout del capacitor cerámico no polar: terminales intercambiables.

**U1 merece revisión especial:** el original dice IR2110PBF DIP14 y apunta a DIP-14, pero ya tiene 16 pines y numeración funcional de SOIC16. La ficha Infineon rev.V p.5 lo confirma. Se conserva esa numeración real; se asigna SOIC-16W MS-013AA y se corrige el rótulo al candidato IR2110STRPBF. El número de pines del símbolo permanece 16; los pads de la huella pasan de **14 a 16**. No se reconstruyó el circuito suponiendo el pinout de un DIP14. La biblioteca descargada SPBF no se renombró ni se asignó ciegamente al código STRPBF.

U2 conserva 1 IN,2 GND,3 OUT; el tab TO-252 es pad2 GND, según la ficha UMW. U3/U4 conservan su numeración completa DIP/SOIC compatible. U5 conserva el símbolo local con entradas y salidas open_collector adecuadas; no se introducen los tipos tri_state/unspecified del CAD comercial. U6 conserva pinout A de INA180A1: 1 OUT,2 GND,3 IN+,4 IN-,5 VS. D1 conserva 1 cátodo/banda,2 ánodo y recibe SMA; no SMB. No hay otras diferencias de números de pads. El detalle por pin de todas las referencias está en la matriz.

Se actualizaron los rótulos MPN de U1–U5, D1 y Q2 para identificar los candidatos. `Original_Value` conserva sus rótulos anteriores. **No se cambió el campo Value de ningún pasivo.** R10 sigue **31k 1%**, C16 sigue **100nF**. Las propuestas 30.9k y 220nF no se aceptan ni se asignan como MPN activo. Los candidatos pendientes solo aparecen en campos `Candidate_*`.

## Tabla de asignación

Las filas no asignadas indican expresamente “candidato pendiente”; su campo Footprint permanece histórico. “Pinout documental” y “ERC” no son validación eléctrica del convertidor. Estado completo de aprobación y pendientes individuales en la matriz previa.

|Referencia|MPN|Símbolo|Footprint|Cambio realizado|Validación|Pendiente|
|---|---|---|---|---|---|---|
|C4|Panasonic 50SVF10M|Buck:C4|Buck_SMD:CAP_SVF_C6_PAN|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (rizado y tensión)|PENDIENTE — ALTO|
|RS1|TA-I RLP25FEER050|Buck:RS1|Resistor_SMD:R_2512_6332Metric|FOOTPRINT_ONLY; huella existente conservada, candidato documentado|Pinout / redes comprobados; APROBADO (potencia calculada, no térmica)|PENDIENTE — ALTO; huella provisional|
|J1|TB002-500-02BE (candidato pendiente; NO aplicado)|Buck:J1|TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal|PENDING|Sin sustitución; original preservado|Fuera de migración SMD segura: conservar conector/punto de prueba THT; MPN/montaje exacto no cerrado. Sin cambios.|
|D1|SS34|Buck:D1|Diode_SMD:D_SMA|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; Solo pinout documental; aptitud eléctrica pendiente|Revisión eléctrica y mecánica|
|L1|Murata 60B334C (candidato pendiente; NO aplicado)|Buck:L1|Buck:Inductor_25mm_P10mm_VERIFY|PENDING|Sin sustitución; original preservado|PENDIENTE — CRÍTICO|
|C1|Panasonic 25SVPF100M|Buck:C1|Buck_SMD:PCAP_SVP_E7_PAN|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (rizado y tensión)|PENDIENTE — MEDIO|
|C2|Panasonic 25SVPF100M|Buck:C2|Buck_SMD:PCAP_SVP_E7_PAN|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (rizado y tensión)|PENDIENTE — MEDIO|
|C3|Yageo CC0603KRX7R9BB104|Buck:C3|Capacitor_SMD:C_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (tensión/temperatura nominal)|PENDIENTE — BAJO|
|J2|TB002-500-02BE (candidato pendiente; NO aplicado)|Buck:J2|TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal|PENDING|Sin sustitución; original preservado|Fuera de migración SMD segura: conservar conector/punto de prueba THT; MPN/montaje exacto no cerrado. Sin cambios.|
|L2|Murata 60B334C (candidato pendiente; NO aplicado)|Buck:L2|Buck:Inductor_25mm_P10mm_VERIFY|PENDING|Sin sustitución; original preservado|PENDIENTE — CRÍTICO|
|C5|Panasonic 50SVF10M|Buck:C5|Buck_SMD:CAP_SVF_C6_PAN|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (rizado y tensión)|PENDIENTE — ALTO|
|Q1|IRFZ44NS (candidato pendiente; NO aplicado)|Buck:Q1|Package_TO_SOT_THT:TO-220-3_Vertical|PENDING|Sin sustitución; original preservado|Revisión/familia UMW y TO-263 pendientes de conciliar; se retiene original TO-220.|
|U1|IR2110STRPBF|Buck:U1|Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; Solo pinout documental; aptitud eléctrica pendiente|Revisión eléctrica y mecánica|
|R2|UNI-ROYAL 0603WAF1002T5E|Buck:R2|Resistor_SMD:R_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (CC)|PENDIENTE — ALTO|
|U2|78M05|Buck:U2|Package_TO_SOT_SMD:TO-252-2|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; Solo pinout documental; aptitud eléctrica pendiente|Revisión eléctrica y mecánica|
|D2|US1G (candidato pendiente; NO aplicado)|Buck:D2|Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal|BLOCKED|Sin sustitución; original preservado|Falta ficha exacta ShunYe US1G; CAD descargado es CLD-Diode, función incompatible. Reemplazo bloqueado.|
|R1|UNI-ROYAL 0805W8F100JT5E|Buck:R1|Resistor_SMD:R_0805_2012Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; PENDIENTE|PENDIENTE — ALTO|
|C11|Samsung CL21A106KAYNNNE|Buck_Redesign:CL21A106KAYNNNE|Capacitor_SMD:C_0805_2012Metric|SYMBOL_REPLACEMENT|Pinout / redes comprobados; APROBADO (tensión nominal)|PENDIENTE — MEDIO|
|C9|Samsung CL21B334KBFNNNE|Buck:C9|Capacitor_SMD:C_0805_2012Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (valor nominal/tensión)|PENDIENTE — MEDIO|
|R4|UNI-ROYAL 0603WAF1001T5E|Buck:R4|Resistor_SMD:R_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (CC)|PENDIENTE — MEDIO|
|R3|UNI-ROYAL 0603WAF1002T5E|Buck:R3|Resistor_SMD:R_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (CC)|PENDIENTE — BAJO|
|U3|SN74HCT14DR|Buck:U3|Buck_SMD:D14|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; Solo pinout documental; aptitud eléctrica pendiente|Revisión eléctrica y mecánica|
|C7|Yageo CC0603KRX7R9BB104|Buck:C7|Capacitor_SMD:C_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (tensión/temperatura nominal)|PENDIENTE — CRÍTICO; huella provisional|
|C12|Yageo CC0603KRX7R9BB104|Buck:C12|Capacitor_SMD:C_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (tensión/temperatura nominal)|PENDIENTE — BAJO|
|C6|Samsung CL21B105KBFNNNE|Buck:C6|Capacitor_SMD:C_0805_2012Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; PENDIENTE|PENDIENTE — CRÍTICO; huella provisional|
|C10|Yageo CC0603KRX7R9BB104|Buck:C10|Capacitor_SMD:C_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (tensión/temperatura nominal)|PENDIENTE — BAJO|
|C8|Yageo CC0603KRX7R9BB104|Buck:C8|Capacitor_SMD:C_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (tensión/temperatura nominal)|PENDIENTE — BAJO|
|C13|Yageo CC0603KRX7R9BB104|Buck:C13|Capacitor_SMD:C_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (tensión/temperatura nominal)|PENDIENTE — BAJO|
|R7|UNI-ROYAL 0603WAF4701T5E|Buck:R7|Resistor_SMD:R_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (CC)|PENDIENTE — BAJO|
|U6|INA180A1IDBVR|Buck:U6|Buck_SMD:DBV0005A_N|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; Solo pinout documental; aptitud eléctrica pendiente|Revisión eléctrica y mecánica|
|R8|UNI-ROYAL 0603WAF1502T5E|Buck:R8|Resistor_SMD:R_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (CC)|PENDIENTE — MEDIO|
|U4|SN74HCT00DR|Buck:U4|Buck_SMD:D14|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; Solo pinout documental; aptitud eléctrica pendiente|Revisión eléctrica y mecánica|
|R12|UNI-ROYAL 0603WAF1002T5E|Buck:R12|Resistor_SMD:R_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (CC)|PENDIENTE — BAJO|
|Q2|MMBT3904|Buck_Redesign:MMBT3904_C20526|Package_TO_SOT_SMD:SOT-23|SYMBOL_REPLACEMENT|Pinout / redes comprobados; Solo pinout documental; aptitud eléctrica pendiente|Revisión eléctrica y mecánica|
|R10|Vishay CRCW060330K9FKEA (candidato pendiente; NO aplicado)|Buck:R10|Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal|PENDING|Sin sustitución; original preservado|PENDIENTE — MEDIO|
|C16|Yageo CC0603KRX7R9BB224 (candidato pendiente; NO aplicado)|Buck:C16|Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm|PENDING|Sin sustitución; original preservado|PENDIENTE — MEDIO|
|U5|LM393BIDR|Buck:U5|Buck_SMD:D0008A-MFG|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; Solo pinout documental; aptitud eléctrica pendiente|Revisión eléctrica y mecánica; courtyard ausente|
|C15|Yageo CC0603KRX7R9BB104|Buck:C15|Capacitor_SMD:C_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (tensión/temperatura nominal)|PENDIENTE — BAJO|
|R13|UNI-ROYAL 0603WAF1002T5E|Buck:R13|Resistor_SMD:R_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (CC)|PENDIENTE — BAJO|
|R9|UNI-ROYAL 0603WAF1002T5E|Buck:R9|Resistor_SMD:R_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (CC)|PENDIENTE — MEDIO|
|R5|UNI-ROYAL 0603WAF1002T5E|Buck:R5|Resistor_SMD:R_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (CC)|PENDIENTE — BAJO|
|R11|UNI-ROYAL 0603WAF1002T5E|Buck:R11|Resistor_SMD:R_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (CC)|PENDIENTE — MEDIO|
|R6|UNI-ROYAL 0603WAF1002T5E|Buck:R6|Resistor_SMD:R_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (CC)|PENDIENTE — BAJO|
|C14|Yageo CC0603KRX7R9BB104|Buck:C14|Capacitor_SMD:C_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (tensión/temperatura nominal)|PENDIENTE — BAJO|
|TP5|No definido (candidato pendiente; NO aplicado)|Buck:TP5|TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm|PENDING|Sin sustitución; original preservado|Fuera de migración SMD segura: conservar conector/punto de prueba THT; MPN/montaje exacto no cerrado. Sin cambios.|
|R14|UNI-ROYAL 0603WAF3001T5E|Buck:R14|Resistor_SMD:R_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (CC ≤13,2V)|PENDIENTE — CRÍTICO; huella provisional|
|TP9|No definido (candidato pendiente; NO aplicado)|Buck:TP9|TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm|PENDING|Sin sustitución; original preservado|Fuera de migración SMD segura: conservar conector/punto de prueba THT; MPN/montaje exacto no cerrado. Sin cambios.|
|TP3|No definido (candidato pendiente; NO aplicado)|Buck:TP3|TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm|PENDING|Sin sustitución; original preservado|Fuera de migración SMD segura: conservar conector/punto de prueba THT; MPN/montaje exacto no cerrado. Sin cambios.|
|TP2|No definido (candidato pendiente; NO aplicado)|Buck:TP2|TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm|PENDING|Sin sustitución; original preservado|Fuera de migración SMD segura: conservar conector/punto de prueba THT; MPN/montaje exacto no cerrado. Sin cambios.|
|TP1|No definido (candidato pendiente; NO aplicado)|Buck:TP1|TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm|PENDING|Sin sustitución; original preservado|Fuera de migración SMD segura: conservar conector/punto de prueba THT; MPN/montaje exacto no cerrado. Sin cambios.|
|TP6|No definido (candidato pendiente; NO aplicado)|Buck:TP6|TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm|PENDING|Sin sustitución; original preservado|Fuera de migración SMD segura: conservar conector/punto de prueba THT; MPN/montaje exacto no cerrado. Sin cambios.|
|R15|UNI-ROYAL 0603WAF1001T5E|Buck:R15|Resistor_SMD:R_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (CC)|PENDIENTE — CRÍTICO; huella provisional|
|TP7|No definido (candidato pendiente; NO aplicado)|Buck:TP7|TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm|PENDING|Sin sustitución; original preservado|Fuera de migración SMD segura: conservar conector/punto de prueba THT; MPN/montaje exacto no cerrado. Sin cambios.|
|TP8|No definido (candidato pendiente; NO aplicado)|Buck:TP8|TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm|PENDING|Sin sustitución; original preservado|Fuera de migración SMD segura: conservar conector/punto de prueba THT; MPN/montaje exacto no cerrado. Sin cambios.|
|C17|Fenghua 0603CG102J500NT|Buck:C17|Capacitor_SMD:C_0603_1608Metric|FOOTPRINT_ONLY; huella y metadatos MPN|Pinout / redes comprobados; APROBADO (tensión/estabilidad nominal)|PENDIENTE — MEDIO|
|J3|61201021621 (candidato pendiente; NO aplicado)|Buck:J3|Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical|PENDING|Sin sustitución; original preservado|Fuera de migración SMD segura: conservar conector/punto de prueba THT; MPN/montaje exacto no cerrado. Sin cambios.|
|TP4|No definido (candidato pendiente; NO aplicado)|Buck:TP4|TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm|PENDING|Sin sustitución; original preservado|Fuera de migración SMD segura: conservar conector/punto de prueba THT; MPN/montaje exacto no cerrado. Sin cambios.|

## Verificaciones automáticas ejecutadas

**Validation scope: escalated**, por migración CAD con contratos de conectividad. Comandos exactos, stdout, stderr y códigos en [native_commands.json](validation/native_commands.json). Se aislaron `KICAD_CONFIG_HOME`, `KICAD_DOCUMENTS_HOME`, `KICAD_CACHE_HOME` bajo artifacts/config; no se cambiaron preferencias globales.

|Prueba real|Resultado|
|---|---|
|CLI `version`|10.0.4, salida0|
|`sch export netlist --format kicadxml` original y nuevo|Exportaciones válidas; 57 componentes/38 redes|
|`sch erc --format json --severity-all --exit-code-violations` original completo y nuevo|Ambos salida0, 0 violaciones|
|Comparación numérica de redes|Solo FB y GND cambian el número de pin de Q2 según tabla|
|Comparación funcional tras normalizar B/E de Q2|Sin diferencias|
|Comparación AST de cables/etiquetas/jerarquía y UUID|Preservados|
|Comparación de valores pasivos|35 sin cambios|
|Existencia de footprints / carga SDK `pcbnew.FootprintLoad`|22 huellas únicas presentes y cargadas; pads numerados y de tamaño positivo|
|Pines de símbolo frente a pads|Todos los pines tienen pad correspondiente; solo U1 cambia de huella14 a16|
|Geometría de huellas estándar copiadas|AST idéntico excluyendo únicamente rutas model3D|
|Rutas 3D declaradas en huellas utilizadas|20 rutas, todas accesibles en la copia|
|`sch export pdf`|Salida0, PDF5 páginas; renderizadas e inspeccionadas|
|Preservación de originales y rama|259 SHA-256 sin cambios; Kicad-PCB conservada|

Se leyeron las tablas de funciones de fabricante para los semiconductores asignados y se contrastó la numeración con los símbolos/pads. Para resistores/MLCC se usó MPN y tamaño 0603/0805/2512, no solo dos pads; terminales no polarizados. Para Panasonic se emplearon los lands comerciales identificados E7/C6, conservando pad1 positivo y pad2 negativo. Esto no certifica tolerancias de ensamblaje, rotación de pick-and-place o proceso de soldadura.

El ERC conserva la configuración heredada: están ignorados `single_global_label`, `four_way_junction`, `simulation_model_issue` y `footprint_filter`. No se añadieron exclusiones ni se cambiaron tipos eléctricos para reducir errores. Persisten tipos originales discutibles, como LIN de U1 declarado power_in y alimentaciones de U3 como input; no se corrigieron fuera del alcance. **ERC limpio no constituye aprobación eléctrica.**

Los primeros intentos de CLI sin entorno completo dieron errores de acceso a Documents. El primer ERC de la copia original incompleta informó dos bibliotecas Buck ausentes; al copiar también sus bibliotecas, el ERC de referencia correcto resultó cero. Estos intentos no se presentan como errores eléctricos corregidos. Los logs originales permanecen en artifacts.

Las ejecuciones finales conservan en stderr avisos de acceso a registro `HKCU\Software\kicad-cli` y de caché Fontconfig no escribible. No se suprimieron. Las exportaciones son válidas y se inspeccionó el PDF; no se observó fallo de cierre en las ejecuciones finales. Poppler también emitió avisos de fuentes al leer algunas fichas antiguas, registrados en la sesión.

La revisión visual de las cinco páginas confirma símbolos y rótulos nuevos, C11 sin signo positivo, y Q2 con E2/B1. Se mantiene la composición original. Hay detalles gráficos heredados en PWR_FLAG y texto inferior de J3 que conviene revisar a mayor zoom; no se alteraron para preservar el esquema. El PDF no aporta validación de posicionamiento/ruteo de PCB.

## Verificación eléctrica y mecánica pendiente

- **L1/L2:** no hay huella Murata acreditada. Se conserva la histórica THT como NO MIGRADA; nunca usarla para 60B334C. Hace falta land específico/orientación, volumen 23.5×27×20mm, L(I,T), pérdidas y acoplamiento.
- **R10/C16:** aceptar o rechazar expresamente 30.9k/220nF; hasta entonces permanecen 31k/100nF sin nueva asignación.
- **Q1:** conciliar revisión UMW IRFZ44N/NS y TO-263 antes de migrar. **D2:** recuperar ficha exacta ShunYe; CAD CLD-Diode incompatible, bloqueado.
- **C6/C7:** huellas genéricas 0805/0603 claramente provisionales; cerrar C efectiva, recarga, arranque y VBS/VGS. No se añadieron C6A/C6B/C18 ni redes nuevas.
- **R14/R15:** 0603 provisional; permanece bloqueo de interfaz ADC por transitorios/sobretensión y secuencia de alimentación. No se añadió protección ni se ajustó divisor.
- **RS1:** 2512 provisional conserva huella previa, no reproduce el land TA-I recomendado (a4.0,b2.1,L4.1mm). Validar Kelvin desde pads, cobre35µm frente a condiciones105µm/300mm², derating y temperatura; no atribuir 2W al montaje actual.
- **C1/C2 y C4/C5:** revisión mecánica de E7/C6, pad1+/banda-, altura, stencil y rotación. ESR10kHz, C efectiva, vida y respuesta PI siguen pendientes. C4/C5 conservan rótulo histórico35V aunque el MPN candidato es50V; esa diferencia de rating/tecnología queda documentada, sin alterar su capacitancia10uF.
- **C11:** estabilidad/ESR con regulador UMW, DC bias y temperatura del X5R pendientes. **R1:** pulsos repetitivos, no solo potencia promedio. Otros MLCC: C efectiva y colocación; otros resistores: temperatura, exactitud y pulsos según matriz.
- **U1–U6, D1, Q2:** aptitud de alimentación, lógica, transitorios, disipación y respuesta real del circuito sin validar. U5 tiene huella comercial sin courtyard; comprobar o completar en la futura fase mecánica. No se hizo simulación nueva ni ensayo físico.
- Dos huellas utilizadas no declaran modelo3D: inductor provisional Buck y testpoint THT; no hay rutas rotas que sustituir. Los modelos presentes son ayuda visual; alineación, escala, orientación, despejes y correspondencia con fabricante necesitan aprobación mecánica. No se generó una vista3D de PCB ni montaje final.

Se conserva el contexto docente de 12V y10kHz, dos330µH en serie, salida20µF nominal y carga externa6Ω. Esta fase no elige ecuaciones ni parámetros nuevos. No hay solver/condiciones iniciales nuevos: no se ejecutó simulación temporal. Se espera conservar la conectividad funcional del original, no se afirma respuesta dinámica equivalente tras cambiar ESR/tecnología hasta ensayar los candidatos.

## Evidencia y punto de parada

- [Resultados estructurados](validation/validation_results.json), [pads originales/nuevos](validation/pad_count_changes.json), [carga nativa de huellas](validation/native_footprints.json), [ERC original completo](validation/original_erc_complete.json) y [ERC nuevo](validation/redesign_erc.json).
- [Netlist nueva](redesign.net.xml), [netlist original](original/original.net.xml), [PDF de revisión](schematic_review.pdf), [matriz previa](component_mapping.md).
- Auxiliares y renders en `../../../artifacts/buck_smd_assignment_20261025/`; scripts nuevos `prepare.py`, `plan_assignment.py`, `apply_assignment.py`, `run_native.py`, `check_assignment.py`, `native_footprints.py`, `write_report.py`. `prepare.py`/`apply_assignment.py` tienen guardas y no deben repetirse sobre una revisión existente.

**Trabajo detenido tras asignación y validación documental.** No se creó PCB, ruteo, Gerbers ni CPL; no se autoriza fabricación ni se cierra la selección integral de pasivos. La siguiente etapa requiere revisión humana de esta copia y decisiones sobre los puntos anteriores.
