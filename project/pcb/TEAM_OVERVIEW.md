# Estado para el equipo

Ya tenemos un diseño original de PCB de dos capas, el firmware del STM32,
una lista de compra y un protocolo de laboratorio. Los archivos editables,
las imágenes y las comprobaciones están incluidos en este paquete.

**Comenzar por estos archivos:**

1. `release/gerber-top.png`: aspecto de la placa exportada.
2. `release/schematic.pdf`: esquema eléctrico de cinco páginas.
3. `docs/purchasing.md` y `purchasing.csv`: componentes, repuestos y presupuesto.
4. `docs/assembly-and-tests.md`: cableado, banco de carga y ensayos.
5. `../firmware/README.md`: programación y captura.

Las comprobaciones de CAD pasan sin violaciones ni conexiones pendientes.
El firmware compila y sus pruebas pasan. Esto sigue siendo **validación en
computador**: falta probar los componentes y el circuito físico.

El objetivo sigue siendo COP 350 000 entre cuatro: COP 87 500 por persona.
El desglose actual estima COP 281 502 antes de contingencia; el envío de PCB
y varios precios deben confirmarse. No se ha hecho ningún pedido.

**Siguiente paso del equipo:** conseguir/verificar componentes críticos y
hacer el prototipo soldado en laboratorio. Las bobinas y los capacitores
deben coincidir con las huellas antes de encargar las PCB. Después se compara
el costo entregado de PCBWay y JLCPCB y se libera la fabricación.

Las entregas 1 y 3 conservan sus simulaciones originales. Las entregas 2 y 4
solo se completarán con mediciones reales y tres repeticiones de cada ensayo.
# Actualización de informes y vistas CAD

Compartir `release/hardware-appendix.pdf` junto con las cuatro entregas de `../reports/final/`. El ZIP de revisión incluye esos documentos, sus fuentes, CAD, modelos 3D, firmware y evidencia numérica compacta. El anexo muestra vistas CAD reales y distingue envolventes provisionales de componentes calificados; no hay fotografías ni mediciones de hardware todavía.

La revisión completa de la guía y la secuencia de trabajo están en `docs/requirements-audit.md`. Prioridad inmediata: cerrar componentes y validar prototipo soldado antes de liberar fabricación. Las entregas experimentales 2 y 4 suman 60% del peso del proyecto y siguen pendientes de laboratorio.
