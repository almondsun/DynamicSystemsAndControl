# Evidencia numérica

Todos los datos son de simulación. No son mediciones experimentales.

- `matlab/`: funciones de transferencia, parámetros, márgenes, robustez,
  resultados MAT/JSON y curvas de las seis pruebas.
- `simulink/`: cuatro curvas del modelo entregado `buck_control.slx`.
- `simulation/`: resultados JSON, seis curvas PWM ideal en CSV y gráficas.
- `circuit/<caso>/`: netlist ngspice ejecutado, log y medias de tensión por
  periodo. `convergence/` corresponde al paso máximo de 250 ns.
- Los cinco logs de la raíz registran la ejecución final y las pruebas.
- `manifest.json`: origen de la ejecución y hashes SHA-256 de los archivos
  numéricos, gráficos y logs copiados. Este README no pertenece al manifiesto.

Tiempo en segundos, tensiones en voltios, corriente en amperios, R en ohmios;
dprime es adimensional. Las medias se calculan en periodos de 100 µs y se
ubican en sus centros. Las curvas instantáneas y los detalles de solver están en
`../../artifacts/buck-final-validation-02/simulation/<caso>/waveform.txt`.

Los `results.json` conservan rutas de procedencia de la ejecución original.
Para regenerar informes con esta copia compacta, desde la raíz del repositorio:

```bash
artifacts/buck-tools/venv/bin/python -B project/python/build_reports.py \
  --matlab-results project/results/matlab \
  --analysis-results project/results/simulation \
  --output artifacts/informes-regenerados
```

El directorio de salida debe ser nuevo. Los netlists también pueden ejecutarse
por separado con ngspice; consultar `../circuit/README.md`.
