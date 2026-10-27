# Auditoría de componentes Buck y preparación SMD/JLCPCB

Documentación de trabajo consolidada el **2026-10-24**, en la rama **Kicad-PCB**.
La BOM original sigue siendo [bom.csv](../bom.csv). Se mantienen separados el
inventario de archivos, la selección comercial y la aprobación técnica.
**La fabricación y el rediseño eléctrico continúan pendientes de revisión.**

## Lectura recomendada para decidir la siguiente fase

|Documento|Contenido y alcance|
|---|---|
|[Requisitos de pasivos](passives_requirements.md)|Documento principal: 35 referencias originales, funciones, cálculos eléctricos y térmicos, escenarios y propuestas todavía no incorporadas|
|[Comportamiento esperado](expected_behavior.md)|Predicciones ideales y con pérdidas, criterios propuestos, protecciones y plan de ensayos; distingue resultados históricos de pruebas nuevas|
|[Candidatos JLCPCB/LCSC](jlc_passives_candidates.md)|MPN, códigos, fuentes, encapsulados y limitaciones; stock vigente NO VERIFICADO|
|[Cumplimiento de datasheets](datasheet_compliance.md)|Relación entre pasivos y condiciones de los IC/semiconductores; páginas y secciones, recomendaciones e hipótesis|
|[Bloqueos abiertos](open_issues.md)|Checklist CRÍTICO/MAYOR/MENOR y evidencia necesaria para aprobar cambios o fabricación|

La revisión cubre los escalones originales de duty, referencia y carga. La
envolvente VIN±10%, el caso combinado 7 V/4.8 Ω y los márgenes adicionales son
propuestas de ingeniería, no requisitos atribuidos a la guía del curso.
El rechazo de candidatos preliminares de entrada y las reservas sobre bootstrap,
saturación, energía del inductor, ADC y térmica deben resolverse antes del layout.

## Inventario y organización ya realizados

|Documento o matriz|Uso|
|---|---|
|[Inventario por referencia](component_inventory.csv)|57 referencias: 48 comprables y 9 puntos de prueba; estado de archivos y selección de la primera reconciliación|
|[Faltantes de componentes y archivos](missing_components.md)|Checklist del inventario inicial; revisar junto con los bloqueos posteriores de pasivos|
|[Candidatos del inventario inicial](jlc_candidates.csv)|Investigación preliminar anterior a los cálculos de pasivos; no es una BOM aprobada|
|[Informe de organización](organization_report.md)|Fuentes, operaciones, hashes, recuentos y límites de inspección|
|[Vista por tipo de archivo](organization_by_type.md)|Datasheets juntos y CAD separado por símbolos, footprints y modelos3D|
|[Ambigüedades del inventario](unresolved_issues.md)|Identidades, archivos ajenos a la BOM, bibliotecas propietarias y otras discrepancias|
|[Procedencia de archivos](asset_manifest.csv)|Orígenes, miembros ZIP, destinos y SHA-256 de las copias organizadas|
|[Assets originales del proyecto](existing_project_assets.csv)|Bibliotecas preexistentes para revisar posible reutilización|
|[Verificación del inventario](verification_results.json)|Resultados y hashes de aquella ejecución, con rutas locales de procedencia|
|[Organizador y procedimiento](../docs/vendor-assets-organizer.md)|Herramienta de copia/verificación local; sus pruebas utilizan archivos sintéticos|

Los recuentos del inventario describen los archivos encontrados en su momento.
Los candidatos y conclusiones eléctricas posteriores están en los documentos de
pasivos. Un enlace a un datasheet no significa que ese PDF esté descargado;
una biblioteca completa tampoco significa un componente aprobado. No actualizar
automáticamente la matriz histórica usando candidatos nuevos como seleccionados.

## Fuentes y evidencia que acompañan al repositorio

El Excel fuente es `Auditoria_preliminar_Buck_JLCPCB_2026-10-22.xlsx`, hoja
`BOM auditada`. Su ubicación y SHA-256 se conservan en el informe de organización.
Se leyó sin modificarlo. El Excel, los datasheets comerciales y las descargas
CAD permanecen locales en Descargas o `../vendor_assets_local/`; no se incluyen
en Git ni se sustituyen por datos inventados.

La carpeta [evidence/](evidence/README.md) conserva resultados compactos de los
cálculos, trazabilidad de las 35 referencias y hashes de las ocho huellas
inspeccionadas. Son metadatos y cálculos propios, sin redistribuir bibliotecas
o datasheets. Las ejecuciones completas y scripts temporales permanecen en
`artifacts/passives_20261024/`, ignorado por Git. Las menciones a esa ruta en
los informes originales indican evidencia local; sus resultados compactos se
incluyen aquí para que la revisión no dependa exclusivamente de ese directorio.

## Estado del repositorio y de la validación

La consolidación documental conserva los cambios KiCad locales existentes;
no los integra como una revisión eléctrica aprobada. No modifica la BOM,
`tools/design.py`, el firmware, las asignaciones de footprints ni el circuito.
Las exportaciones, ERC/DRC y simulaciones de [VALIDATION.md](../VALIDATION.md)
son resultados históricos de revisión A, no comprobaciones nuevas del SMD.
La exportación reciente de netlist falló por acceso a configuración de KiCad;
los cálculos usan lectura estática y esa limitación está documentada.

Consultar [repo_update_review.md](repo_update_review.md) para la comprobación
de rama, solapamientos con el remoto, exclusiones y verificaciones de esta
actualización. No ejecutar generadores de KiCad para actualizar estos documentos.
