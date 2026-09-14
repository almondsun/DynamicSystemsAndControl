# Validación de la revisión A — 14 de septiembre de 2026

**Validation scope: escalated.** PCB generada, interconexión eléctrica,
firmware bare-metal, temporización, archivos de fabricación y protecciones.
Estado: paquete de revisión generado y comprobado; **sin aprobación de
fabricación ni pruebas físicas**.

## Passed

| Comprobación ejecutada | Resultado |
|---|---|
| KiCad ERC | 0 errores, 0 advertencias |
| KiCad DRC | 0 violaciones, 0 pads sin conexión |
| KiCad comparación esquemático/PCB | 0 diferencias |
| Auditoría independiente de conectividad | 57 componentes; 152 pads conectados coinciden con esquema y definición |
| Geometría y máscara | 99 × 99 mm, dos capas; pads de L1/L2 accesibles para soldadura |
| Ruteo | Potencia 0.60 mm; señales 0.30 mm; escapes locales de U6 de 0.36/0.225 mm; cuatro vías 1.20/0.60 mm |
| Latch NAND | Prioridad de disparo, retención y RUN bajo comprobados por tabla de estados |
| Lectura Gerber independiente | Gerbonara 1.6.3: dos capas, máscara, contorno y 158 taladros metalizados; cero no metalizados |
| Firmware ARM | GCC 16.2.0, Cortex-M3; ELF/BIN/HEX enlazados, sin advertencias de compilación |
| Memoria enlazada | 5309 bytes de texto, 0 de datos inicializados, 6288 de BSS; límite flash 64 KB/RAM 20 KB y reserva stack ≥4 KB |
| Pruebas C | Núcleo PI y runtime; AddressSanitizer/UBSan para runtime |
| Captura UART | Cuatro pruebas: unidades/timestamps, registros perdidos, timestamps repetidos y falla |
| Simulación PCB aislada | Seis escenarios completados, sin disparos simulados; error final PI <20 mV |
| Convergencia numérica | Máxima diferencia entre medias de periodo a 0.5/0.25 µs: 1.345 mV en ref_up |
| Revisión visual | Cinco páginas de esquemático, una de montaje y ambas caras de Gerbers inspeccionadas |

La corriente pico máxima de la estimación conmutada fue **1.549272 A** en
load_down. Las referencias se establecieron alrededor de 4.3 ms; los cambios
de carga, alrededor de 0.8/0.9 ms, bajo los supuestos documentados. El ajuste
físico puede cambiar estos resultados. Los CSV y JSON están en
`release/simulation/`; no son datos experimentales.

El cálculo estático conservador entrega disparo de corriente entre
**1.825 y 2.184 A** y OVP entre **7.561 y 8.867 V** por tolerancias. No deben
presentarse 2 A y 8.2 V como límites exactos garantizados. La simulación usa
los umbrales nominales; el cálculo de tolerancia se comprueba por separado.

## Commands run

Desde la raíz del repositorio, herramientas locales aisladas en `artifacts/`:

```sh
source project/pcb/tools/local_env.sh
/usr/bin/python project/pcb/tools/generate.py
/usr/bin/python project/pcb/tools/finish_board.py artifacts/buck-pcb-validation/buck.ses
bash project/pcb/tools/export_review.sh
artifacts/buck-tools/venv/bin/python project/pcb/tools/check_gerbers.py
make -C project/firmware all test
python -m unittest discover -s project/firmware -p 'test_capture.py' -v
python project/pcb/simulation/validate.py
```

Ruteo ejecutado, con GUI, servidor API y telemetría deshabilitados:

```sh
java -Djava.awt.headless=true -jar artifacts/buck-tools/freerouting.jar \
  --gui.enabled=false --usage_and_diagnostic_data.disable_analytics=true \
  --api_server.enabled=false -de project/pcb/buck.dsn \
  -do artifacts/buck-pcb-validation/buck.ses -mp 20 -mt 2
```

`export_review.sh` ejecuta ERC/DRC con `--exit-code-violations`, y DRC además
con `--schematic-parity`. Exporta netlist XML y ejecuta `verify.py` antes de
producir PDF, Gerbers, taladros y vistas. El reporte DRC conserva la lista
de comprobaciones ignoradas por defecto; no se añadieron exclusiones para
ocultar violaciones del diseño.

Los registros completos se conservaron en `artifacts/buck-pcb-validation/`:
`export.log`, `routing.log`, `gerber-check.log`, `generate-final.log`,
`firmware-final.log`, `simulation-final.log`, informes ERC/DRC y JSON.
Las pruebas de captura imprimieron sus cuatro resultados correctos en la
consola. Las imágenes de revisión también permanecen allí.

## Failed / resolved

- La instalación de sistema no pudo usar sudo sin contraseña. Se descargaron
  y extrajeron KiCad y GCC ARM localmente; no se modificó el escritorio.
- Las primeras comprobaciones detectaron problemas del generador, separación
  física, serigrafía y metadatos de pines no conectados. Se corrigieron y se
  repitieron las comprobaciones hasta el resultado final indicado arriba.
- El primer ensayo de convergencia cuantizaba el flanco PWM al paso del
  integrador. Se resolvieron fracciones de paso y se repitieron los escenarios.
- KiCad local emite advertencias de inicialización SWIG y la ausencia de
  `/usr/share/kicad/schemas/api.v1.schema.json`. Están conservadas en los logs.
  ERC/DRC/exportación devolvieron éxito; los Gerbers se verificaron también
  con otro lector. No se validó el servidor API de KiCad.

## Not run / remaining unverified

- Programación de un STM32 real, autenticidad del MCU, reloj, ADC/DMA,
  duración ISR, fase PWM y latencia medidas. La compilación no acredita
  temporización física.
- Cotización final entregada de PCBWay/JLCPCB, disponibilidad real, MPN
  definitivos de capacitores, geometría/DCR/Isat de inductores y huellas
  contra componentes recibidos.
- Prototipo soldado, montaje, respuesta bootstrap, error de sensado y
  conexiones Kelvin efectivas, temperatura, rizado, EMI, umbrales reales,
  reset, watchdog y respuesta a falla del hardware.
- Repeticiones de laboratorio y ajuste de los informes 2 y 4. Los documentos
  y resultados previos del curso no se sustituyeron por esta estimación.

Estos puntos retienen la liberación de fabricación. El ZIP comparte un
resultado revisable, no evidencia de que una placa haya sido fabricada o funcione.
