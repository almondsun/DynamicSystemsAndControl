# Cambios de diseño ejecutados: revisión NUCLEO

**Revisión de esquemático coherente para revisión humana; NO habilitada para potencia/layout liberado.** Fecha2026-10-25. RamaKicad-PCB; KiCadCLI/SDK10.0.4. El proyecto vigente es [buck.kicad_pro](buck.kicad_pro), dentro de `project/pcb/redesign/`; no el proyecto homónimo de la revisión original.

Se inspeccionaron Git, bibliotecas y auditorías previas. El directorio ya tenía cambios locales del usuario; permanecen. Se guardó una copia completa preactualización en `artifacts/buck_nucleo_update_20261025/pre_update/` y hashes en `baseline.json`; `redesign/original/` sigue siendo el esquema histórico inicial. Los antiguos `assignment_report.md` y `component_mapping.md` quedan identificados como históricos, con enlace a este estado vigente.

## Tres grupos de actualización

1. **Bootstrap:** C6 de1µF0805 a2.2µF1206; MPN/código/fabricante/URL/Basic registrados. Se conserva conexiónVB−VS; validación eléctrica pendiente, con contraejemploVBS<10V al mínimoVIN.
2. **ADC:** R14/R15 de3k/1k a15k/2.2k; se mantiene la redVSENSE y C17=1nF. Ganancia0.1279069767. No se incorporaron clamps/switches aún; [análisis y alternativas](adc_protection_review.md).
3. **NUCLEO externa:** J3 actualizado, sin conexión5V/VIN, UART reservada y3.3 V solo haciaR13. [Cableado, alimentación y firmware separado](nucleo_l432kc_migration.md). Se conserva UUID/referencia, reemplazando símbolo y huella del conector.

Además, cambios nominales explícitamente aceptados por el usuario: **R10=30.9k**, VishayCRCW060330K9FKEA/C844354, y **C16=220nF**, YageoCC0603KRX7R9BB224/C107083. Ahora reciben huellas SMD 0603. La conectividad de todos esos pasivos permanece igual.

| Ref. | Valor anterior | Valor vigente | Footprint vigente |
| --- | --- | --- | --- |
| C6 | 1uF 50V X7R | 2.2uF 50V X7R 10% | Capacitor_SMD:C_1206_3216Metric |
| R10 | 31k 1% | 30.9k 1% | Resistor_SMD:R_0603_1608Metric |
| C16 | 100nF | 220nF 50V X7R 10% | Capacitor_SMD:C_0603_1608Metric |
| R14 | 3k 1% | 15k 1% | Resistor_SMD:R_0603_1608Metric |
| R15 | 1k 1% | 2.2k 1% | Resistor_SMD:R_0603_1608Metric |
| J3 | STM32 CABLE 2x5 | NUCLEO-L432KC EXT USB | Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical |

## Cambios menores: fundamento y alcance

