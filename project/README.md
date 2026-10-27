# Proyecto final: convertidor Buck

Proyecto basado en `classroom/Descripcion Proyecto Buck.pdf`. Están desarrolladas
las entregas de simulación 1 y 3. Las entregas 2 y 4 incluyen metodología y
herramientas de análisis, pero requieren construir el convertidor y obtener
mediciones reales; no se presentan datos inventados.

## Documentos y modelo

La selección SMD para JLCPCB se documenta en la [auditoría de componentes del Buck](pcb/audit/README.md): inventario, requisitos eléctricos y térmicos de los 35 pasivos, candidatos comerciales y bloqueos. Es una revisión documental posterior al diseño original; no aprueba componentes ni fabricación y no recalifica los resultados históricos para SMD.

| Entrega | Archivo | Estado |
|---|---|---|
| 1. Modelo y simulación | [Informe PDF](reports/final/entrega_1.pdf) · [Fuente LaTeX](reports/final/entrega_1.tex) | Simulación completada |
| 2. Lazo abierto experimental | [Documento PDF](reports/final/entrega_2.pdf) · [Fuente LaTeX](reports/final/entrega_2.tex) | Ensayos físicos pendientes |
| 3. Diseño del PI | [Informe PDF](reports/final/entrega_3.pdf) · [Fuente LaTeX](reports/final/entrega_3.tex) | Simulación completada |
| 4. Controlador implementado | [Documento PDF](reports/final/entrega_4.pdf) · [Fuente LaTeX](reports/final/entrega_4.tex) | Integración y ensayos físicos pendientes |

- [Modelo Simulink](models/buck_control.slx): PI, saturación, anti-windup,
  driver inversor y planta promediada. Parámetros guardados en el workspace del modelo.
- [Circuito ngspice](circuit/buck.cir.in) y [descripción](circuit/README.md).
- [Implementación y protocolo de laboratorio](hardware/implementacion.md).
- [Núcleo C del controlador](hardware/buck_control.c): validado en computador;
  [adaptador STM32F103](firmware/README.md) compilable, con validación en computador;
  falta verificarlo en la tarjeta física.
- [PCB, lista de compra y protocolo de montaje](pcb/README.md): diseño KiCad
  de revisión; fabricación retenida hasta calificar componentes y prototipo.
- [Contrato de datos experimentales](data/README.md) y
  [analizador](python/analyze_experiment.py).
- [Registro de validación](VALIDATION.md).
- [Datos y evidencia numérica](results/README.md): CSV, MAT, JSON, netlists y logs.

## Parámetros y resultados

Vin=12 V, L=660 µH, C=20 µF, R=6 Ω, PWM=10 kHz. La figura del proyecto usa
660 µH; el valor 270 µH de `Ej_Buck.m` corresponde a otro ejemplo.

La entrada es **d′=1−d**. Aumentar d′ reduce la tensión. La planta incremental es

```text
Gd′(s) = −12 / (1.32e−8 s² + 1.10e−4 s + 1)
```

El PI actúa sobre el duty físico con Kp=0.0261655286 V⁻¹ y
Ki=78.4965859 (V·s)⁻¹; la salida lógica es d′=1−d. El diseño continuo tiene
102.07° de margen de fase y 4.83 ms de establecimiento nominal.

Los seis escenarios PWM/ngspice y los cuatro de Simulink pasan. En ngspice,
los cambios 6→7 V y 6→5 V se establecen en 4.95 ms (banda ±20 mV sobre medias
de periodo). Los cambios de R ±20% se establecen en 0.65 ms (banda ±0.12 V).
La diferencia por reducir el paso de ngspice a la mitad es 0.927 mV.

En lazo abierto, el circuito con pérdidas queda unos 0.30 V por debajo del
modelo ideal. El rizado es aproximadamente 0.28–0.29 V pico a pico. Los
semiconductores de ngspice son genéricos y DCR/ESR son supuestos explícitos;
estos resultados no certifican un montaje físico.

## Abrir y simular en MATLAB

Desde la raíz del repositorio:

```matlab
open_system('project/models/buck_control.slx')
in = Simulink.SimulationInput('buck_control');
in = in.setVariable('RefFinal',5,'Workspace','buck_control');
in = in.setVariable('RFinal',6,'Workspace','buck_control');
out = sim(in);
plot(out.buck_signals.Time, out.buck_signals.Data(:,1))
xlabel('Tiempo (s)'); ylabel('Tensión de salida (V)'); grid on
```

