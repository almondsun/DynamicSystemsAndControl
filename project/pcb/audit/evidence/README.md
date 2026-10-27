# Evidencia compacta de la auditoría de pasivos

Copias de resultados propios generados el2026-10-24. No contienen datasheets,
símbolos, footprints ni modelos comerciales. Los archivos originales completos
de ejecución permanecen en `artifacts/passives_20261024/` y las descargas en
`project/pcb/vendor_assets_local/`, ambos fuera de Git.

|Archivo|Contenido|
|---|---|
|[calculations.json](calculations.json)|Escenarios ideales y estimados con pérdidas, envolventes, resistencias, umbrales y presupuesto bootstrap; no simulación temporal|
|[passives_definition.json](passives_definition.json)|Snapshot de las35 definiciones originales usadas para cotejar referencias y valores con la BOM; no fuente generadora nueva|
|[footprint_checks.json](footprint_checks.json)|Ocho archivos KiCad10 realmente inspeccionados: hash, pads y dimensiones; no aprobación de land ni de ensamblaje|
|[local_datasheet_hashes.json](local_datasheet_hashes.json)|Hashes de seis PDF locales consultados; obtener las copias originales por separado|
|[document_checks.json](document_checks.json)|Cobertura de35 referencias, estructura de23 tablas, hashes documentales y comprobación histórica de18 archivos protegidos|

Las rutas del clon y de la instalación de KiCad se normalizaron en las copias
para facilitar lectura en otros equipos. `${REPO_ROOT}` identifica la raíz del
clon original; `${KICAD10_FOOTPRINT_DIR}` identifica la biblioteca instalada
que se inspeccionó. No son variables que KiCad deba registrar automáticamente.
Los hashes describen el contenido original de los archivos referidos.

La lista de bloqueos sigue en [open_issues.md](../open_issues.md). Estas
comprobaciones no sustituyen ERC/DRC, simulación dinámica o pruebas físicas.
