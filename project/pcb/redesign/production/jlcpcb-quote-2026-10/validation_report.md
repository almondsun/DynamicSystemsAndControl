# Validación del paquete de cotización

**Estado: archivos reconciliados para una primera cotización parcial SMT; PENDIENTE DE REVISIÓN DE FABRICACIÓN.** No constituye aprobación eléctrica, térmica ni de funcionamiento. No se realizó pedido ni pago.

## Origen y protección

- Proyecto vigente: `project/pcb/redesign/buck.kicad_pro`, identificado por el proyecto abierto y la PCB guardada más reciente. Rama: `Kicad-PCB`; árbol Git con cambios previos del usuario, sin cambio de rama, commits, merges o push.
- Exportación: **2026-10-27 00:43, America/Bogota** (05:43 UTC), KiCad **10.0.4**, Windows, API Python y `kicad-cli` instalados.
- PCB de origen y copia exportada SHA-256: `b36ae24a2b7476bdffe4aea791b446df31d33e03d4c126b70946e8e1632c1835`. Esta huella identifica la revisión exacta; no se inventa un número de liberación.
- Los editores CAD estaban cerrados, sin cambios pendientes de guardar observados. Copia recuperable con CAD, esquemáticos jerárquicos, reglas, tablas y bibliotecas/modelos: `artifacts/jlcpcb-quote-20261027-004235/source/` desde la raíz del repositorio. Inventario SHA-256: `evidence/source_manifest.json`.
- Refill/guardado solo en copia aislada. Comparación de bytes de los originales y comparación de geometría de footprints/pads/pistas/vías aprobadas. La copia PCB final tiene el mismo SHA-256 que el original. **No se modificaron circuito, ruteo, posiciones, orientaciones, reglas ni exclusiones.** No se ejecutaron generadores antiguos.

## Método y geometría

JLCPCB Fabrication Toolkit está instalado (5.3.0); no se usó ni se afirma haber validado su flujo completo con KiCad 10. Se eligió el método reproducible nativo más conversión local. Scripts: `project/pcb/tools/export_jlc_quote.py` y `finalize_jlc_quote.py`; identidad comercial registrada en `jlc_quote_catalog.json`. Comandos, versiones, salidas y códigos de retorno en `evidence/commands.json`. Referencia de formato: [documentación oficial JLCPCB](https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad).

| Comprobación | Resultado |
|---|---|
| Capas / espesor | 2 / 1,6 mm; stackup CAD con 35 µm por cara |
| Contorno | Rectángulo cerrado, 105,55 × 81,05 mm medidos sobre línea central |
| Footprints / redes PCB | 57 / 40 |
| BOM | 24 grupos, 41 designators únicos |
| CPL | 41 designators únicos; todos en BOM y PCB/SCH |
| Ensamblaje SMT previsto | 41, todos en F.Cu |
| THT pendientes | 7; montaje manual confirmado: 0 |
| Pads de prueba sin componente | 9; DNP marcado en CAD: 0 |
| Componentes externos inventariados | 2: NUCLEO-L432KC y carga; sin posiciones inventadas |
| Taladros | 81 PTH, 0 NPTH; posición y diámetro reconciliados uno a uno |
| Cobre/máscara/pasta | Centros SMD presentes en Gerbers: 131/131/134 respectivamente |
| ZIP | Integridad CRC y contenido byte a byte comprobados; 12 archivos planos, sin BOM/CPL/Markdown |

Gerbers: F.Cu/B.Cu, F.Mask/B.Mask, F.Silkscreen/B.Silkscreen, F.Paste/B.Paste, Edge.Cuts, más job y Excellon PTH/NPTH. Las capas inferiores de pasta y serigrafía están vacías. No se incluyeron capas auxiliares. Se comprobaron terminadores, unidades mm, formato 4.6 y origen común de Gerbers. La comprobación Excellon respeta su resolución de 0,001 mm: tolerancia máxima de redondeo 0,0005 mm, sin alterar taladros CAD.

CPL procede directamente de posiciones nativas: X = X de KiCad; Y = −Y de KiCad; origen absoluto (0,0), igual al usado por Gerbers/Excellon. No hay espejado de componentes inferiores (no existen colocaciones inferiores). Se normalizan ángulos módulo 360 sin aplicar tablas genéricas de corrección JLC. **La orientación de máquina sigue pendiente del visualizador JLCPCB.**

## DRC/ERC reales

DRC antes y después de exportar: **0 errores, 0 conexiones pendientes, 0 discrepancias de paridad; 5 advertencias**. Zonas rellenadas en copia; salida completa `evidence/drc-export.json` y `drc-final.json`.

| Tipo | Objetos / coordenadas mm | Pendiente |
|---|---|---|
| items_not_allowed (2) | Vías HO (148,8;55,8), (157,45;60,8) | Revisar cambio de capa en lazo de gate |
| missing_courtyard | U5 (160,6;72,4) | Calificar land/courtyard de LM393 |
| silk_over_copper (2) | VOUT+ / J2.1 (199,95;105,2); GND− / J2.2 (204,95;105,2) | La máscara recorta textos; revisar legibilidad antes de fabricar |

ERC: **0 errores, 2 advertencias isolated_pin_label** sobre UART_TX y UART_RX, sin circuito interno adicional conectado. Son señales de interfaz reservadas; no se añadió conexión artificial. Ver `evidence/erc.json`.