Para los otros escenarios elegir (RefFinal,RFinal): (7,6), (6,7.2), (6,4.8).
Las cuatro columnas registradas son tensión, corriente, d′ y referencia.
Condición inicial: 6 V y 1 A; evento a 10 ms; tiempo final 30 ms; ode45,
RelTol=1e-8, AbsTol=1e-10, MaxStep=10 µs. No se borra el workspace del usuario.

## Reproducir todo

Requisitos: MATLAB/Simulink/Control System Toolbox R2026a, ngspice 44.2,
Python 3.14 con [requirements.txt](python/requirements.txt), GCC y Tectonic
0.15.0 para los PDF LaTeX. No se necesitan Simscape, Simulink Test ni
Simulink Control Design. La reconstrucción estructural opcional utiliza el
toolkit oficial SATK, mediante `build_buck_model.m`; el modelo ya entregado
puede simularse sin SATK.

Con las herramientas disponibles en esta máquina:

```bash
BUCK_MATLAB=/home/mitin/MATLAB/R2026a/bin/matlab \
BUCK_PYTHON="$PWD/artifacts/buck-tools/venv/bin/python" \
BUCK_NGSPICE="$PWD/artifacts/buck-tools/ngspice/usr/bin/ngspice" \
bash project/run_project.sh
```

En otra máquina, instalar las dependencias de Python en un entorno virtual y
usar rutas propias o los ejecutables `matlab`, `python` y `ngspice` del PATH.
La distribución local de ngspice está extraída en `artifacts/buck-tools/`, sin
cambiar paquetes del sistema. Sus bibliotecas se seleccionan sólo para el
subproceso ngspice; no se cambian las bibliotecas de MATLAB.

El ejecutor crea una carpeta nueva bajo `artifacts/`, guarda CSV, MAT, JSON,
netlists por caso, formas de onda, logs, pruebas y PDF. Si se pasa una carpeta
ya existente, se detiene para evitar sobrescrituras. Ejemplo:
`bash project/run_project.sh artifacts/mi-nueva-ejecucion`.

## Completar las entregas físicas

Seguir `hardware/implementacion.md`: medir R/L/C y pérdidas; construir y
verificar la etapa de potencia y driver; elegir tarjeta; integrar ADC/PWM;
capturar dos ensayos de lazo abierto y cuatro de lazo cerrado con repeticiones.
Después, incorporar las mediciones y conclusiones a los documentos 2 y 4.
El analizador no convierte nominales de simulación en parámetros medidos.

## Reconstruir sólo los informes

Los cuatro PDF usan IEEEtran, ecuaciones LaTeX numeradas, CircuitikZ y gráficas
vectoriales PGFPlots. Las fuentes editables principales son `entrega_N.tex`;
los `.md` son compañeros con delimitadores matemáticos. Los autores aparecen
tanto en el documento como en los metadatos PDF. Las entregas 2 y 4 siguen
identificadas como metodologías con resultados experimentales pendientes.

El compilador local está en `artifacts/buck-tools/tectonic/tectonic`. Se puede
seleccionar otro con `BUCK_TECTONIC` o `--tectonic`. La primera compilación
necesita acceso a Internet para llenar la caché de paquetes de Tectonic.
El binario oficial utilizado es `tectonic-0.15.0-x86_64-unknown-linux-musl.tar.gz`,
de [la publicación 0.15.0](https://github.com/tectonic-typesetting/tectonic/releases/tag/tectonic%400.15.0).
SHA-256 del archivo descargado:
`dfb82876f2986862996e564fa507a9e576e0c1e3bee63c2c1bd677c2543e6407`.

```bash
artifacts/buck-tools/venv/bin/python -B project/python/build_reports.py \
  --matlab-results project/results/matlab \
  --analysis-results artifacts/buck-final-validation-02/simulation \
  --output artifacts/mis-informes-latex
```

La carpeta de salida debe ser nueva. Para reconstruir desde simulaciones se
requieren sus `waveform.txt`, además de JSON y CSV PWM, para obtener el detalle
instantáneo del rizado. Esto no vuelve a ejecutar MATLAB ni ngspice. Las fuentes
TeX entregadas también pueden compilarse directamente desde `reports/final/`:

```bash
../../../artifacts/buck-tools/tectonic/tectonic --keep-logs entrega_1.tex
```

El generador conserva los datos gráficos en `data/`, verifica coherencia de
parámetros y rechaza glifos faltantes, referencias indefinidas y desbordamientos.
La reducción de puntos retiene extremos por intervalo y extremos temporales;
las métricas proceden de resultados completos, sin recalcularlas sobre gráficos.
Validación de Python: `python -B -m unittest discover -s project/python -p 'test_*.py' -v`.