[VishayD/CRCW20035rev.14-Apr-2026](https://www.vishay.com/docs/20035/dcrcwe3.pdf) identifica familia0603/1608; código30K9=30.9k, F=1%,KEApackaging. [C844354comercial](https://jlcpcb.com/partdetail/VishayIntertech-CRCW060330K9FKEA/C844354). El land genérico localR0603 conserva terminales1/2; revisión de soldadura pendiente.

VREF nominal2V yR11=10k: VOVP con 31k=8.20V;30.9k = **8.18V**, cambio−0.244%. No es límite garantizado de salida. ConV5±5% y1%independiente enR8/R9/R10/R11, el cálculo de umbral sinVos daaprox7.56–8.83V; offset/rango común/comportamiento transitorio delLM393B siguen pendientes.

[YageoMPNexacto](https://yageogroup.com/download/specsheet/CC0603KRX7R9BB224):220nF±10%,50V,X7R, cuerpo1.6×0.8mm nominal, compatible conhuella0603. Se inspeccionaron gráficasPDFpp.2–3: caída típica a5–5.25V del orden3–4%; ficha las identifica como **simulación típica, no especificación**. Con−10%tolerancia y−15%T quedan168.3nF antesDC/edad. Para≥100nF hace falta retención DC/edad≥59.42%. Un ejemplo prudente de95%DC y90%edad produce143.9nF; esos factores no son garantías de lote. **Hay margen orientativo; no se confirma un mínimo garantizado de100nF** sin curva garantizada/medición. Desacoplo INA180 sigue pendiente de localidad, lazoGND y medida. [TIINA180](https://www.ti.com/lit/ds/symlink/ina180.pdf) recomienda bypass0.1µF; no convierte220nFnominal en aprobación.

No se cambiaron L1/L2,Q1,D2,R2,R1,C7,C17 ni gananciasPIoriginales. Permanecen sus bloqueos anteriores. No se ejecutó ningún generadorCADprevio, commit, push, ruteo ni exportaciónGerber/CPL. El firmwareF103original no fue editado.

## Diferencias permitidas de conectividad

| Terminal | Antes | Después |
| --- | --- | --- |
| J3.9 | +3V3 | NUC_3V3 |
| R13.1 | +3V3 | NUC_3V3 |
| J3.10 | GND | UART_RX |
| J3.1 | +5V | UART_TX |

El renombrado`+3V3→NUC_3V3` conserva todos sus terminales físicos; no une una fuente nueva. SoloJ3.1 yJ3.10 se reasignan desde5V/GND aUART_TX/UART_RX. **57componentes,38→40redes**. Sin componentes ni pines añadidos o eliminados; referencias, UUID de instancia y pines, posiciones, cables y jerarquía conservados. Los nombres de pines de J3 se actualizan a su nueva función; ninguna otra correspondencia se inventa.

## Validaciones automáticas ejecutadas

Alcanceescalado: migraciónCAD/MCUconcontratoeléctrico. [Evidenciasactuales](validation/nucleo_update/validation_results.json), [comandosnativos](validation/nucleo_update/native_commands.json), [cálculos](validation/nucleo_update/calculations.json), [compilación](validation/nucleo_update/firmware_build_commands.json).

- NetlistsKiCadXML anterior y nueva exportadas y comparadas por terminal: solo diferenciaslistadas. [Anterior](validation/nucleo_update/before.net.xml), [nueva](redesign.net.xml).
- ERCantes:0violaciones. ERCdespués: **0errores y2avisos** de etiquetasUARTconectadas aunsolopin (reservasexternas). SalidaCLI5 por esosavisos; no se presenta comopass0. No se añadieron exclusiones ni se ocultaron avisos. Se mantienen reglasignoradas heredadas que limitan el alcance delERC.
-21huellasúnicas utilizadas existen y cargan conSDK10.0.4. Todos sus pines conectados tienen pad. Rutas3Ddeclaradas accesibles; no equivalen a validar montaje. C6/IDCsoncopiaslocalesnuevas; R10/C16 usanbibliotecaslocalesexistentes.
- Firmware L432 compilado/enlazado aCortexM4F; imagen con RUN inhibido, sin flash. Ensayos deperiféricos/PIreales NO ejecutados.
-273archivos originales protegidospor SHA-256 permanecen intactos, incluido F103; rama yestado Git fuera de rediseño conservados.
- PDFnuevo de5páginas exportado; revisiónvisual documentada trasrender. Los símbolos/landsse validan enCAD, no comoPCB fabricable.

Persistenstderr deHKCU/FontconfigdeKiCad; los primeros procesos paralelos también informaron creación de directorios ya existentes. No se suprimieron. No hubo fallo de cierre final. Las descargas directas ST fallaron por timeout; se trabajó con lectura oficial web y drivers ST locales. No se inventó resultado donde faltó medida/datasheet garantizado.

**Punto de parada de migración:** asignación, esquemático, firmware compilable ydocumentación preparados. Bootstrap, ADC y secuencia de fuentes siguen abiertos según[open_issues.md](open_issues.md). La tarea posterior de reglas PCB solo puede empezar después del cierre operativo de esta fase y comprobando que nadie edite estos archivos simultáneamente; no implica aceptar esos riesgos.
