# Paquete JLCPCB — Buck Rev B (2026-10-27)

**Listo para pedir como prototipo de laboratorio** (ver [informe Rev B](../../revB_release_report.md), secciones 7, 7b y 7d). Nada se ha subido ni pedido desde aquí.

PCB de origen: `../../buck.kicad_pcb`, SHA-256 `ee424698b431ce423ca0664407f9331b4e0f952d4aec9421b8bc89f30235b530`. Hashes del paquete en `SHA256SUMS.txt`.

La bobina es una sola **Murata 60B684C** (680 µH, LCSC C6095796), en lugar de 2 × 60B334C sin stock; misma serie 6000B y mismo land. **JLCPCB no la coloca**: se compra aparte y se suelda a mano. Hay dos motivos. Su pico de reflujo admisible es 245 °C, y Economic PCBA refluye a 255 ± 5 °C sin ajuste. Además, su cuerpo queda a 0,48 mm del borde inferior.

## Archivos

| Archivo | Uso |
|---|---|
| `gerbers_revB.zip` | Subir en la cotización de PCB (9 Gerber, 2 Excellon, job) |
| `bom_jlcpcb_revB.csv` | BOM de ensamblaje superior: 31 líneas (sin L1) |
| `cpl_jlcpcb_revB.csv` | 62 colocaciones, cara superior, mm, origen absoluto de KiCad, rotaciones nativas |
| `manual_assembly_revB.csv` | Piezas a comprar y montar a mano: L1 (60B684C), J1, J2, J3, Q1, D2; los 9 puntos de prueba son pads desnudos |
| `assembly_top_revB.pdf` | Plano de montaje (F.Fab con designadores, serigrafía, courtyards) |
| `schematic_revB.pdf` | Esquemático de 6 hojas |
| `evidence/` | ERC/DRC (JSON y RPT), netlist, posiciones, stock JLCPCB, comandos y resumen |

## Al cotizar (sin confirmar el pedido)

1. 2 capas, FR-4 1,6 mm, 1 oz, **105,55 × 81,05 mm**; revisar que el visor detecte un único contorno.
2. Revisar en el visor Gerber ambas caras: cobre, máscara (vías tapadas), pasta y taladros de J1/J2 (1,3), J3 (1,1), Q1 (1,4), D2 (1,1).
3. Ensamblaje **Economic PCBA, solo cara superior**: subir BOM y CPL; deben reconocerse 31 líneas y 62 colocaciones. No aceptar sustituciones automáticas. Si el portal propone añadir L1, no aceptarlo.
4. Comprar aparte **una 60B684C por placa más una de repuesto** (LCSC C6095796: 17 en stock y ≈ 6,90 USD/u el 2026-10-27; DigiKey como alternativa). JLCPCB imprime pasta en los pads de L1 aunque no la coloque, así que la placa llega con los pads estañados.
5. Comprobar que se reconocen U10 = LM4040AIM3X-2.5/NOPB (C111866) y R10 = 0603WAF3092T5E (C23022).
6. Revisar **las 62 rotaciones** en el visualizador: pin 1 de U1–U10, «+» de C1/C2/C4/C5, cátodo de D1 y D3–D5, Q2. No aprobar con un giro o pinout dudoso.
7. Registrar precio, opciones y stock observado antes de pagar.

**Alternativa (no recomendada para hoy):** que JLCPCB coloque L1 con **Standard PCBA**, que refluye a 240 ± 5 °C y lleva rieles de fabricación. Requiere su confirmación por escrito del perfil, del peso (37 g) y de la cercanía al borde. Si la confirman, añadir al BOM la línea `680uH 60B684C,L1,L_Murata_6000B_27.0x23.5mm,C6095796,60B684C` y al CPL la línea `L1,148.0000mm,-98.5000mm,Top,0.0`. L1 no es polar; en el visor, sus terminales deben caer sobre los dos pads horizontales.

## Montaje manual de L1

1. Antes de soldar, medir L1 suelta: 578–782 µH a 10 kHz (680 µH ±15 %) y ≤ 135 mΩ a 4 hilos.
2. Soldar L1 **antes que Q1 y D2**, para tener acceso al terminal SW (el de la izquierda, junto a la pestaña de Q1).
3. Murata solo especifica el pico de reflujo (245 °C, J-STD-020D.1), no condiciones de soldador. Lo siguiente es práctica general, no un dato del fabricante. Precalentar la placa por debajo a ≈ 100–120 °C. Usar un soldador de ≥ 60 W a 330–350 °C con punta ancha y flux. Calentar a la vez el terminal y el pad, en pasadas de pocos segundos, dejando enfriar entre pasadas. El mojado debe cubrir todo el pad de 3 × 14 mm.
4. El cuerpo queda a 0,48 mm del borde inferior: no sujetar ni apoyar la placa por ese borde en la zona de L1. Para transportar la placa montada, añadir un punto de silicona neutra entre el cuerpo y la PCB.

## Referencia para el visualizador (vista superior, coordenadas KiCad)

Un giro de 180° en U1, U6 o U9 cae igual sobre los pads y destruye la pieza (p. ej. U9 intercambia VDD y RESET̅): comprobar marca de pin 1, no solo el encaje.

| Ref | Rot | Marca | Ref | Rot | Marca |
|---|---|---|---|---|---|
| C1 | 180 | «+» a la derecha | U1 | 180 | pin 1 abajo-derecha |
| C2, C4, C5 | 0 | «+» a la izquierda | U2 | 90 | IN abajo-izquierda, pestaña arriba; centroide Y −42,84 |
| D1 | 180 | cátodo a la derecha (hacia L1) | U3–U9 | 0 | pin 1 arriba-izquierda |
| D3, D4 | 90 | cátodo abajo | U10 | 0 | pin 1 arriba-izquierda, pin 3 solo a la derecha |
| D5 | 0 | cátodo a la izquierda | Q2 | 0 | base arriba-izquierda, colector solo a la derecha |
