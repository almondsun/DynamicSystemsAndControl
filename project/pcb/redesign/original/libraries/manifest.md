# Manifiesto de integración CAD Buck SMD

Fecha:2026-10-24. Rama comprobada: **Kicad-PCB**. Fuente real de descargas: `C:/Users/justa/Downloads`, accesible y enumerada (481 entradas en raíz). Se inspeccionaron15 ZIP pertinentes mediante CRC, límites de tamaño y comprobación de rutas, además de las bibliotecas locales previas. No se recorrieron instaladores/juegos ni se afirma una inspección de todas las carpetas personales. El estado Git inicial completo está preservado en `artifacts/buck_library_integration/baseline.json`.

## Resultado y significado de los estados

|Métrica|Cantidad|
|---|---:|
|Símbolos encontrados en los15 ZIP pertinentes|13|
|Archivos footprint encontrados, antes de reutilizar SOIC14|34|
|Nombres/variantes de footprint distintos, reutilizando SOIC14 compartido|31|
|Modelos3D únicos encontrados (13 miembros,10 hashes)|10|
|Símbolos registrados en Buck_SMD|9|
|Footprints registrados en Buck_SMD.pretty|25|
|Componentes/MPN con pareja símbolo–footprint accesible|9|
|Modelos almacenados en 3dmodels|6|
|Modelos únicos vinculados y visibles en prueba3D|5|
|PDF locales copiados, sin nuevas descargas|7|
|Conjuntos ZIP en revisión sin registrar|5|

**INTEGRADO** significa que el CAD está registrado, se carga y sus enlaces se resuelven; no aprobación eléctrica ni de fabricación. **PENDIENTE DE VALIDAR** identifica correspondencia comercial/geométrica no confirmada o un conjunto excluido. **INCOMPLETO** indica piezas de CAD faltantes. **NO ENCONTRADO** indica ausencia de CAD identificable para el MPN en el alcance inspeccionado. Que falte3D no bloquea símbolo/huella. Ningún candidato cambia de estado eléctrico por esta integración.

## Componentes accesibles desde KiCad

