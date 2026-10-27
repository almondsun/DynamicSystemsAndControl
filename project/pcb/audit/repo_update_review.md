# Revisión de la consolidación documental del repositorio

Fecha:2026-10-24. Actualización preparada en **Kicad-PCB**. Este registro describe
comprobaciones de Git y documentación; no es una revisión eléctrica de KiCad.

## Rama, remoto y posibles colisiones

|Comprobación|Resultado observado|
|---|---|
|Rama activa|`Kicad-PCB`; no se ejecutó checkout ni cambio de rama|
|HEAD local|`079e7edf332101328de1c41e2e9dbc7982c5866f`|
|Rama remota consultada|`origin/Kicad-PCB` apunta al mismo commit, confirmado con `git ls-remote --heads origin`|
|main remoto|`105a1d5a4ab1f0c894cf0ba8de28cb4ce120cb32`; dos commits adicionales, `talleres` y `respuesta dinamica`|
|Archivos modificados por esos commits|Adiciones en `classroom/` y `simulations/dynamic_response_2/`; sin solapamiento con los archivos documentales preparados|
|Conflictos abiertos en el índice|Ninguno: `git ls-files --unmerged` vacío|
|Colisiones de mayúsculas/minúsculas|Ninguna entre archivos versionados y archivos seleccionados para esta actualización, comparados con `casefold` para Windows|
|Marcadores de merge en la actualización|Ninguno detectado en los documentos, matrices y scripts seleccionados|
|Cambios de otras ramas|No se incorporaron: no se ejecutó merge, rebase o pull|
|Publicación|Sin commit ni push en esta consolidación|

El remoto puede avanzar después de la consulta. Estos resultados no prometen
ausencia de conflictos futuros y no justifican un push forzado.

## Qué se incorpora y qué se conserva aparte

- Índice de auditoría, enlaces desde los README principal, del proyecto y dePCB.
- Inventario y manifiestos propios, documentos de requisitos y selección de
  pasivos, fuentes, checklist de bloqueos y guía del organizador.
- Evidencia compacta de cálculos y hashes en [evidence/](evidence/README.md),
  sin copiar datasheets o bibliotecas comerciales al repositorio.
- Herramienta del organizador y sus pruebas sintéticas existentes, con su guía;
  no se inició el watcher ni se ejecutó clasificación sobre Descargas.
- Exclusiones de Git para la biblioteca local, historial KiCad y `Buck.bak`;
  esos archivos permanecen en disco.

Los cambios locales previos de `Buck.kicad_sym`, `buck.kicad_pro` y los cinco
esquemáticos son extensos y se conservaron sin modificarlos. **Quedan fuera del
conjunto documental preparado para publicación.** No se atribuyen a esta
auditoría ni se consideran aprobados. No se alteraron PCB, BOM, `design.py`,
firmware ni asignaciones de footprints. Los18 archivos protegidos coinciden
con los hashes registrados al iniciar la auditoría de pasivos.

## Validación realizada

**Validation scope: narrow local.** La actualización cambia documentación y
exclusiones; se comprueba además la herramienta aislada que se desea conservar.
No se cambia su implementación ni el flujo eléctrico/firmware.

**Commands run:** desde la raíz del repositorio:

```powershell
git status --short --branch
git branch -vv
git remote -v
git rev-parse HEAD origin/Kicad-PCB origin/main
git ls-remote --heads origin
git ls-files --unmerged
git log --oneline --decorate -5 origin/main
git diff --name-status HEAD origin/main
git diff --check
git check-ignore project/pcb/vendor_assets_local/datasheets/C2968.pdf project/pcb/.history/buck.kicad_sch project/pcb/Buck.bak
```

Se ejecutó el comando de pruebas documentado, usando el ejecutable disponible
dePython3.12 del entorno en lugar del alias `python`:

```powershell
python -m unittest discover -s project/pcb/tools -p test_organize_vendor_assets.py -v
```

**Passed:** cinco pruebas del organizador; cobertura sintética de identidad,
ambigüedad, corrupción, ZIP, estabilidad, duplicados, colisiones de nombre,
rechazo de sobrescritura y recarga de configuración. No acceden a Descargas ni
importan el diseño. Las exclusiones se verificaron con Git y `diff --check`
no encontró errores de whitespace. La estructura de JSON, hashes de los cinco
informes de pasivos, integridad de los archivos protegidos y ausencia de
solapamientos con los commits remotos se comprobaron con un script aislado en
`artifacts/consolidate_buck_docs.py`.

**Failed / limitaciones de herramientas:** la consulta del remoto ejecutada
como subproceso dePython falló por conectividad del sandbox; la consulta Git
directa sí respondió y confirmó los commits indicados. Git avisa que la copia
de trabajo de `buck.kicad_pro` podría convertirLF aCRLF si se vuelve a escribir;
no se reescribió ni se preparó ese archivo para publicación.

**Not run:** generación/exportación deKiCad, ERC/DRC, simulación, compilación
de firmware y ensayos físicos, porque no son necesarios para esta actualización
documental y no califican por sí solos la selecciónSMD. No se reintentó la
exportación de netlist que había fallado durante la auditoría.

**Remaining unverified:** concordancia eléctrica delCAD modificado, aprobación
deMPN y huellas, existenciasJLC actuales, térmica y funcionamiento físico.
Los bloqueos técnicos siguen en [open_issues.md](open_issues.md).
