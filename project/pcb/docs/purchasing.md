# Compra y presupuesto — COP, Colombia

Objetivo de planificación: **COP 350 000 por equipo / COP 87 500 por estudiante**.
Son cuatro integrantes, una unidad ensamblada, una pequeña tanda de placas
desnudas y repuestos selectivos. El laboratorio proporciona fuente limitada
en corriente, osciloscopio y sondas apropiadas, multímetro, LCR y soldadura.

| Reserva inicial | COP |
|---|---:|
| Dos STM32, ST-LINK, adaptador UART y cables | 75 000 |
| Potencia, driver, protección, conectores y repuestos | 80 000 |
| Banco de carga externo y conmutadores | 20 000 |
| Cinco PCB y transporte internacional | 80 000 |
| Envíos nacionales | 25 000 |
| Contingencia para diferencias, impuestos y disponibilidad | 70 000 |
| **Total de planificación** | **350 000** |

La lista detallada [purchasing.csv](../purchasing.csv) calcula las cantidades
para **una placa**, repuestos y accesorios externos. Sus precios de reserva
no constituyen cotizaciones. Si el subtotal de componentes supera los
COP 80 000 inicialmente separados, se cubre primero con contingencia y se
recalcula el aporte; no se asume un total garantizado. El presupuesto incluye
adaptador USB–UART de lógica 3.3 V: el ST-LINK mini seleccionado no aporta UART.

Resultado del desglose actual en `budget.json`: componentes de PCB y
accesorios COP 85 633.10; controlador/programación COP 74 041.05; carga
COP 16 827.80. Sumando las reservas de envíos y fabricación: **COP 281 501.95
antes de contingencia**, con COP 68 498.05 disponibles dentro del objetivo.

## Referencias locales consultadas

Consulta de planificación del 14 de septiembre de 2026, Didácticas Electrónicas
I+D. El proveedor indica **confirmar precio y disponibilidad con un asesor**.
Los valores no acreditan transporte, impuestos adicionales ni stock reservado.
No se contactó al proveedor ni se realizó un pedido.

| Producto / SKU | Precio unitario observado (COP) | Fuente |
|---|---:|---|
| STM32F103C8T6 USB-C / D-STM32F103C8T6-C | 10 890.88 | [Producto](https://www.didacticaselectronicas.com/shop/d-stm32f103c8t6-c-tarjeta-de-desarrollo-stm32f103c8t6-usb-tipo-c-39492) |
| ST-LINK V2 mini / WS-10053 | 39 259.29 | [Producto](https://www.didacticaselectronicas.com/shop/ws-10053-programador-y-compilador-stm-st-link-v2-mini-10292) |
| IR2110 DIP14 | 10 890.88 | [Producto](https://www.didacticaselectronicas.com/shop/ir2110-driver-mosfet-ir2110-500v-2a-6383) |
| Toroide vertical 330 µH / BOB-V-65125-330UH | 3 871.07 | [Candidato](https://www.didacticaselectronicas.com/shop/bob-v-65125-330uh-bobina-toroidal-vertical-de-330uh-5a-24437) |
| 1N5822 DO-201AD | 404.60 | [Producto](https://www.didacticaselectronicas.com/shop/1n5822-tp-diodo-schottky-40v-3a-do-201ad-4261) |
| Resistencia 12 Ω / 10 W | 963.90 | [Candidato, stock insuficiente en consulta](https://www.didacticaselectronicas.com/shop/r-12r-10w-resistencia-ceramica-12r-10w-35841) |

El toroide horizontal del mismo proveedor es una alternativa de búsqueda,
**no intercambiable automáticamente** con la huella vertical. La rotulación
de 5 A o 6 A no proporciona una curva de saturación. Medir L, DCR, dimensiones
y comportamiento hasta al menos 2.2 A; preferir un componente con Isat
documentada ≥3 A. Separar físicamente ambas bobinas, verificar la inductancia
total en su disposición real y fijarlas mecánicamente.

Para U6 comprar **INA180A1IDBVR**, no INA180B1 ni una ganancia A2/A3/A4.
Para U3/U4 usar **HCT**, no HC a 5 V. Para Q1 exigir fabricante y referencia
IRFZ44N verificables; la publicación genérica IRFZ44 no acredita el mismo
componente. Para C4/C5 exigir 10 µF cada uno, tensión ≥35 V, polaridad y
dimensiones compatibles, ESR y corriente de rizado documentadas a 10 kHz.
La huella actual admite Ø6.3 mm / paso 2.5 mm. Si el componente calificado
usa paso 2 mm, se cambia la huella y se repite DRC/Gerber antes de fabricar.
En el presupuesto estos capacitores son **candidatos pendientes**, no MPN
cerrados ni supuestos de compra aprobados.

## PCBWay frente a JLCPCB

Cotizar exactamente el mismo ZIP, dimensiones, cantidad, espesor, cobre y
acabado. Completar destino real en Colombia y registrar:

| Dato | PCBWay | JLCPCB |
|---|---|---|
| URL | https://www.pcbway.com/ | https://jlcpcb.com/ |
| Cinco placas / 99 × 99 mm / dos capas | Pendiente | Pendiente |
| Transporte y tiempo al destino real | Pendiente | Pendiente |
| Impuestos, manejo y conversión COP | Pendiente | Pendiente |
| **Total entregado COP** | **Pendiente** | **Pendiente** |

JLCPCB publicita FR-4 desde USD 2 por cinco placas; **no es el costo puesto
en Colombia**. No se obtuvo una cotización entregada de ninguna empresa.
La reserva de COP 80 000 para PCB y transporte sigue siendo una estimación.
Elegir el menor total entregado compatible con el calendario, después de
resolver las verificaciones físicas. No reducir protecciones para compensar
un envío costoso; consolidar componentes y considerar repartir placas de sobra.

## Orden de trabajo del equipo

1. Responsable de compras: cerrar existencias, MPN, dimensiones y presupuesto.
2. Responsable de montaje: prototipo soldado, inspección con otra persona y PCB.
3. Responsable de firmware: verificar STM32/SWD/reloj/ADC, calibrar y documentar.
4. Responsable de mediciones: capturas, incertidumbre, repeticiones e informes.

Primera semana: componentes críticos y programación. Segunda: prototipo y
mediciones. Luego liberar fabricación y esperar transporte; finalmente
ensamblar y ejecutar los seis escenarios. Reservar 4–6 semanas como horizonte,
sujeto a cotización, transporte y disponibilidad real de laboratorio.
