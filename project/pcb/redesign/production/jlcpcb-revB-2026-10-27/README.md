# Paquete JLCPCB — Buck Rev B (2026-10-27)

**Prototipo pendiente de puesta en marcha. No pagar hasta cerrar los bloqueos del [informe Rev B](../../revB_release_report.md#7-bloqueos-y-decisiones-pendientes-no-son-aprobaciones-condicionadas).** Nada se ha subido ni pedido.

PCB de origen: `../../buck.kicad_pcb`, SHA-256 `d1dda4c1ab6b64db18240570a3af670aa0abed413a410cefdd3bfeda5349d6b5`. Hashes del paquete en `SHA256SUMS.txt`.

## Archivos

| Archivo | Uso |
|---|---|
| `gerbers_revB.zip` | Subir en la cotización de PCB (9 Gerber, 2 Excellon, job) |
| `bom_jlcpcb_revB.csv` | BOM de ensamblaje superior: 32 líneas |
| `cpl_jlcpcb_revB.csv` | 64 colocaciones, cara superior, mm, origen absoluto de KiCad, rotaciones nativas |
| `manual_assembly_revB.csv` | Piezas a montar a mano (J1, J2, J3, Q1, D2), L1/L2 como alternativa manual y los 9 puntos de prueba desnudos |
| `assembly_top_revB.pdf` | Plano de montaje (F.Fab con designadores, serigrafía, courtyards) |
| `schematic_revB.pdf` | Esquemático de 6 hojas |
| `evidence/` | ERC/DRC (JSON y RPT), netlist, posiciones, stock JLCPCB, comandos y resumen |

## Al cotizar (sin confirmar el pedido)

1. 2 capas, FR-4 1,6 mm, 1 oz, **105,55 × 81,05 mm**; revisar que el visor detecte un único contorno.
2. Revisar en el visor Gerber ambas caras: cobre, máscara (vías tapadas), pasta y taladros de J1/J2 (1,3), J3 (1,1), Q1 (1,4), D2 (1,1).
3. Ensamblaje **solo superior**: subir BOM y CPL; deben reconocerse 32 líneas y 64 colocaciones. No aceptar sustituciones automáticas.
4. L1/L2 (C6823957) aparecerán sin stock: decidir Global Sourcing, consigna o no colocar y soldar a mano (ver informe).
5. Confirmar LM4040AIM3X-2.5/NOPB (C111866) como variante de bobina del LM4040AIM3-2.5/NOPB, y R10 (C844354, stock 5).
6. Revisar **las 64 rotaciones** en el visualizador: pin 1 de U1–U10, «+» de C1/C2/C4/C5, cátodo de D1 y D3–D5, Q2, L1/L2. No aprobar con un giro o pinout dudoso.
7. Registrar precio, opciones y stock observado; **detenerse antes de pagar**.

## Referencia para el visualizador (vista superior, coordenadas KiCad)

Un giro de 180° en U1, U6 o U9 cae igual sobre los pads y destruye la pieza (p. ej. U9 intercambia VDD y RESET̅): comprobar marca de pin 1, no solo el encaje.

| Ref | Rot | Marca | Ref | Rot | Marca |
|---|---|---|---|---|---|
| C1 | 180 | «+» a la derecha | U1 | 180 | pin 1 abajo-derecha |
| C2, C4, C5 | 0 | «+» a la izquierda | U2 | 90 | IN abajo-izquierda, pestaña arriba; centroide Y −42,84 |
| D1 | 180 | cátodo a la derecha (hacia L1) | U3–U9 | 0 | pin 1 arriba-izquierda |
| D3, D4 | 90 | cátodo abajo | U10 | 0 | pin 1 arriba-izquierda, pin 3 solo a la derecha |
| D5 | 0 | cátodo a la izquierda | Q2 | 0 | base arriba-izquierda, colector solo a la derecha |
