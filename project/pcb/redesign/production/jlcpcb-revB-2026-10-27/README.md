# Paquete JLCPCB — Buck Rev B (2026-10-27)

**Listo para pedir como prototipo de laboratorio** (ver [informe Rev B](../../revB_release_report.md), secciones 7 y 7b). Nada se ha subido ni pedido desde aquí.

PCB de origen: `../../buck.kicad_pcb`, SHA-256 `9cb758e93f206784ae35fcfe1db60a2def58e6aaddbb9a22d034e13bf41a9ec2`. Hashes del paquete en `SHA256SUMS.txt`.

La bobina es una sola **Murata 60B684C** (680 µH, C6095796) que coloca JLCPCB, en lugar de 2 × 60B334C sin stock; misma serie 6000B y mismo land.

## Archivos

| Archivo | Uso |
|---|---|
| `gerbers_revB.zip` | Subir en la cotización de PCB (9 Gerber, 2 Excellon, job) |
| `bom_jlcpcb_revB.csv` | BOM de ensamblaje superior: 32 líneas (L1 incluida) |
| `cpl_jlcpcb_revB.csv` | 63 colocaciones, cara superior, mm, origen absoluto de KiCad, rotaciones nativas |
| `manual_assembly_revB.csv` | Piezas THT a comprar y montar a mano: J1, J2, J3, Q1, D2; los 9 puntos de prueba son pads desnudos |
| `assembly_top_revB.pdf` | Plano de montaje (F.Fab con designadores, serigrafía, courtyards) |
| `schematic_revB.pdf` | Esquemático de 6 hojas |
| `evidence/` | ERC/DRC (JSON y RPT), netlist, posiciones, stock JLCPCB, comandos y resumen |

## Al cotizar (sin confirmar el pedido)

1. 2 capas, FR-4 1,6 mm, 1 oz, **105,55 × 81,05 mm**; revisar que el visor detecte un único contorno.
2. Revisar en el visor Gerber ambas caras: cobre, máscara (vías tapadas), pasta y taladros de J1/J2 (1,3), J3 (1,1), Q1 (1,4), D2 (1,1).
3. Ensamblaje **solo superior**: subir BOM y CPL; deben reconocerse 32 líneas y 63 colocaciones. No aceptar sustituciones automáticas.
4. L1 = Murata 60B684C (C6095796, Extended): 17 en stock el 2026-10-27, alcanza para 5 placas pero no para 20. Es una pieza de ≈ 37 g y 20 mm de alto: comprobar en el portal que JLCPCB la acepta en SMT. Si la pasa a soldadura manual, aceptar el recargo; si la rechaza, quitarla del pedido y soldarla a mano (los pads llevan pasta).
5. Comprobar que se reconocen U10 = LM4040AIM3X-2.5/NOPB (C111866) y R10 = 0603WAF3092T5E (C23022).
6. Revisar **las 63 rotaciones** en el visualizador: pin 1 de U1–U10, «+» de C1/C2/C4/C5, cátodo de D1 y D3–D5, Q2, y que los terminales de L1 caigan sobre los dos pads horizontales. No aprobar con un giro o pinout dudoso.
7. Registrar precio, opciones y stock observado antes de pagar.

## Referencia para el visualizador (vista superior, coordenadas KiCad)

Un giro de 180° en U1, U6 o U9 cae igual sobre los pads y destruye la pieza (p. ej. U9 intercambia VDD y RESET̅): comprobar marca de pin 1, no solo el encaje.

| Ref | Rot | Marca | Ref | Rot | Marca |
|---|---|---|---|---|---|
| C1 | 180 | «+» a la derecha | U1 | 180 | pin 1 abajo-derecha |
| C2, C4, C5 | 0 | «+» a la izquierda | U2 | 90 | IN abajo-izquierda, pestaña arriba; centroide Y −42,84 |
| D1 | 180 | cátodo a la derecha (hacia L1) | U3–U9 | 0 | pin 1 arriba-izquierda |
| D3, D4 | 90 | cátodo abajo | U10 | 0 | pin 1 arriba-izquierda, pin 3 solo a la derecha |
| D5 | 0 | cátodo a la izquierda | Q2 | 0 | base arriba-izquierda, colector solo a la derecha |
| L1 | 0 | no polar; terminales a izquierda y derecha (pads a 20,8 mm). Si el modelo de JLCPCB aparece girado 90°, corregir a 90 o 270 | | | |
