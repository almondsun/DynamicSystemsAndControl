# Buck: PCB y controlador STM32 — revisión A

**Paquete de ingeniería para revisión. Fabricación retenida hasta completar
la calificación de componentes y el prototipo soldado.** No se ha comprado,
fabricado, ensamblado ni probado físicamente esta tarjeta.

El diseño original conserva 12 V, 660 µH, 20 µF, 6 Ω y PWM de 10 kHz del
proyecto de Sistemas Dinámicos y Control. Emplea dos inductores de 330 µH en
serie, IR2110, MOSFET IRFZ44N, rectificación 1N5822 y una Blue Pill externa.
El controlador PI conserva la interfaz existente `buck_update` en voltios y
la salida invertida **d′ = 1 − d**. La protección por corriente y tensión
es independiente del programa del STM32.

## Archivos para compartir con el equipo

- [Auditoría SMD/JLCPCB e índice de documentación actual](audit/README.md): inventario de 57 referencias, requisitos calculados de los 35 pasivos y selección comercial pendiente.
- [Bloqueos antes de cambiar el circuito o fabricar](audit/open_issues.md) y [comportamiento esperado y pruebas](audit/expected_behavior.md). Los resultados de revisión A que siguen abajo son históricos; no constituyen una validación de los nuevos candidatos SMD.
- [Organización de documentos y bibliotecas descargadas](audit/organization_by_type.md) y [uso del organizador local](docs/vendor-assets-organizer.md). Las descargas originales y bibliotecas comerciales permanecen fuera de Git.

- [Anexo visual de hardware](release/hardware-appendix.pdf): 3D, plano, conexiones y esquemas completos.
- [Cuatro informes IEEE actualizados](../reports/final/) y [auditoría de requisitos](docs/requirements-audit.md).
- [Vista 3D isométrica](release/report-assets/pcb-3d.png) y [superior](release/report-assets/pcb-top.png). Son vistas CAD; geometría de inductores y referencias de capacitores pendientes de calificación.
- [Paquete ZIP completo](release/buck-team-review.zip) y [resumen para el equipo](TEAM_OVERVIEW.md).
- [Esquemático PDF](release/schematic.pdf) y [proyecto KiCad](buck.kicad_pro).
- [Vista frontal](release/board-front.png), [vista posterior](release/board-back.png)
  y [plano de montaje](release/assembly.pdf).
- [BOM de la placa](bom.csv) y [lista de compra con reservas](purchasing.csv).
- [Presupuesto y proveedores](docs/purchasing.md).
- [Montaje, conexiones y ensayos](docs/assembly-and-tests.md).
- [Firmware y programación](../firmware/README.md).
- [Resultados de validación y límites](VALIDATION.md).
- [Archivos de fabricación para revisión](release/fabrication-review/).

Los Gerbers son una exportación de revisión, **no una autorización para
encargar placas**. La geometría de L1/L2 es provisional: cuerpo máximo
25 mm, separación de terminales 10 mm, agujero 1.3 mm. Una bobina comercial
rotulada «330 µH, 5 A» no acredita esta geometría ni su corriente de saturación.
También deben cerrarse referencias exactas de los capacitores antes del pedido.

## Construcción y reproducción

Para actualizar las ilustraciones con las herramientas locales: `bash project/pcb/tools/render_review.sh`.
Esto adjunta modelos locales al PCB existente; no regenera ni enruta la placa. Tras ejecutar `generate.py`, repetir la importación de ruta y luego este paso de modelos. Ejecutar `export_review.sh` para comprobar ERC/DRC/paridad.
Los modelos estándar conservan su licencia oficial en `models/LICENSE-KiCad.md`; `models/manifest.json` registra procedencia y SHA-256. Las envolventes de inductores se generan en `prepare_3d.py` y no son modelos de fabricante.

Los informes se reconstruyen con `project/python/build_reports.py` y los resultados completos guardados, según el README del proyecto. La fuente del anexo es `docs/hardware-appendix.tex`; compilar desde `release/` para resolver los PDF y figuras incluidos. Los CSV compactos del ZIP permiten revisar resultados y ejecutar pruebas; regenerar las gráficas de rizado requiere las ondas completas de la ejecución original.

KiCad 10.0.6, bibliotecas estándar de KiCad y Python `pcbnew`; GCC ARM para
STM32. Las bibliotecas propias están dentro de esta carpeta. No se necesita
una licencia comercial de CAD. El STM32 y su programador no están integrados
en la placa, por lo que pueden reemplazarse sin rehacerla.

`tools/design.py` contiene la conectividad, numeración de pines y colocación.
`tools/generate.py` genera los archivos editables y el DSN. **Regenerar reemplaza
los archivos CAD generados**: conservar por separado cualquier revisión manual.
`tools/finish_board.py` importa la sesión de Freerouting y añade el plano GND.
Las comprobaciones finales y sus comandos están en `VALIDATION.md`.

El circuito de `simulation/` es una estimación con pérdidas y el código real
del controlador; no reemplaza el modelo Simulink ni los resultados originales.
Los informes de las entregas 2 y 4 siguen pendientes de evidencia experimental.

## Especificación de fabricación propuesta

99 × 99 mm; 2 capas; FR-4 de 1.6 mm; cobre de 1 oz; máscara verde;
acabado HASL sin plomo o estándar según el presupuesto; cinco placas desnudas;
sin montaje, stencil ni opciones premium. Señales de 0.30 mm, conexiones de
potencia de 0.60 mm y plano GND posterior; separación de ruteo 0.25 mm;
vías de 1.20/0.60 mm. Verificar calentamiento y caídas de tensión en banco:
estas dimensiones no sustituyen la validación térmica.
La salida GND de baja corriente de U6 incluye un escape local de 0.36 mm.
Su salida ISENSE incluye dos segmentos locales de 0.225 mm entre pads SOT23.

No hay orificios para chasis. Sujetar la placa por sus bordes con un soporte
aislante; los inductores pesados necesitan fijación aislante que no obstruya
la refrigeración. Nunca apoyar la cara inferior sobre una superficie metálica.
