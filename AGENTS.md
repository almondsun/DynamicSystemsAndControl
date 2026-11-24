# Convertidor Buck 12 V → 6 V con control PI digital — contexto para agentes

Lee esto primero. El repositorio contiene **solo** el proyecto final de *Sistemas
Dinámicos y Control* (Universidad Nacional de Colombia, sede Manizales, 2026-2):
el convertidor Buck Rev C, su firmware, el análisis, los datos de laboratorio, los
cuatro informes y el material docente del curso (`curso/`).

## 1. Estado (2026-11-24): proyecto terminado

| Entrega | Contenido | Estado |
|---|---|---|
| 1. Modelo y simulación | `informes/entrega-1/entrega_1.pdf` | Entregada (diseño original; sin fuentes en el repo) |
| 2. Lazo abierto experimental | `informes/entrega-2/entrega_2.pdf` | Entregada sobre placa perforada con MOSFET canal P; falló por re-conducción (ver §8). La identificación válida de la planta está en la E4. |
| 3. Diseño del PI | `analisis/entrega-3/`, `informes/entrega-3/` | Terminada sobre la planta Rev C |
| 4. Controlador implementado | `firmware/`, `laboratorio/`, `analisis/entrega-4/`, `informes/entrega-4/` | Terminada: 4 ensayos × 3 repeticiones, todas las especificaciones cumplidas |

La placa Rev C se fabricó en JLCPCB (PCBA), se puso en marcha el 2026-11-23 y los
ensayos de la E4 se hicieron el 2026-11-24. No hay trabajo de diseño pendiente.

## 2. Mapa del repositorio

```
hardware/kicad/          proyecto KiCad 10 (pcb_revC.kicad_{pro,sch,pcb,dru}); símbolo propio
                         AOD4184A (buckRevC.kicad_sym), huella L_Bourns_SRR1280 y su modelo 3D
                         en lib/easyeda.3dshapes/ (la huella lo referencia con esa ruta relativa)
hardware/bom/            BOM maestro (español): LCSC, Basic/Extended, "Local" = soldado a mano
hardware/produccion/     archivos subidos a JLC: gerbers/, zip, BOM_JLC, CPL_JLC (generados)
hardware/herramientas/   make_jlc_files.py (regenera produccion/), check_layout.py +
                         layout_checklist.md (auditoría de layout con checklist con fuentes)
firmware/                PlatformIO + STM32Cube HAL para la NUCLEO-L432KC (src/: main, hw, control)
laboratorio/             guia-puesta-en-marcha.md (inspección, energizado por etapas, ensayos E4),
                         scripts/ (cl_event.py, run_suite.py: AD3 + consola serie),
                         datos/ (capturas crudas; ver §6)
analisis/entrega-3/      MATLAB sin toolboxes: e3_main (diseño, simulación, resultados JSON/MAT),
                         e3_figures('slides'|'report') → figuras/ y figuras/informe/
analisis/entrega-4/      e4_main.py (figuras, métricas, error rms, márgenes con la planta
                         identificada) + analyze_e4.py (port de e3_metrics.m y cargadores)
informes/entrega-N/      PDF entregados; E3 y E4 con su .tex (IEEE, `latexmk -pdf`)
curso/                   enunciado, programa, capítulos de teoría, talleres y ejemplos del docente
```

Los PDF, PNG, CSV de `laboratorio/datos/`, `.mat`, `.zip`, `.step`, `.wrl` y `.slx`
están en **Git LFS** (`git lfs install` antes de clonar). `hardware/**` es `-text`:
los gerbers y archivos de KiCad se guardan byte a byte (los gerbers versionados
tienen CRLF porque se generaron en Windows).

## 3. Restricciones y reglas de trabajo

- **No modificar la placa ni la producción** sin pedido explícito: es el diseño
  fabricado. Si se edita el KiCad, regenerar `hardware/produccion/` con
  `make_jlc_files.py` (KiCad cerrado) y volver a correr ERC/DRC.
- `place_revC.py`/`route_revC.py` (generadores de una sola vez) ya no existen; la
  ubicación y el ruteo se editan en KiCad. Las zonas de cobre se rellenan con B.
- Salidas de verificación (ERC/DRC, renders, gerbers de prueba) van a una carpeta
  temporal, nunca dentro del repo. `check_layout.py` escribe en
  `hardware/herramientas/runs/` (ignorado).
- No inventar datos experimentales. Las métricas salen de `laboratorio/datos/` con
  `analisis/entrega-4/e4_main.py`.
- Herramientas instaladas en esta máquina (Linux): `kicad-cli` 10.0.8 con `pcbnew`
  para Python del sistema, `pio`, `latexmk`. MATLAB no está en el PATH (usar la MCP
  de MATLAB si está disponible para `analisis/entrega-3`).

## 4. Punto de operación y especificaciones

