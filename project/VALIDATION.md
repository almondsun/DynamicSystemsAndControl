# Registro de validación

## Alcance

Validación completa de los entregables numéricos: MATLAB, modelo Simulink,
PWM ideal, circuito ngspice, núcleo C, análisis de capturas y documentos PDF.
Los ensayos físicos no se han realizado.

## Comandos ejecutados

Desde la raíz del repositorio:

```bash
BUCK_MATLAB=/home/mitin/MATLAB/R2026a/bin/matlab \
BUCK_PYTHON="$PWD/artifacts/buck-tools/venv/bin/python" \
BUCK_NGSPICE="$PWD/artifacts/buck-tools/ngspice/usr/bin/ngspice" \
bash project/run_project.sh artifacts/buck-final-validation-02
```

También se ejecutaron `checkcode` sobre los tres archivos MATLAB originales,
`bash -n project/run_project.sh`, análisis de sintaxis de los cinco archivos
Python, pruebas de comparación MATLAB–Simulink y renderizado de los cuatro PDF
con `pdftoppm`. Las unidades y exponentes negativos se revisaron visualmente.

## Resultados ya comprobados

| Comprobación | Resultado |
|---|---|
| MATLAB: signos y destinos de ambos escalones abiertos | PASS |
| MATLAB: cuatro escenarios cerrados | PASS |
| Estabilidad continua y discreta, 27 combinaciones R/L/C | PASS |
| SATK: puertos y conexiones del modelo | healthy |
| Simulink: cuatro escenarios | PASS |
| Modelo exportado como buck_control.slx | PASS |
| PWM ideal: seis escenarios, CCM, regulación y establecimiento | PASS |
| ngspice: seis escenarios | PASS |
| Convergencia 500 ns → 250 ns en d′+0.1 | 0.927 mV máximo en medias de periodo |
| Núcleo C con AddressSanitizer y UndefinedBehaviorSanitizer | PASS |
| Analizador experimental: solución independiente y entradas inválidas | 2 pruebas PASS |
| MATLAB–Simulink, mayor diferencia en las cuatro curvas | 43.42 µV |
| PDFs | Cuatro documentos generados; fórmulas, tablas y figuras inspeccionadas |

La primera evidencia completa por componentes está en
`artifacts/buck-matlab-01/`, `artifacts/buck-analysis-05/`,
`artifacts/buck-simulink-02/` y `artifacts/buck-delivery-validation.log`.
La reproducción conjunta corregida terminó con código de salida **0** y
`PASS: complete numerical run` en `artifacts/buck-final-validation-02/`.
Sus cuatro PDF finales y datos compactos se entregan en `project/reports/final/`
y `project/results/`. Las formas de onda completas permanecen en la carpeta
de esa ejecución; el manifiesto de resultados registra hashes SHA-256.

La distribución local de ngspice emitió `Warning: can't find the initialization
file spinit.` en los siete análisis. El circuito utiliza exclusivamente
dispositivos internos, sin modelos XSPICE cargados desde ese archivo; todos los
análisis finalizaron y pasaron sus comprobaciones. La advertencia se conserva
en cada log. El lote MATLAB final no registró advertencias gráficas ni fallos
de cierre.

## Fallos encontrados y corregidos

- Inicialización CC del PI en ngspice: se fijó explícitamente el estado integral
  inicial a cero. La validación posterior pasó.
- SATK resolvía `Saturation` a una biblioteca no instalada. Se usó el BlockType
  correcto `Saturate`; los chequeos correctos son `unconnected_ports` y
  `unconnected_lines`. El modelo posterior es saludable y simula.
- El cálculo de establecimiento de carga utilizaba una banda diminuta causada
  por el pequeño error inicial. Se fijó la referencia nominal de 6 V y la banda
  de ±0.12 V, según la especificación.
