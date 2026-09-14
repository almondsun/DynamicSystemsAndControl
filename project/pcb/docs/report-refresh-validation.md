# Validación de la actualización de informes

Fecha: 14 de septiembre de 2026. Alcance: validación de generación, documentos y paquete; comprobación CAD tras adjuntar modelos 3D. No se modificaron ecuaciones, ganancias, firmware ni trazado eléctrico.

## Comandos ejecutados

Desde la raíz del repositorio, con las herramientas locales existentes:

```bash
bash project/pcb/tools/render_review.sh
bash project/pcb/tools/export_review.sh
artifacts/buck-tools/venv/bin/python project/pcb/tools/check_gerbers.py
artifacts/buck-tools/venv/bin/python -B -m unittest discover -s project/python -p 'test_*.py' -v
artifacts/buck-tools/venv/bin/python -B project/python/build_reports.py --matlab-results artifacts/buck-final-validation-02/matlab --analysis-results artifacts/buck-final-validation-02/simulation --output artifacts/buck-hardware-reports-04
```

Desde `project/pcb/release/`:

```bash
../../../artifacts/buck-tools/tectonic/tectonic --keep-logs --keep-intermediates --outdir . ../docs/hardware-appendix.tex
```

Empaquetado desde la raíz: `/usr/bin/python project/pcb/tools/package_review.py`.

## Resultado

- Seis pruebas de contratos de informes y análisis experimental superadas. Comprobación de autores, referencias, matemáticas, consistencia numérica, figuras externas, separación de evidencia y rechazo de datos experimentales inválidos.
- Cuatro informes compilados: 3, 3, 4 y 3 páginas. Anexo de 11 páginas, incluyendo cinco hojas vectoriales nativas de KiCad.
- Revisión visual de las 24 páginas: fórmulas LaTeX, diagramas, tablas, leyendas y límites de la evidencia. Se corrigieron modelos 3D ausentes, normales de la envolvente provisional, tamaño del diagrama de potencia, salto de párrafo de tabla y separadores del encabezado.
- ERC, DRC y paridad esquema–placa sin infracciones; comprobaciones de 57 componentes, 152 pads conectados, cuatro vías y placa de dos capas de 99 × 99 mm superadas. Verificación independiente de Gerbers superada.
- ZIP con manifiesto SHA-256 y CRC comprobados por el empaquetador.

Los logs finales no contienen desbordamientos LaTeX, caracteres ausentes ni referencias sin resolver. Se conserva una advertencia al leer el PDF vectorial 1.7 durante la fase de inclusión configurada inicialmente como 1.5; el PDF resultante es 1.7 y fue inspeccionado. El entorno local también informa de esquema API KiCad ausente, aserciones de enumeraciones de pcbnew y advertencias de Fontconfig. No se ocultaron errores: la primera compilación del anexo falló por rutas relativas y la primera versión tenía un desbordamiento de tabla; ambos se corrigieron antes de la entrega.

## No ejecutado nuevamente

No se repitieron MATLAB, ngspice, simulación C ni compilación de firmware porque sus fuentes y parámetros no cambiaron. Los informes citan los resultados guardados, distinguiendo la simulación BJT original de la estimación adicional IR2110/STM32. La procedencia del CAD y los modelos consta en los manifiestos del paquete y de `models/`.

## Pendiente

Calificación comercial y dimensional de componentes, saturación y rizado admisible; prototipo soldado; fabricación, montaje, programación del MCU, calibración, temporización, protección, térmica y 18 registros de laboratorio propuestos. Ningún render ni chequeo CAD reemplaza esas pruebas. Fabricación retenida.
