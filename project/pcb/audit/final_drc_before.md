# DRC inicial de la PCB guardada

2026-10-27. Rama `Kicad-PCB`; proyecto vigente `project/pcb/redesign/buck.kicad_pcb`, guardado por el usuario a las 23:55:35 del 26-10. KiCad cerrado al iniciar modificaciones. KiCad 10.0.4 en Windows; sin generadores, cambio de rama, commits ni push.

Respaldo recuperable: `artifacts/pcb-final-20261026-235708/initial-cad.zip`; los 288 archivos CAD, bibliotecas y modelos se releyeron del ZIP y verificaron contra SHA-256 en `backup-manifest.json`. Los directorios `backup` y `backup-verified` son intentos incompletos y NO son el respaldo canónico.

Inventario inicial: 57 huellas, 246 elementos de ruteo; una zona GND en ambas caras, dos capas de cobre, espesor 1.6 mm. Caja de borde incluyendo línea: 105.60 × 80.35 mm; rectángulo nominal 105.55 × 80.30 mm. Inventario completo: `board-before.json`.

Ejecutado: `kicad-cli pcb drc project/pcb/redesign/buck.kicad_pcb --schematic-parity --refill-zones --severity-all --all-track-errors --format json --output <evidencia>/drc-before.json`. Relleno en memoria, sin guardar PCB.

Resultado: **5 errores, 5 advertencias, 0 exclusiones, 0 discrepancias de paridad**. Cuatro de los errores son conexiones incompletas. ERC: **0 errores, 2 advertencias** `isolated_pin_label` para UART_TX/UART_RX; no se excluyen.

| ID/tipo | Severidad | Objetos, redes y coordenadas mm | Causa probable | Solución propuesta | Riesgo |
|---|---|---|---|---|---|
| D01 `malformed_courtyard` | error | Footprint U6 @ (166.675001, 77.300001) | U6 contiene cruz central en F.CrtYd además del rectángulo cerrado | Mover solo la cruz central a F.Fab; conservar rectángulo y pads | Bajo, gráfico sin cobre |
| D02 `items_not_allowed` | warning | Via [HO] on F.Cu - B.Cu @ (148.8, 55.8) | HO cambia de capa mediante vía | Conservar y revisar inductancia/retorno del lazo de gate; no reenrutar sin aprobación | Cambio de topología: no aplicar |
| D03 `items_not_allowed` | warning | Via [HO] on F.Cu - B.Cu @ (157.45, 60.8) | HO cambia de capa mediante vía | Conservar y revisar inductancia/retorno del lazo de gate; no reenrutar sin aprobación | Cambio de topología: no aplicar |
| D04 `missing_courtyard` | warning | Footprint U5 @ (160.6, 72.4) | La huella de U5 carece de envolvente de ensamblaje acreditada | Documentar; requiere calificar land y cuerpo con ficha, sin inventar geometría | Mecánico pendiente |
| D05 `silk_overlap` | warning | Footprint text of U4 (*) @ (175.5368, 64.5322); Footprint text of U4 (*) @ (175.5368, 64.5322) | Dos marcadores de pin 1 superpuestos | Ocultar un duplicado manteniendo el otro marcador y los campos | Bajo, serigrafía |
| D06 `silk_overlap` | warning | Footprint text of U3 (*) @ (173.0132, 50.729); Footprint text of U3 (*) @ (173.0132, 50.729) | Dos marcadores de pin 1 superpuestos | Ocultar un duplicado manteniendo el otro marcador y los campos | Bajo, serigrafía |
| D07 `unconnected_items` | error | Pad 7 [GND] of U4 on F.Cu @ (166.215, 64.7862); Track [GND] on B.Cu, length 0.4243 mm @ (162.3, 66.95) | Pads o islas GND sin continuidad después de relleno | Escapes GND y vías locales a plano existente; verificar separación, paridad y continuidad con DRC | Local: no altera netlist; revisar retorno |
| D08 `unconnected_items` | error | Pad 2 [GND] of R6 on F.Cu @ (177.625, 66.4362); Zone [GND] on F.Cu and B.Cu, priority 0 @ (105.4, 31.45) | Pads o islas GND sin continuidad después de relleno | Escapes GND y vías locales a plano existente; verificar separación, paridad y continuidad con DRC | Local: no altera netlist; revisar retorno |
| D09 `unconnected_items` | error | Zone [GND] on F.Cu and B.Cu, priority 0 @ (105.4, 31.45); Pad 2 [GND] of C16 on F.Cu @ (183.25, 71.275) | Pads o islas GND sin continuidad después de relleno | Escapes GND y vías locales a plano existente; verificar separación, paridad y continuidad con DRC | Local: no altera netlist; revisar retorno |
| D10 `unconnected_items` | error | Zone [GND] on F.Cu and B.Cu, priority 0 @ (105.4, 31.45); Zone [GND] on F.Cu and B.Cu, priority 0 @ (105.4, 31.45) | Pads o islas GND sin continuidad después de relleno | Escapes GND y vías locales a plano existente; verificar separación, paridad y continuidad con DRC | Local: no altera netlist; revisar retorno |

## Reglas y exclusiones heredadas

Sin exclusiones DRC existentes. Comprobaciones ignoradas heredadas: `track_not_centered_on_via`, `tuning_profile_track_geometries`, `footprint_filters_mismatch`. ERC ignora de origen `single_global_label`, `four_way_junction`, `simulation_model_issue`, `footprint_filter`. Se mantienen visibles aquí; no se alterarán reglas ni severidades.

La regla local heredada permite un solo radio térmico aunque el mínimo global sea dos. No se cambió para obtener DRC limpio; revisar capacidad de retorno en potencia.

Antes de editar: no hay cortos reportados ni paridad discrepante. Esto no acredita encapsulados, tensiones ni funcionamiento. No se modificarán valores, netlist ni componentes críticos sin aprobación.