- Un proceso auxiliar de MATLAB retenía la tubería de `tee` después de la
  salida del proceso principal. El ejecutor conserva stdout/stderr en un archivo
  regular y verifica el código de salida. No se ocultaron errores ni se cambiaron
  bibliotecas de MATLAB.
- El primer PDF no dibujaba algunos superíndices Unicode. Se corrigió el
  renderizado de exponentes, sin cambiar las ecuaciones.

El MCP de MATLAB no se pudo conectar a una sesión compartida al comenzar.
Se usó el fallback batch documentado. Las advertencias de los intentos fallidos
siguen en sus logs; no se cuentan como validaciones satisfactorias.

## Límites de la evidencia

- No hay medidas reales de R/L/C, fotografías ni capturas de un montaje.
- Los modelos de semiconductores son genéricos; ESR/DCR son supuestos.
- El C está probado en el computador, sin tarjeta ADC/PWM elegida ni firmware
  integrado, protecciones físicas o pruebas térmicas.
- El PI del circuito es continuo; la implementación digital se prueba con el
  modelo PWM ideal y una latencia definida. Su hardware puede introducir otras.
- El error de regulación se mide sobre medias de periodo; el rizado instantáneo
  es aproximadamente 0.28–0.29 V pico a pico.
- La robustez cubre una malla de 27 puntos, no todas las variaciones posibles.
- La convergencia de paso del circuito se verificó en uno de los dos escalones
  de lazo abierto. No se afirma validación experimental ni de hojas de datos.

## Revisión LaTeX de las cuatro entregas — 14 de septiembre de 2026

Alcance de validación: generación documental completa y verificaciones numéricas
locales. No se modificaron ni se volvieron a ejecutar las simulaciones.

Comandos ejecutados desde la raíz:

```bash
artifacts/buck-tools/venv/bin/python -B project/python/build_reports.py \
  --matlab-results project/results/matlab \
  --analysis-results artifacts/buck-final-validation-02/simulation \
  --output artifacts/buck-latex-final
artifacts/buck-tools/venv/bin/python -B -m unittest discover \
  -s project/python -p 'test_*.py' -v
```

Los cuatro informes compilaron con Tectonic 0.15.0 sin advertencias, referencias
indefinidas, glifos faltantes ni desbordamientos reportados por el compilador.
Pasaron cinco pruebas de Python: dos del analizador experimental y tres de
coherencia numérica, estructura documental y preservación de extremos gráficos.
El generador verificó además las medias finales de los seis archivos de onda
y los seis CSV PWM contra sus resultados JSON. Las métricas no se obtuvieron
de curvas reducidas para visualización.

Se renderizaron e inspeccionaron individualmente las diez páginas finales a
1500 píxeles de altura. Las imágenes están en
`artifacts/buck-final-page-review/`; los logs finales se conservan en
`artifacts/buck-latex-final/` y `artifacts/buck-latex-final-build.log`.

| Documento | Páginas revisadas | Elementos comprobados |
|---|---|---|
| Entrega 1 | 1, 2, 3 | Autores, polaridad de la fuente, driver, estados ON/OFF, matrices, transferencia, dinámica, errores, ambos escalones y referencias |
| Entrega 2 | 1, 2 | Parámetros medidos pendientes, modelo ajustado, ecuaciones de error, dos tablas experimentales y apéndice |
| Entrega 3 | 1, 2, 3 | Signo del lazo, derivación PI, Bode junto al diseño, anti-windup, temporización, cuatro casos, tablas y orden de referencias |
| Entrega 4 | 1, 2 | ADC, calibración, integración discreta, coeficientes cargados pendientes, reajuste y cuatro pruebas físicas |

La inspección visual corrigió problemas que el compilador no detectó: polaridad
del símbolo de fuente, ancho de una ecuación y orden de lectura de figuras y
bibliografía. Las fuentes TeX y los CSV gráficos acompañan los PDF para permitir
edición y recompilación. Los datos experimentales y la integración física siguen
pendientes; no se sustituyeron con datos simulados.
