# Convertidor Buck 12 V → 6 V con control PI digital

Proyecto final de *Sistemas Dinámicos y Control*, Universidad Nacional de Colombia,
sede Manizales (2026-2). Es un convertidor Buck diseñado, fabricado y controlado de
punta a punta:

- placa propia de dos capas, ensamblada por JLCPCB;
- driver bootstrap discreto para un MOSFET de canal N;
- control PI digital a 20 kHz en una NUCLEO-L432KC;
- validación experimental frente a la simulación.

![Placa Rev C (render de KiCad)](hardware/placa-3d.png)

## Resultados

El PI diseñado en la Entrega 3 se implementó **sin reajustes**. Con la planta
identificada en el banco conserva 97° de margen de fase y 11.6 dB de margen de
ganancia. Valores medidos (media de 3 repeticiones; entre paréntesis, la simulación
conmutada de la Entrega 3):

| Ensayo | Resultado medido | Especificación |
|---|---|---|
| Referencia 6 → 7 V | ts 4.89 ms (4.53), Mp 0.48 % (0.13 %) | ts ≤ 5 ms, Mp ≤ 5 % |
| Referencia 6 → 5 V | ts 4.55 ms (4.58), Mp 0.53 % (0.08 %) | ts ≤ 5 ms, Mp ≤ 5 % |
| Carga +20 % (6 → 7.2 Ω) | pico +0.62 V, ±20 mV en 1.47 ms | recuperación ≤ 5 ms |
| Carga −20 % (6 → 4.8 Ω) | pico −0.76 V, ±20 mV en 2.54 ms | recuperación ≤ 5 ms |
| Régimen | error < 1 mV (ADC del lazo), d máx 0.694 | ess = 0, d ≤ 0.85 |

Planta real identificada: r_L ≈ 0.94 Ω, V_F ≈ 0.26 V, C efectiva 14–17 µF,
ωn ≈ 10.2–11.1 krad/s, ζ ≈ 0.62. La eficiencia en lazo abierto fue de 79–85 %.

## Entregas

| Entrega | Informe | Material |
|---|---|---|
| 1. Modelo y simulación | [PDF](informes/entrega-1/entrega_1.pdf) | — |
| 2. Convertidor en lazo abierto | [PDF](informes/entrega-2/entrega_2.pdf) | Placa perforada con MOSFET canal P. Su falla (re-conducción por efecto Miller) motivó la placa Rev C. |
| 3. Diseño del compensador | [PDF](informes/entrega-3/entrega_3.pdf) · [LaTeX](informes/entrega-3/entrega_3.tex) | [`analisis/entrega-3`](analisis/entrega-3) |
| 4. Controlador implementado | [PDF](informes/entrega-4/entrega_4.pdf) · [LaTeX](informes/entrega-4/entrega_4.tex) | [`firmware`](firmware), [`laboratorio`](laboratorio), [`analisis/entrega-4`](analisis/entrega-4) |

## Estructura

```
hardware/      KiCad 10 (esquemático, PCB, reglas), BOM, archivos de producción JLC y
               herramientas (regenerar producción, auditoría de layout)
firmware/      PlatformIO + STM32Cube HAL: PWM, ADC sincronizado, PI, protecciones, consola
laboratorio/   guía de puesta en marcha y ensayos, scripts de adquisición (Analog
               Discovery 3 + serie) y datos crudos
analisis/      entrega-3 (MATLAB: diseño y simulación), entrega-4 (Python: métricas,
               figuras y comparación con la simulación)
informes/      los cuatro informes (IEEE)
curso/         enunciado, presentaciones, talleres y ejemplos del docente (ver curso/README.md)
AGENTS.md      contexto técnico detallado: circuito, decisiones, resultados, comandos
```

## Reproducir

Los binarios (PDF, imágenes, CSV de laboratorio, `.mat`) están en Git LFS:

```sh
git lfs install
git clone git@github.com:almondsun/DynamicSystemsAndControl.git
```

| Qué | Cómo |
|---|---|
| Firmware | `cd firmware && pio run` (`pio run -t upload` para programar por ST-Link) |
| Diseño E3 | MATLAB, desde `analisis/entrega-3/matlab`: `e3_main`, luego `e3_figures('report')` |
| Análisis E4 | `python3 -I analisis/entrega-4/e4_main.py` (numpy, scipy, matplotlib) |
| Informes | `cd informes/entrega-4 && latexmk -pdf entrega_4.tex` |
| Hardware | `kicad-cli pcb drc --schematic-parity hardware/kicad/pcb_revC.kicad_pcb`; producción con `python3 -I hardware/herramientas/make_jlc_files.py` (KiCad cerrado) |
| Ensayos | `laboratorio/guia-puesta-en-marcha.md`; `laboratorio/scripts/run_suite.py` |

## Autores

Martín Ramírez Espinosa, Jerónimo Vargas Orozco, Andrew Esteban Henao Becerra y
Mateo Alexander Cardenas Cuesta. Profesor: Juan David Bastidas Rodríguez.

El material de `curso/` pertenece a sus autores. El modelo 3D del inductor
(`hardware/kicad/lib/easyeda.3dshapes`) proviene de la biblioteca de EasyEDA/LCSC.
