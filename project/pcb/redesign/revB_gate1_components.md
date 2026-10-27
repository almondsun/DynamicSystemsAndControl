# Rev B — Puerta 1: herramientas, dibujos y suministro

Fecha de consulta: 2026-10-27 (America/Bogota). Las cifras de stock son instantáneas públicas, no reservas.

## Herramientas

KiCad **10.0.7** (Arch `kicad 10.0.7-2`), `kicad-cli` y `pcbnew` SWIG con Python 3.14. Se cargó la revisión A y se reprodujeron sus resultados nativos antes de editar (ERC 0 errores/2 avisos UART; DRC 0 errores, 5 avisos, 0 pendientes, 0 paridad) y se exportaron netlist y Gerbers. No se instaló software de sistema. Solo se creó un entorno Python aislado en `artifacts/gerber-venv` con `pygerber 2.4.3` para inspeccionar los Gerbers con un intérprete independiente de KiCad.

Bibliotecas estándar de KiCad no instaladas: las huellas genéricas se descargaron como datos de `gitlab.com/kicad/libraries/kicad-footprints` (tag 10.0.7) para comparar; las huellas Rev B se generan desde los dibujos del fabricante con `revb_tools/footprints_revb.py`.

## Piezas fijadas por el plan

| Ref | MPN | Dibujo usado (página) | Land Rev B | Suministro (2026-10-27) | Montaje |
|---|---|---|---|---|---|
| L1 (actual) | **Murata 60B684C**, 680 µH, 3 A, 135 mΩ | Mismo dibujo de la serie: Murata KMP_6000B_B01 p.1 | Mismo land que la 60B334C (2 pads 3 × 14 mm a 20,8 mm) | **JLCPCB C6095796: 17** (Extended), 2026-10-27 19:31 UTC | **SMT superior en JLCPCB**. Sustituye a L1+L2 desde el 2026-10-27; +3 % de inductancia frente a 660 µH |
| L1, L2 (descartadas) | Murata 60B334C | Murata KMP_6000B_B01 p.1 «Recommended Pad Layout» (copia LCSC, SHA-256 `9266b3e5…`) | 2 pads 3 × 14 mm a 20,8 mm entre centros; envolvente 23,5 × 27,0 × 20,0 mm máx.; courtyard +0,5 mm | **JLCPCB 0, LCSC 0** (C6823957, Extended, mín. 2); DigiKey 582 (811-2464-ND, plazo 14 sem.); Sager 133 (agregador) | SMT superior pedido por el plan: **bloqueado por stock JLC/LCSC** |
| Q1 | Infineon IRFZ44NPBF | Infineon rev 2.1 p.1 (pinout), p.8 PG-TO220-3-U05 | TO-220 vertical, taladro Ø1,4 mm (IPC-2222: diagonal máx. 1,01 × 0,61 = 1,18 mm + 0,2) | LCSC/JLC C2586: 33 955; DigiKey 5 033 | Manual THT |
| D2 | Vishay UF4004-E3/54 | Vishay 88755 p.4 DO-204AL | DO-41 10,16 mm, taladro 1,1 (pin ≤ 0,86) | LCSC 0, JLC C5137033: 2; DigiKey 50 846 | Manual THT (comprar en DigiKey) |
| J1, J2 | Same Sky TB002-500-02BE | Same Sky rev 1.04 p.2 | Ø1,30 a 5,00 mm; fila de pines a 4,10 de la cara trasera y 3,50 de la entrada de cable; pestaña 0,5 en pin 1 | LCSC C2757858: 461; DigiKey 107 671 | Manual THT |
| J3 | Würth 61201021621 (WR-BHD 10 pines) | Würth rev 002.001 p.1 | Ø1,1 ± 0,15; fila impar (pin 1) en la pared de la ranura de llave (4,5 mm centrada) | LCSC C4355000: 1 873; DigiKey 31 845 | Manual THT |
| Arnés J3 | Würth 61201023021 (IDC hembra) + 63911015521CAB (plano 1,27 mm, 28 AWG) | Würth rev 002.000 / 002.004 | — | DigiKey 43 333 / 790 m | Manual; banda roja en conductor 1 (convención, Würth no la asocia al pin 1) |

## Piezas nuevas de la interfaz

| Ref | MPN | Land (fuente) | JLC stock | Nota |
|---|---|---|---|---|
| U7 | TI SN74LV4T125PWR (C90755) | PW0014A 1,5 × 0,45 mm, filas a 5,8 (SCLS749C p.22) | 2 110 | |
| U8 | TI TMUX1511PWR (C2866750) | PW0014A (SCDS390B p.43) | 2 673 | |
| U9 | TI TPS3808G33DBVR (C43698) | DBV0006A 1,1 × 0,6, filas 2,6 (SBVS050N p.37) | 50 112 | |
| U10 | TI **LM4040AIM3X-2.5/NOPB** (C111866) | DBZ0003A 1,3 × 0,6 (SNOS633N p.78) | 23 149 | Sustitución consciente: el plan nombra LM4040AIM3-2.5/NOPB, con stock 0 y no comprable en JLC/LCSC. SNOS633N §11: la «X» tiene las mismas propiedades eléctricas; el anexo de pedido solo difiere en la bobina (ambas Active, marcado R2A). **Decisión del usuario** |
| D3, D4, D5 | Diodes BAT54WS-7-F (C124205) | SOD323 0,59 × 0,45, extensión 2,70 (DS30098 rev 14 p.4) | 110 056 | Pad 1 = cátodo |

## Lands existentes corregidos tras auditoría

C1/C2 (Panasonic E7: 4,15 × 1,9 a ±3,475), C4/C5 (C6: 3,5 × 1,6 a ±2,80) según Panasonic AAB8000COL10; RS1 (TA-I RLP R>0,004 Ω: 2,1 × 4,0, separación 4,1) según TRLP-250S008F p.3; U3/U4 (D0014A), U5 (D0008A con courtyard ±3,75 × ±2,75) y U6 (DBV0005A) según las páginas de ejemplo TI. Los demás pasivos usan lands IPC nominales compatibles (auditoría en `validation/revb/`).

## Resultado de la puerta

- **Herramientas: cerrada.**
- **Dibujos mecánicos: cerrada** para todas las piezas fijadas y nuevas (land del fabricante o derivación IPC documentada cuando el fabricante no da land: Q1, D2, U1, U2).
- **Suministro para ensamblaje JLCPCB: cerrada (2026-10-27)**: L1+L2 se sustituyen por una sola 60B684C con stock en JLCPCB (32/32 líneas del BOM con stock); R10 pasa a C23022; se acepta la variante X del LM4040. Una decisión intermedia del mismo día (comprar las 60B334C a DigiKey y soldarlas a mano) quedó sin efecto. Antes de esas decisiones: **NO cerrada.** L1/L2 (60B334C) no tienen stock en JLCPCB ni LCSC. Rutas posibles, todas decisión del usuario y ninguna ejecutada: (a) Global Sourcing de JLCPCB desde DigiKey/otros (requiere cuenta; no consultado); (b) consignar las piezas compradas a DigiKey; (c) pedir la placa sin L1/L2 y soldarlas a mano (pads de 3 × 14 mm, terminación de estaño puro, 37 g). La huella es la misma en los tres casos.
- Con esas decisiones la placa puede pedirse como prototipo de laboratorio; la revisión de orientaciones en el visualizador se hace al pedir.