| Magnitud | Valor |
|---|---|
| Vin | 12 V de fuente de laboratorio (límite 1.5 A; 100 mA en la puesta en marcha) |
| Vout | 6 V nominal; escalones de referencia 6→7 V y 6→5 V |
| Carga | 6 Ω nominal (1 A); perturbaciones +20 % (7.2 Ω) y −20 % (4.8 Ω) |
| L | 2 × 330 µH SRR1280-331K en serie (DCR ≤ 0.6 Ω c/u, Irms 1.1 A, Isat 1.4 A) |
| C | 2 × 10 µF cerámicos 50 V (C efectiva medida 14–17 µF por polarización DC) |
| fsw | 20 kHz nominal (medida 19.84 kHz: tolerancia del oscilador MSI) |
| Entrada de control | **d** (el driver es no inversor; el enunciado asume d' = 1 − d con su driver inversor) |
| Especificaciones (E3) | ess = 0, Mp ≤ 5 %, ts ≤ 5 ms (±2 %), MF ≥ 60°, MG ≥ 6 dB, d ≤ 0.85, recuperación de carga ≤ 5 ms |

Red de carga: J2 carga base 7.2 Ω (2 × 3.6 Ω 10 W); J3 36 Ω vía Q6 → 6.0 Ω; J4 24 Ω
vía Q7 → 4.8 Ω. Corriente máxima en régimen ≈ 1.25 A (no combinar 7 V con 4.8 Ω:
supera la Irms de los inductores).

## 5. Circuito (Rev C)

- **Potencia:** J1 → VIN; C1–C3 10 µF/50 V 1206 + C4 100 nF (lazo caliente) + C5
  100 µF electrolítico (soldado a mano). Q1 **AOD4184A** (TO-252, D = VIN, S = SW),
  diodo D1 **SS34**, L1 → VMID → L2 → VOUT, C6/C7 (C8 sin montar).
- **Driver bootstrap discreto, no inversor:** PWM (D9/PA8) → R1 1 k → Q2 MMBT3904
  (R2 100 k a GND) → R3 10 k a VIN → Q3 MMBT3904 → DRV_B; R4 1.2 k a BOOT; tótem
  Q4 MMBT2222A / Q5 S8550 → R5 10 Ω → GATE; R6 10 k G–S. Bootstrap D2 1N4148W +
  C9 1 µF. PWM en alto ⇒ Q1 encendido; **con el PWM flotante o sin NUCLEO, Q1 queda
  apagado** (más seguro que el circuito de referencia).
- **Cargas:** Q6/Q7 AO3400A con LSW_A (D2/PA12) y LSW_B (D3/PB0), 100 Ω serie y
  100 k a GND.
- **Sensado:** divisores 30 k/10 k (×0.25) con 4.7 nF: VOUT_SENSE → A1/PA1,
  VIN_SENSE → A2/PA3. TRIG (TP10) en A3/PA4 marca cada evento para el osciloscopio.
- **NUCLEO-L432KC** en zócalos J5 (CN3) / J6 (CN4), filas a 15.24 mm, **USB hacia
  J2–J4** (flecha "USB ->" en la serigrafía). Se alimenta por su USB; sus VIN/5V/3V3
  no se conectan a la placa.
- Puntos de prueba: TP1 VIN, TP2 SW, TP3 GATE, TP4 VOUT, TP5 PWM, TP6–TP8 GND,
  TP9 BOOT, TP10 TRIG. Pinza de tierra del osciloscopio **solo en TP6–TP8**.

## 6. Firmware y datos

- `firmware/`: TIM1 genera el PWM (ARR = 3999 a 80 MHz). El evento de
  actualización dispara el grupo inyectado del ADC (VOUT, VIN; `ScanConvMode`
  **debe** ser ENABLE o el HAL descarta el rango 2). El PI corre en la ISR del ADC:
  Kp = 0.030477, KiTs = 0.0045716 (Ki = 91.43 s⁻¹), anti-windup condicional,
  d ∈ [0, 0.85], CCR con precarga ⇒ retardo de 1.5 Ts como en el diseño. FPU por
  hardware vía `fpu.py` (PlatformIO usa soft-float por defecto).
- Protecciones en la ISR (3 ms): VOUT > 8.5 V, VIN > 13 V, VIN < 9 V. Watchdog
  0.5 s. Arranque suave sin salto (la integral toma el d vigente; la referencia sube
  a 0.05 V/ms).
- Consola serie (115200): `s`, `d`, `step`, `x`, `pi on/off`, `v`, `a`, `b`, `t`,
  `log`, `dump` (2000 muestras por evento: 10 ms antes, 90 ms después), `cal`,
  `vmin`. **`cal` vive en RAM**: repetirla tras cada reinicio (en la E4: multímetro
  5.991 V con ADC 6.000 V → `cal 5.991`).
- `laboratorio/datos/`: `stepC_*`, `stepD_*`, `stepE_table.txt` (puesta en marcha),
  `dynamics_step_*` (escalón de d 0.60↔0.70 para identificar la planta),
  `closed_loop/` (arranque en lazo cerrado), `entrega4/` (24 CSV `<ensayo>_r<n>_{ad3,fw}`
  + `metrics_entrega4.csv` + figura). AD3 a 1 MS/s: CH1 = TRIG, CH2 = VOUT.

## 7. Resultados medidos (para no recalcularlos)

- Puesta en marcha: Vgs 10.8 V encendido / 0.07 V apagado, bootstrap ≥ 11.5 V,
  11 mA en reposo, η 79–85 %.
- Planta identificada: r_L ≈ 0.94 Ω, V_F ≈ 0.26 V (efectivo, con d_ef = d + 0.0053),
  C_ef 14.3–16.7 µF, ωn 10.2–11.1 krad/s, ζ 0.61–0.63, K ≈ 10.25 V por unidad de d.
  Diseño E3: r_L 1.2 Ω, V_F 0.4 V, C 20 µF, ωn 9.5 krad/s, ζ 0.53.
- Márgenes con la planta identificada: MF 97.3°, MG 11.6 dB ⇒ PI sin reajustes.
- E4 (media de 3, osciloscopio corregido al multímetro; entre corchetes, simulación E3):
  6→7 V tr 2.62 ms [2.40], Mp 0.48 % [0.13], ts 4.89 ms [4.53] (una repetición
  5.01 ms; con el ADC del lazo 4.67 ms); 6→5 V tr 2.49 [2.42], Mp 0.53 % [0.08],
  ts 4.55 [4.58]; carga +20 % pico +0.619 V [+0.561], ±20 mV en 1.47 ms [1.68];
  carga −20 % pico −0.759 V [−0.725], ±20 mV en 2.54 ms [2.98]; ess < 1 mV (ADC);
  d máx 0.694. Error rms medición–simulación: 10–16 mV en referencia, 33–43 mV en carga.

## 8. Decisiones y problemas resueltos

- **Por qué Rev C:** la E2 usó un MOSFET canal P (FQP27P06) apagado solo por 1 kΩ
  a Vin; la capacitancia Miller lo hacía re-conducir ~8 veces por periodo y el
  modelo identificado describía ese defecto. Rev C usa canal N con tótem activo.
- Inductores comprados antes del diseño (2 × 330 µH = 660 µH de referencia): no se
  cambian.
- fsw 20 kHz en vez de 10 kHz: rizado de corriente 0.23 A (pico 1.36 A < Isat) y
  de tensión ≈ 0.07 V p-p calculado (medido 0.12–0.13 V por la C efectiva menor);
  inaudible.
- Límite de d = 0.85: a d = 1 el bootstrap se descarga en ~10 ms y Q1 entra en zona
  lineal (~4 W). 0.95 es solo el límite del bootstrap.
- Sin agujeros de montaje (espacio). GND como vertido final en ambas caras; cobre de
  potencia como zonas en F.Cu; teardrops aplicados; DRC con 1 aviso aceptado (silk
  de J1 en el borde).
- Ensamble: JLC PCBA para todo el SMD (Q1 C99124 y L1/L2 C2041412 son Extended);
  a mano: J1–J4 (KF301 5.0 mm), J5/J6, TP1–TP10, C5. Rotación de SOT-23 en el CPL
  corregida 180° (`JLC_ROT_OFFSET` en `make_jlc_files.py`).
- Cables de la fuente: los primeros tenían ~2 Ω (caída de 1.1 V a 0.6 A); usar
  cables gruesos (≈ 0.3 Ω). El lazo compensa la caída, pero reduce el margen de d.
- Térmico: los inductores llegan a ~60 °C a 6 Ω y ~80 °C a 4.8 Ω; mantener corto el
  ensayo de −20 % (en la E4, ~6 s por repetición).

## 9. Cómo verificar rápido

```sh
# Hardware (salidas a una carpeta temporal)
kicad-cli sch erc --severity-all -o /tmp/erc.rpt hardware/kicad/pcb_revC.kicad_sch           # 0 violaciones
kicad-cli pcb drc --severity-all --schematic-parity -o /tmp/drc.rpt hardware/kicad/pcb_revC.kicad_pcb
#   esperado: 0 sin conectar, 0 paridad, 1 aviso (silk_edge_clearance de J1)
python3 -I hardware/herramientas/check_layout.py hardware/kicad/pcb_revC.kicad_pcb --stage S5 --no-export
#   esperado: 0 FAIL (39 PASS, 9 WARN, 1 N/A). MAN-1 y MAN-2 quedan en WARN porque la línea base
#   sin rutear y jlc_spacing.py no se versionaron; la revisión original dio 43 PASS / 7 WARN.

# Firmware
cd firmware && pio run                      # pio run -t upload para programar (ST-Link)

# Análisis e informes
python3 -I analisis/entrega-4/e4_main.py    # regenera resultados/e4_results.json y figuras/informe/
cd informes/entrega-4 && latexmk -pdf entrega_4.tex
# MATLAB: e3_main; e3_figures('report'); e3_figures('slides')  (desde analisis/entrega-3/matlab)
```