Se conservaron las reglas ignoradas preexistentes; no se añadieron exclusiones. DRC ignora `track_not_centered_on_via`, `tuning_profile_track_geometries`, `footprint_filters_mismatch`. ERC ignora `single_global_label`, `four_way_junction`, `simulation_model_issue`, `footprint_filter`. Por ello cero errores corresponde al conjunto de reglas configurado, no a una revisión eléctrica completa. No se registraron violaciones excluidas adicionales en estos informes.

## Reconciliación comercial y pendientes

Inventario independiente PCB vs netlist recién exportada: mismas 57 referencias, valores y footprints. CSV reabiertos y comparados con las filas previstas; sin duplicados; conjuntos BOM/CPL idénticos; sin THT, DNP, pads virtuales ni componentes externos solicitados accidentalmente. Las 41 selecciones SMT tienen MPN/LCSC; tabla de identidad y fuentes primarias en `assembly_inventory.md` y `evidence/catalog_checks.json`. Se comprueba familia de encapsulado, **no aprobación dimensional completa de cada land**.

Selección actual preservada: C6 Samsung CL31B225KBHNNNE/C50254; R10 30,9 kΩ; C16 220 nF; divisor ADC R14/R15 15 kΩ/2,2 kΩ. No se copiaron códigos Candidate_LCSC antiguos a campos de selección.

- **BLOCKER para cotizar el conjunto completo:** L1/L2, Q1, D2, J1/J2 y J3 no tienen selección comercial final válida para las huellas THT actuales. L1/L2 son provisionales; sus candidatos SMD, el IRFZ44NS y US1G no corresponden a los footprints conservados. J3 tiene MPN TBD/código no seleccionado. Excluidos de BOM/CPL SMT y conservados en inventario. No se sustituyeron componentes.
- **BLOCKER para liberar fabricación:** todos los campos `Electrical_Approval` siguen pendientes. Lands personalizados, especialmente C1/C2/C4/C5, RS1 y U5, requieren calificación mecánica/datasheet. El DRC no valida bootstrap, márgenes ADC, pérdidas térmicas ni funcionamiento de protecciones; la auditoría eléctrica previa no queda cerrada por esta exportación.
- **WARNING:** stock para PCBA de todos los componentes **NO VERIFICADO**. Identidad de catálogo no equivale a disponibilidad por cantidad/modalidad/fecha. Confirmar detalle comercial de Q2 C20526 (rango 100–300), coste de fixture de U1 si el portal lo exige y asignación exacta de fabricante.
- **WARNING:** C4/C5 muestran 35 V en CAD frente al MPN seleccionado de 50 V; RS1 muestra 1 W frente al catálogo de 2 W. Diferencias registradas, sin editar valores ni reemplazar piezas.
- **WARNING:** comprobar visualmente pin 1 de U1–U6, D1, Q2, polaridad C1/C2/C4/C5 y todas las rotaciones en el portal. No se aplicó una corrección de máquina sin evidencia.

## Límites de la verificación

Se exportaron vistas nativas `evidence/front-native.svg` y `back-native.svg` para revisión. Se intentó abrir el ZIP en Gerber Viewer, pero la automatización del diálogo no permitió cargarlo de forma verificable: **revisión visual CAM del ZIP pendiente**, no presentada como realizada. Las pruebas programáticas de centros, contorno y taladros no constituyen una verificación visual completa de todas las regiones de cobre/máscara/pasta. No se validó simulación térmica, fabricación física, disponibilidad autenticada, visualizador de ensamblaje JLC, precio ni recepción de una placa.

Al cargar dos placas con la API Python, wx emitió avisos de manejadores de imagen duplicados; no hubo error de carga y las comparaciones finalizaron correctamente. Los avisos no se ocultaron.

## Repetir y verificar

Desde la raíz, PowerShell, usando Python instalado con KiCad:

```powershell
& 'C:/Program Files/KiCad/10.0/bin/python.exe' project/pcb/tools/export_jlc_quote.py --project project/pcb/redesign/buck.kicad_pro
$quoteOutput = (Get-Content artifacts/jlcpcb-quote-current.txt).Trim()
& 'C:/Program Files/KiCad/10.0/bin/python.exe' project/pcb/tools/finalize_jlc_quote.py $quoteOutput
```

Una nueva exportación crea otra revisión, sin sobrescribir esta entrega; reconstruye evidencias y CSV. Los documentos de revisión y checklist deben actualizarse si cambia el origen. La llamada DRC exacta se conserva en `evidence/commands.json`, con `--schematic-parity --refill-zones --save-board --severity-all --all-track-errors` sobre la copia aislada; ERC con `--severity-all`.

Hashes SHA-256 de los archivos principales se incluyen a continuación. `SHA256SUMS.txt` contiene además el hash de este informe y del resto del paquete, excepto el propio manifiesto, para evitar autorreferencia.

<!-- DELIVERY_HASHES -->

| Archivo | SHA-256 |
|---|---|
| gerbers.zip | `318e25ed9f3b5d3265a5b17a28c0ca4320406cbe7beec576aef80f8b7da9ff59` |
| bom_jlcpcb.csv | `23c777bbf4503e8b69a7b5ecb92868ce414984c9d36dde916570fa2b692c162c` |
| cpl_jlcpcb.csv | `5f9fca8f7c5a8bac5da65effe39db94408e37649fdfdeed9944032cb5f9910f6` |
| assembly_inventory.md | `c6c95b6db31e1ea19dbdf17fb143599b0ef26933ab07e434d4b5cc79a01f7eff` |
| quote_checklist.md | `89149f8f4759d9d435dbcdda22d43e0eae3157e4ac56a1595e72cc09930740ea` |
