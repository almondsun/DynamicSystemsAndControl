# Dynamic Response 2 simulations

## Versión en español

**Respuesta_Dinamica_2_Simulaciones_ES.pdf** incluye el informe traducido,
once capturas de las diapositivas originales, gráficas en español y análisis
de polos y ceros para todos los casos. Se distinguen las transferencias de las
transformadas de salida y el comportamiento de cada salida física.

```matlab
results = run_respuesta_dinamica_2();
```

Para regenerar el informe español a partir de esa ejecución:

```sh
python build_report_es.py /ruta/devuelta/en/results.outputDir
```

Este generador también requiere `pymupdf` y acceso al PDF original en
`classroom/`. La versión española se validó en MATLAB R2026a: 19 comprobaciones
numéricas aprobadas y ninguna incidencia de Code Analyzer. Se calcularon polos
y ceros para 12 funciones de transferencia. Los resultados numéricos coinciden
con la versión inglesa. La ejecución y sus datos están en
`artifacts/dynamic_response_2/spanish_run/`; el registro de MATLAB está en
`artifacts/dynamic_response_2/matlab_spanish.log`.

## English version

Open **Dynamic_Response_2_Simulations.pdf** for all eleven simulation cases,
MATLAB code, input/output plots and brief analysis. Cases cover every distinct
worked system in `classroom/4 Dynamic Response 2.pdf`, including both motor
outputs and both satellite pulse inputs. General transform tables are not
additional simulation cases.

From this folder in MATLAB (Control System Toolbox required):

```matlab
results = run_dynamic_response_2();
```

Each default run creates a timestamped directory in
`artifacts/dynamic_response_2/` with eleven PNG figures, `simulation_data.mat`
and `validation.json`. It performs 19 numerical assertions and preserves
existing workspaces and figures. Figures are exported without opening windows;
open the PNGs to view them or load the MAT file for further plotting.

The report uses seconds, labeled physical units and explicit initial conditions.
The abstract ODE examples use selected initial values of 1 and 0.5 where the
slides leave them symbolic. The car uses a 500 N step and the motor a 1 V step.
Satellite pulses are held exactly over [5,5.1) and [6.1,6.2) seconds.

To rebuild the PDF from a completed MATLAB run:

```sh
python build_report.py /absolute/path/to/results.outputDir
```

The PDF builder requires `reportlab` and Liberation Sans/Mono TrueType fonts
under `/usr/share/fonts/liberation/`. In this workspace, an isolated environment
is available as `artifacts/dynamic_response_2/venv/bin/python` relative to the
repository root. The builder replaces only this generated report.

Validation used MATLAB R2026a Update 5 in a separate batch process because the
shared MCP session was unavailable. All 19 assertions passed and MATLAB Code
Analyzer returned no issues. MATLAB warned that graphics acceleration hardware
was unavailable; plot exports succeeded and the process exited with status 0.
The PDF was text-checked and visually inspected after rendering.

Validation scope: narrow local (new simulations and their report). The final
MATLAB command was:

```sh
/home/mitin/MATLAB/R2026a/bin/matlab -batch "addpath('/home/mitin/code/uni/DynamicSystemsAndControl/simulations/dynamic_response_2'); assert(isempty(checkcode('run_dynamic_response_2.m','-id'))); results=run_dynamic_response_2('/home/mitin/code/uni/DynamicSystemsAndControl/artifacts/dynamic_response_2/release_run');" -logfile /home/mitin/code/uni/DynamicSystemsAndControl/artifacts/dynamic_response_2/matlab_release.log
```

PDF checks: `pdfinfo`, `pdftotext -layout`, rendered-page inspection and a
PyMuPDF check for all 14 pages, 11 plot images and no text outside page bounds.
These are numerical model results, not experimental hardware validation.