|Componente|MPN|Símbolo|Footprint|Modelo3D|Datasheet|Estado|
|---|---|---|---|---|---|---|
|C1/C2 alternativa|25SVF100M|`Buck_SMD:25SVF100M`|[`Buck_SMD:CAP_SVF_E7_PAN`](footprints/Buck_SMD.pretty/CAP_SVF_E7_PAN.kicad_mod)|[Panasonic_E7.stp](3dmodels/Panasonic_E7.stp)|[URL oficial](https://industrial.panasonic.com/ww/products/pt/os-con/models/25SVF100M) — PDF no encontrado localmente|INTEGRADO|
|C1/C2 alternativa|25SVPF100M|`Buck_SMD:25SVPF100M`|[`Buck_SMD:PCAP_SVP_E7_PAN`](footprints/Buck_SMD.pretty/PCAP_SVP_E7_PAN.kicad_mod)|[Panasonic_E7.stp](3dmodels/Panasonic_E7.stp)|[URL oficial](https://industrial.panasonic.com/ww/products/pt/os-con/models/25SVPF100M) — PDF no encontrado localmente|INTEGRADO|
|C4/C5 alternativa|50SVF10M|`Buck_SMD:50SVF10M`|[`Buck_SMD:CAP_SVF_C6_PAN`](footprints/Buck_SMD.pretty/CAP_SVF_C6_PAN.kicad_mod)|[Panasonic_C6.stp](3dmodels/Panasonic_C6.stp)|[URL oficial](https://industrial.panasonic.com/ww/products/pt/os-con/models/50SVF10M) — PDF no encontrado localmente|INTEGRADO|
|C4/C5 alternativa|50SVPF10M|`Buck_SMD:50SVPF10M`|[`Buck_SMD:PCAP_SVP_C6_PAN`](footprints/Buck_SMD.pretty/PCAP_SVP_C6_PAN.kicad_mod)|[Panasonic_C6.stp](3dmodels/Panasonic_C6.stp)|[URL oficial](https://industrial.panasonic.com/ww/products/pt/os-con/models/50SVPF10M) — PDF no encontrado localmente|INTEGRADO|
|U6|INA180A1IDBVR|`Buck_SMD:INA180A1IDBVR`|[`Buck_SMD:DBV0005A_N`](footprints/Buck_SMD.pretty/DBV0005A_N.kicad_mod)|[DBV0005A.stp](3dmodels/DBV0005A.stp)|[URL oficial](https://www.ti.com/lit/ds/symlink/ina180.pdf) — PDF no encontrado localmente|INTEGRADO|
|U5|LM393BIDR|`Buck_SMD:LM393BIDR`|[`Buck_SMD:D0008A-IPC_A`](footprints/Buck_SMD.pretty/D0008A-IPC_A.kicad_mod)|[D0008A.stp](3dmodels/D0008A.stp)|[URL oficial](https://www.ti.com/lit/ds/symlink/lm393.pdf) — PDF no encontrado localmente|INTEGRADO|
|U4|SN74HCT00DR|`Buck_SMD:SN74HCT00DR`|[`Buck_SMD:D14`](footprints/Buck_SMD.pretty/D14.kicad_mod)|[D0014A.stp](3dmodels/D0014A.stp)|[URL oficial](https://www.ti.com/lit/ds/symlink/sn74hct00.pdf) — PDF no encontrado localmente|INTEGRADO|
|U3|SN74HCT14DR|`Buck_SMD:SN74HCT14DR`|[`Buck_SMD:D14`](footprints/Buck_SMD.pretty/D14.kicad_mod)|[D0014A.stp](3dmodels/D0014A.stp)|[TI, PDF local](datasheets/TI_SN74HCT14.pdf)|INTEGRADO|
|RS1 alternativa|WSL2512R0500FEA|`Buck_SMD:WSL2512R0500FEA`|[`Buck_SMD:RES_2512_WSL`](footprints/Buck_SMD.pretty/RES_2512_WSL.kicad_mod)|NO ENCONTRADO; no bloqueante|[URL oficial](https://www.vishay.com/docs/30100/wsl.pdf) — PDF no encontrado localmente|INTEGRADO|

|MPN|Fabricante|JLC/LCSC histórico o candidato|Observación CAD pendiente|
|---|---|---|---|
|25SVF100M|Panasonic|C454370|Confirmar polaridad1+/2− contra dibujo y banda real; tipos eléctricos unspecified y representación alternativa conservados; mismo modelo de cuerpo compartido no garantiza intercambiabilidad comercial|
|25SVPF100M|Panasonic|C136279|Confirmar polaridad1+/2− contra dibujo y banda real; tipos eléctricos unspecified y representación alternativa conservados; mismo modelo de cuerpo compartido no garantiza intercambiabilidad comercial|
|50SVF10M|Panasonic|C454354|Confirmar polaridad1+/2− contra dibujo y banda real; tipos eléctricos unspecified y representación alternativa conservados; mismo modelo de cuerpo compartido no garantiza intercambiabilidad comercial|
|50SVPF10M|Panasonic|NO VERIFICADO|Confirmar polaridad1+/2− contra dibujo y banda real; tipos eléctricos unspecified y representación alternativa conservados; mismo modelo de cuerpo compartido no garantiza intercambiabilidad comercial|
|INA180A1IDBVR|Texas Instruments|C122228|Comparar land, dimensiones, orientación y variante de densidad con fabricante; aprobación eléctrica pendiente|
|LM393BIDR|Texas Instruments|C2865059|Las4 huellas no incluyen courtyard; entradas tri_state y salidas unspecified en símbolo de origen. Se conservan sin corrección; revisar ERC y pinout antes de uso eléctrico|
|SN74HCT00DR|Texas Instruments|C6764|Comparar land, dimensiones, orientación y variante de densidad con fabricante; aprobación eléctrica pendiente|
|SN74HCT14DR|Texas Instruments|C6769|Comparar land, dimensiones, orientación y variante de densidad con fabricante; aprobación eléctrica pendiente|
|WSL2512R0500FEA|Vishay Dale|C413486|Sin modelo3D; comprobar land y conexionesKelvin. CAD no cambia selección deRS1 ni presupuesto térmico/TCR|

Stock/clase comercial actual no investigados en esta tarea. Los códigos se transcriben de la auditoría; **no se marcan piezas disponibles ni seleccionadas definitivamente**. La presencia de cuatro opciones Panasonic no significa poblar cuatro piezas en lugar de las dos originales.

## Descargas incompatibles o no integradas

|Componente|MPN candidato|Símbolo|Footprint|Modelo3D|Datasheet|Estado|
|---|---|---|---|---|---|---|
|U1|IR2110STRPBF|IR2110SPBF, otro código|IR2110SPBF_INF yvariantes, sin asignar|IR2110STRPBF.step disponible sin vincular|Infineon_IR2110.pdf|INCOMPLETO|
|Q2|ChangjingMMBT3904/C20526|MMBT3904 deDiotec|TRANS_MMBT3904 deDiotec|MMBT3904.step deDiotec|Changjing_MMBT3904.pdf|PENDIENTE DE VALIDAR|
|D1|MDDSS34/C8678|SS34 con Reference=U|SMB_ONS, incompatible conSMA candidato|SMB_ONS.step|MDD_SS34.pdf|PENDIENTE DE VALIDAR|
|D2|ShunYeUS1G/C3034075|Descarga contieneCLD-Diode|P25_DO-214AC_SMA, no acreditada|do-214ac-sma.stp, sin vincular|Ficha oficial exacta no encontrada|PENDIENTE DE VALIDAR|
|J1/J2|TB002-500-02BE/C2757858|IntLibAltium; no KiCad|No nativoKiCad|Modelo previo en inventario; no asignado|URL del inventario, sin PDF local|INCOMPLETO|
|U2|UMW78M05/C347278|NO ENCONTRADO|NO ENCONTRADO|NO ENCONTRADO|UMW_78Mxx.pdf|NO ENCONTRADO|
|Q1|UMWIRFZ44NS/C5199867|NO ENCONTRADO|NO ENCONTRADO|NO ENCONTRADO|UMW_IRFZ44N_family.pdf|NO ENCONTRADO|

Las cinco carpetas de revisión son copias intactas de sus archivos; no se añadieron a las tablas.

- [IR2110SPBF](pending_review/IR2110SPBF/): MPN descargado SPBF distinto de candidato STRPBF. No se renombra ni se asigna por suposición; comprobar código de pedido y encapsulado.
- [MMBT3904](pending_review/MMBT3904/): MANUFACTURER=Diotec Semiconductor en el símbolo; candidato comercial Changjing/C20526. No se acredita identidad por el nombre MMBT3904.
- [SS34](pending_review/SS34/): Huella SMB_ONS y Reference=U; candidato MDD/C8678 es SMA. Fabricante/paquete no conciliados.
- [US1G](pending_review/US1G/): Símbolo real CLD-Diode (current limiting diode), no rectificador US1G. Huella contiene rutas absolutas F:/ y referencia a modelo no incluido con ese nombre.
- [TB002_500_02BE](pending_review/TB002_500_02BE/): Biblioteca Altium IntLib sin símbolo/footprint KiCad nativo; no se realiza conversión sin herramienta que conserve pines y geometría.

`IR2110SPBF` no se renombró artificialmente a`IR2110STRPBF`. El STEP del candidato exacto se conserva como archivo sin huella asociada. La coincidencia de pines entre dos códigos no se presume. En`US1G.zip` el nombre externo era engañoso: la función interna es un diodo limitador de corriente. Sus rutas absolutas originales permanecen solo dentro de la cuarentena no registrada; ninguna ruta activa depende de ese discoF:.

## Cobertura de los demás candidatos del inventario

La siguiente tabla conserva trazabilidad de las referencias sin parejaCAD nueva. Se basa en el inventario original, no reasigna componentes. Para los pasivos, la selección posterior y sus rechazos están en [requisitos](../audit/passives_requirements.md) y[candidatos](../audit/jlc_passives_candidates.md). No se copian huellas genéricas como si fueran entregables del fabricante.

|Referencias originales|MPN candidato del inventario|JLC/LCSC|Símbolo/footprint nativos nuevos|Estado|
|---|---|---|---|---|
|L1, L2|XR6826TS331MHL65|C22447628|NO ENCONTRADO para el MPN; bibliotecas originales/estándar no se reasignan|NO ENCONTRADO|
|C3, C7, C8, C10, C12, C13, C14, C15, C16|CC0603KRX7R9BB104|C14663|NO ENCONTRADO para el MPN; bibliotecas originales/estándar no se reasignan|NO ENCONTRADO|
|C6|CL21B105KBFNNNE|C28323|NO ENCONTRADO para el MPN; bibliotecas originales/estándar no se reasignan|NO ENCONTRADO|
|R1|0805W8F100JT5E|C17415|NO ENCONTRADO para el MPN; bibliotecas originales/estándar no se reasignan|NO ENCONTRADO|
|R2, R3, R5, R6, R9, R11, R12, R13|0603WAF1002T5E|C25804|NO ENCONTRADO para el MPN; bibliotecas originales/estándar no se reasignan|NO ENCONTRADO|
|C9|CL21B334KBFNNNE|C73142|NO ENCONTRADO para el MPN; bibliotecas originales/estándar no se reasignan|NO ENCONTRADO|
|C11|CL21A106KAYNNNE|C15850|Altium SchLib/PcbLib previo con MPN identificado; no convertido ni acreditado como KiCad|NO ENCONTRADO|
|R4, R15|0603WAF1001T5E|C21190|NO ENCONTRADO para el MPN; bibliotecas originales/estándar no se reasignan|NO ENCONTRADO|
|R7|0603WAF4701T5E|C23162|NO ENCONTRADO para el MPN; bibliotecas originales/estándar no se reasignan|NO ENCONTRADO|
|R8|0603WAF1502T5E|C22809|NO ENCONTRADO para el MPN; bibliotecas originales/estándar no se reasignan|NO ENCONTRADO|
|R10|31 kΩ exactos sin MPN;31.6 kΩ del inventario no asignable|NO VERIFICADO|NO ENCONTRADO para el MPN; bibliotecas originales/estándar no se reasignan|NO ENCONTRADO|
|R14|RC0603FR-073KL|C126358|NO ENCONTRADO para el MPN; bibliotecas originales/estándar no se reasignan|NO ENCONTRADO|
|C17|0603CG102J500NT|C1636|NO ENCONTRADO para el MPN; bibliotecas originales/estándar no se reasignan|NO ENCONTRADO|
|J3|61201021621|NO VERIFICADO|NO ENCONTRADO para el MPN; bibliotecas originales/estándar no se reasignan|NO ENCONTRADO|

TP1–TP9 son puntos de prueba y no requieren una compraMPN por defecto. LPS3015-152MRC/LPS3015-153MRC, NRF52840 yMCP73871 encontrados anteriormente son ajenos a la selección del Buck; no se registraron en Buck_SMD. Los cerámicos/resistencias sinCAD propio pueden estudiarse después para usar bibliotecas estándar, previa revisión; esta tarea no fabrica símbolos específicos ni declara equivalencia mecánica por valor.

## Huellas: variantes, pads y dimensiones comprobadas

Las dimensiones siguientes son la envolvente de pads de cobre derivada del archivo, **no dimensiones de cuerpo ni dimensiones aprobadas de fabricante**. Se inspeccionaron números, tipo, tamaño, coordenadas y capas de todos los pads en`integration_data.json`. Se preservaron geometría, contornos y marcas de pin1 del proveedor.

|Huella|MPN relacionados|Pads|Envolvente de pads X×Y (mm)|Courtyard|Silkscreen|Modelo|
|---|---|---|---|---|---|---|
|CAP_SVF_E7_PAN-L|25SVF100M|2|9.8044×1.1176|Sí|Sí|Panasonic_E7.stp|
|CAP_SVF_E7_PAN-M|25SVF100M|2|10.6172×1.3208|Sí|Sí|Panasonic_E7.stp|
|CAP_SVF_E7_PAN|25SVF100M|2|10.2108×1.2192|Sí|Sí|Panasonic_E7.stp|
|PCAP_SVP_E7_PAN-L|25SVPF100M|2|9.8044×1.1176|Sí|Sí|Panasonic_E7.stp|
|PCAP_SVP_E7_PAN-M|25SVPF100M|2|10.6172×1.3208|Sí|Sí|Panasonic_E7.stp|
|PCAP_SVP_E7_PAN|25SVPF100M|2|10.2108×1.2192|Sí|Sí|Panasonic_E7.stp|
|CAP_SVF_C6_PAN-L|50SVF10M|2|8.1026×1.1176|Sí|Sí|Panasonic_C6.stp|
|CAP_SVF_C6_PAN-M|50SVF10M|2|8.9154×1.3208|Sí|Sí|Panasonic_C6.stp|
|CAP_SVF_C6_PAN|50SVF10M|2|8.5090×1.2192|Sí|Sí|Panasonic_C6.stp|
|PCAP_SVP_C6_PAN-L|50SVPF10M|2|8.1026×1.1176|Sí|Sí|Panasonic_C6.stp|
|PCAP_SVP_C6_PAN-M|50SVPF10M|2|8.9154×1.3208|Sí|Sí|Panasonic_C6.stp|
|PCAP_SVP_C6_PAN|50SVPF10M|2|8.5090×1.2192|Sí|Sí|Panasonic_C6.stp|
|DBV0005A_L|INA180A1IDBVR|5|3.1000×2.7000|Sí|Sí|DBV0005A.stp|
|DBV0005A_M|INA180A1IDBVR|5|3.6000×3.1000|Sí|Sí|DBV0005A.stp|
|DBV0005A_N|INA180A1IDBVR|5|3.3500×2.9000|Sí|Sí|DBV0005A.stp|
|D0008A-IPC_A|LM393BIDR|8|7.2964×4.4321|NO: pendiente|Sí|D0008A.stp|
|D0008A-IPC_B|LM393BIDR|8|6.8964×4.3921|NO: pendiente|Sí|D0008A.stp|
|D0008A-IPC_C|LM393BIDR|8|6.4964×4.3521|NO: pendiente|Sí|D0008A.stp|
|D0008A-MFG|LM393BIDR|8|6.9500×4.4100|NO: pendiente|Sí|D0008A.stp|
|D14-L|SN74HCT00DR, SN74HCT14DR|14|6.5024×8.1280|Sí|Sí|D0014A.stp|
|D14-M|SN74HCT00DR, SN74HCT14DR|14|7.3152×8.1788|Sí|Sí|D0014A.stp|
|D14|SN74HCT00DR, SN74HCT14DR|14|6.9088×8.1788|Sí|Sí|D0014A.stp|
|RES_2512_WSL-L|WSL2512R0500FEA|2|6.9088×3.3782|Sí|Sí|Sinmodelo|
|RES_2512_WSL-M|WSL2512R0500FEA|2|7.7216×3.4798|Sí|Sí|Sinmodelo|
|RES_2512_WSL|WSL2512R0500FEA|2|7.3152×3.4290|Sí|Sí|Sinmodelo|

Todos los pads registrados sonSMD y usanF.Cu/F.Paste/F.Mask. Se cotejaron conjuntos de números pin/pad para las9 parejas; no se utiliza esa coincidencia como prueba suficiente de geometría o función. Las representaciones alternativas de capacitores y shunt repiten números en estilos diferentes: no se contabilizan como terminales físicos adicionales. LM393B tiene dos unidades.

## Modificaciones realizadas y procedencia

- Nueva biblioteca de símbolos fusionada: conserva números, nombres, tipos eléctricos, referencia, valor, unidades y dibujos. Solo se actualizan enlacesFootprint/Datasheet/filtros yse añaden metadatosMPN/fabricante/LCSC/estado.
- En variantes cuyo encabezado no coincidía con elnombre de archivo, se ajusta elnombre interno a ese archivo. Se documenta `header_renamed_to_match_variant_file`; no se modifica geometría. LosD14 deHCT00/HCT14 comparten geometría yse reutilizan en lugar de crear bibliotecas redundantes.
- Los modelos de cuerpoE7/C6 se deduplican por SHA-256. Los cinco vinculados usan escala1, offset0 yrotación0. Se revisaron visualmente sobre la placa temporal; no se certifican orientación de pin1 ausente en modelo, tolerancias dimensionales ni ajuste contra la pieza comprada.
- `sym-lib-table` y`fp-lib-table`: se conserva cada entrada anterior yse añade una sola`Buck_SMD`, con `${KIPRJMOD}`. No se cambian tablas globales.
- Nuevos documentos, metadatos ycomprobador de solo lectura. Ninguna asignación de componentes actuales se modifica.

Cada archivo copiado conserva hash del ZIP, miembro, hash original, destino y hash delresultado en[integration_data.json](integration_data.json). Los activos descargados permanecen locales, sin commit/push. Las licencias recibidas deSnapMagic se conservan con los conjuntos correspondientes en revisión; revisar derechos antes de redistribuir archivos de terceros.

## Validación ejecutada y límites

**Validation scope: escalated**, por importaciónCAD, formatos yregistro de bibliotecas. Se usó la habilidadbuild-validate para elegir pruebas enfocadas enbibliotecas, sin ejecutar generadores ni pruebas que reescriban el diseño.

|Prueba real|Resultado|
|---|---|
|Análisis S-expression de símbolos, footprints ytablas|Válido; una raíz por archivo|
|Nombres yURI registrados|Buck_SMD resuelve a archivos reales; entradas anteriores conservadas|
|Comparación pin/nombre/tipo/referencia/valor condescargas|Conservados en los 9 símbolos|
|EnlacesFootprint yfiltros de símbolo|Todas lasreferencias resuelven a las 25 huellas locales|
|Duplicados|Sin nombres duplicados; sinpares de geometría idéntica entrelas 25 huellas finales; modelos deduplicados porhash|
|KiCadPythonSDK10.0.4 FootprintLoad|25/25 cargadas; pads verificados|
|Placa temporal con 25 huellas|Guardada yreabierta con 25; no esPCB de potencia ni placa para fabricar|
|KiCadCLI sym upgrade --force sobre copia|Biblioteca leída y actualizada enartifacts; fuente integrada no sobrescrita|
|KiCadCLI sym export svg|15 SVG para 9 símbolos/unidades/estilos|
|KiCadCLI pcb export step|Ensamble temporal exportado, incluye los cinco modelos vinculados|
|KiCadCLI pcb render|Render3D visible después de redirigir caché; inspección visual realizada|
|Hash del diseño original y bibliotecas protegidas|12 archivos conservados; tablas locales son los únicos registrosCAD modificados|

Comandos de carga usados, ejecutados desde la raíz: `python project/pcb/libraries/validate.py`; `kicad-cli sym upgrade --force --output artifacts/buck_library_integration/native_validated.kicad_sym project/pcb/libraries/symbols/Buck_SMD.kicad_sym`; `kicad-cli sym export svg --output artifacts/buck_library_integration/symbol_previews --include-hidden-pins project/pcb/libraries/symbols/Buck_SMD.kicad_sym`. Para placa temporal se usóSDK (`native_validate.py`) y las órdenes`pcb export step`/`pcb render`, sinleer ni guardar laPCB original.

Los primeros intentos de render no mostraron modelos por falta de acceso a la caché de usuario. Se resolvió para la prueba con`KICAD_CONFIG_HOME`, `KICAD_DOCUMENTS_HOME` y`KICAD_CACHE_HOME` dentro de`artifacts/buck_library_integration/`. Esas variables se establecieron solo en los procesos de prueba; no se cambiaron preferencias globales. Persisten avisosHKCU de KiCadCLI, aunque las órdenes finales retornan0 ygeneran resultados válidos. Dos procesos de prueba se interrumpieron al bloquearse por acceso a Documentos sin entorno aislado. Un primer intento de importación detectó nombres internos repetidos; sus copias parciales se conservaron en`artifacts/buck_library_integration/partial_attempt1`, antes de reconstruir el nuevo directorio. No se borraron descargas.

[Render de la placa temporal](validation/temporary_assembly.png). Las primeras previsualizaciones sin modelos no se utilizan como evidencia de orientación. No hubo comprobación interactiva de los selectores enGUI; la accesibilidad se demuestra por tablas/rutas ylectura nativa, yel[README](README.md) indica cómo comprobarla personalmente. No se ejecutaron ERC/DRC del diseño original ni ensayos eléctricos.

## Revisión manual que permanece abierta

- [ ] MPN/fabricante/encapsulado deU1/Q2/D1/D2 yconversiónAltium: resolver antes de registrar sus archivos.
- [ ] Revisar tipos eléctricos delLM393B, courtyard de las4 variantes ycompatibilidad deland. Conservar sincorrección es una limitación documentada, no aprobación.
- [ ] Verificar dimensiones contra plano comercial exacto, marcas de pin1/polaridad yperfil de ensamblaje; conteo de pads/imagen3D no bastan.
- [ ] Completar símbolos/huellas faltantes paraU2/Q1 ypasivos sinCAD específico; no utilizar bibliotecas de otros MPN por similitud de nombre.
- [ ] Obtener PDF oficiales faltantes localmente si se necesita trabajar sin conexión; losURLs oficiales de los 9 símbolos sí están preservados.
- [ ] Cerrar requisitos eléctricos/térmicos en[open_issues.md](../audit/open_issues.md) antes de reemplazar componentes o diseñar layout.
