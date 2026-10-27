# Cálculos preliminares de cobre y vías

Fecha 2026-10-26. Estimaciones reproducibles en [calculations.json](validation/pcb_rules/calculations.json), generadas por `artifacts/buck_pcb_rules_20261026/configure_rules.py`. No son resultados de Saturn, ensayos ni aprobación térmica.

## Método y sensibilidad

Se inspeccionó el artículo primario de Michael Jouppi, [The Value of IPC-2152](https://www.electronics.org/system/files/technical_resource/E7%26S22_03.pdf), especialmente figuras 3/4. Distingue la curva conservadora de las nuevas mediciones de conductores, con efectos de montaje, planos y espesor. No es válido trasladar sin justificación un gráfico de capa interna a esta placa exterior de dos capas.

La [ayuda oficial de Saturn](https://saturnpcb.com/saturn-pcb-toolkit-help-htm/) distingue la curva conservadora heredada del gráfico interno IPC-2221 y la metodología IPC-2152. La serie 8 ya no aplica los multiplicadores antiguos de área. No se aplicó una supuesta bonificación térmica por plano GND ni se afirmó usar IPC-2152 completo.

Al no poder operar Saturn, el filtro conservador usa `I=0.024·ΔT^0.44·A^0.725`, A en mil². **Es un ajuste de la curva conservadora heredada, no una simulación IPC-2152 de esta geometría.** Se complementa con resistencia, caída, disipación, tolerancias, discusión de montaje y revisión del documento IPC-2152. La comprobación térmica con esa metodología queda abierta; el ajuste no basta para liberar el layout.

Se calcula ancho dibujado `w=A·0.0254²/(0.030·0.8)`: cobre supuesto 30 µm y pérdida de ancho 20%. Los 30 µm son un caso de sensibilidad, no mínimo garantizado de JLCPCB. Ambiente 45 °C; comparación ΔT=10/20 °C. Pistas exteriores sin adjudicar enfriamiento por planos. Encapsulado, máscara, cobre vecino, longitud, disipación de componentes y ventilación alteran el resultado real.

| Corriente A | Incremento °C | Ancho estimado mm |
|---:|---:|---:|
| 1.458 | 10 | 1.917 |
| 1.458 | 20 | 1.259 |
| 1.470 | 10 | 1.939 |
| 1.470 | 20 | 1.273 |
| 2.000 | 10 | 2.965 |
| 2.000 | 20 | 1.947 |
| 2.500 | 10 | 4.033 |
| 2.500 | 20 | 2.648 |

Elección preliminar: 3 mm para entrada presupuestada a 2 A y 2 mm para troncos a 1.47 A RMS. Los 1.5 mm iniciales no satisfacen el filtro de 10 °C en este caso de sensibilidad. A 2.5 A sostenidos se necesitarían aproximadamente 4.03 mm para 10 °C o 2.65 mm para 20 °C según el mismo ajuste: las pistas de 2 mm no se declaran aptas para esa falla continua.

## Caída y disipación

`R=ρ·l/(w·t)`, `V=I·R`, `P=I²R`. Cobre ρ20=1.724×10⁻⁸ Ωm; α=0.00393/K; ρ55=1.96114×10⁻⁸ Ωm. Tabla a 55 °C, 30 µm y ancho real 80% del dibujado; escalar linealmente por longitud. El JSON incluye también cobre nominal 35 µm sin pérdida de ancho. Para 65 °C, multiplicar las resistencias a 55 °C por aproximadamente 1.0345.

| Ancho dibujado mm | I A | R mΩ/10 mm | Caída mV/10 mm | Disipación mW/10 mm |
|---:|---:|---:|---:|---:|
| 1.5 | 1.47 | 5.448 | 8.008 | 11.772 |
| 1.5 | 2.00 | 5.448 | 10.895 | 21.790 |
| 1.5 | 2.50 | 5.448 | 13.619 | 34.048 |
| 2.0 | 1.47 | 4.086 | 6.006 | 8.829 |
| 2.0 | 2.00 | 4.086 | 8.171 | 16.343 |
| 2.0 | 2.50 | 4.086 | 10.214 | 25.536 |
| 3.0 | 1.47 | 2.724 | 4.004 | 5.886 |
| 3.0 | 2.00 | 2.724 | 5.448 | 10.895 |
| 3.0 | 2.50 | 2.724 | 6.810 | 17.024 |

Medir la longitud real y sumar pad escapes, conectores, barriles, shunt y estrechamientos. La resistencia del tronco no es la resistencia total de lazo y su caída puede contaminar el sensado si comparte cobre Kelvin.

## Vías

Señal 0.60/0.30 mm; auxiliar 0.80/0.40 mm. Anillos radiales nominales 0.15 y 0.20 mm. La tolerancia de perforación/registro reduce el anillo efectivo; confirmar aceptación del fabricante en el CAM. Sin vías en pads SMD abiertos. Tenting no sustituye relleno/capado si se quisiera vía en pad, proceso que aquí no se eligió.

Barril modelado `A=π(d+t)t`, `R=ρ·l/A`; se aproxima la capacidad comparativa desplegando el área en la curva conservadora. Este recurso **no predice por sí solo temperatura de una vía ni reemplaza el módulo térmico de Saturn**. No incluye resistencia de spreading ni reparto térmico entre vías próximas. Los 18 µm son promedio publicado, los 15 µm un supuesto de sensibilidad y ninguno constituye un mínimo contratado.

| Taladro real mm | Metal µm supuesto | Longitud mm | R mΩ a 55 °C | I equivalente Δ10 A | I equivalente Δ20 A |
|---:|---:|---:|---:|---:|---:|
| 0.30 | 18 | 1.60 | 1.745 | 0.738 | 1.001 |
| 0.40 | 18 | 1.60 | 1.327 | 0.900 | 1.220 |
| 0.32 | 15 | 1.76 | 2.186 | 0.671 | 0.911 |

Para un cambio inevitable de potencia, candidato inicial: cinco vías 0.80/0.40 en paralelo. A 2 A, con una vía inoperante y reparto 25% desigual: 2/(5−1)×1.25=0.625 A por vía más cargada. Comparar con la fila de sensibilidad anterior; a 2.5 A resultan 0.781 A por vía, por encima del filtro de 10 °C de ese caso. La resistencia ideal del conjunto es Rindividual/N (y N−1 en contingencia), pero entradas asimétricas empeoran el reparto. No se ha colocado ninguna vía de potencia.

Disponer accesos simétricos, cobre ancho y aproximadamente 1 mm entre centros cuando sea viable; comprobar clearance de cobre entre redes distintas y separación real de agujeros. Evitar vías en el lazo caliente y gate. Si la placa obliga a un cambio de capa, volver a evaluar número, reparto, metalizado mínimo y temperatura conjunta con Saturn y montaje real.

## Corrientes de falla

2.5 A es hipótesis, no límite de cortocircuito. A esa corriente, I²t es 0.0000625/0.00625/0.0625/0.625 A²s para 10 µs/1 ms/10 ms/100 ms respectivamente. Sin retardo garantizado de comparador/latch/driver, impedancia de fuente y comportamiento de MOSFET/diodo no se acredita supervivencia. L almacena 1.04 mJ a 660 µH y 1.775 A; 2.06 mJ a 2.5 A, antes de energía adicional de entrada. No usar 2 A de presupuesto como fusible, ni inferir limitación por una fuente de 1 A.

## Comprobación pendiente en Saturn

Instalación localizada: `C:/Program Files (x86)/Saturn PCB Design/Saturn PCB Toolkit V8.48/PCB Toolkit V8.48.exe`. Se intentó abrir por la interfaz autorizada; devolvió que no existía ventana controlable y el inventario de ventanas tampoco la mostró. Ayuda local extraída identificada como V8.46; no confundirla con la versión instalada 8.48. No se inventaron capturas ni salidas de cálculo.

Al poder abrirlo: registrar versión, módulo de corriente, metodología IPC-2152 sin modificadores antiguos, conductor exterior, FR-4 de 1.6 mm, cobre base y metalizado separados, 45 °C ambiente, Δ10/20 °C, corrientes 1.458/1.470/2/2.5 A y geometría/planos reales. Repetir con mínimo de cobre confirmado; exportar ancho, R por longitud, caída y potencia. Para vías registrar taladro terminado, metalizado mínimo, longitud, cantidad y separación. Si difiere del filtro, revisar anchos y documentar la decisión antes del ruteo.
