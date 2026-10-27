# Organizador local de documentos Buck (Windows)

Requiere Python 3.11 o posterior, sin paquetes externos. Desde la raíz del clon:

```powershell
python project/pcb/tools/organize_vendor_assets.py init
python project/pcb/tools/organize_vendor_assets.py watch
```

Si `python` no está en PATH, use la ruta de un ejecutable Python 3.11 o posterior
que funcione en su equipo. Sustituya la ruta de ejemplo:

```powershell
& 'C:\ruta\a\python.exe' project/pcb/tools/organize_vendor_assets.py watch
```

Detener: Ctrl+C en esa terminal. Procesar un lote y terminar: sustituir `watch`
por `once`; espera 10 segundos y compara dos observaciones. El sondeo continuo
se hace cada 3 segundos. `--settle 20 --interval 5` permite aumentar los tiempos.
Una descarga pausada puede parecer estable; los controles básicos no garantizan
que todo archivo esté completo. Para mayor certeza, descargar primero fuera de
la entrada dedicada y copiar allí cuando el navegador termine.

La ubicación real de Downloads se resuelve cada inicio leyendo la configuración
del shell del usuario, incluyendo redirecciones. Se comprueba acceso mediante
enumeración. Se crea `Downloads/Buck_component_inbox`; guarde **únicamente archivos
del proyecto Buck** allí. No se recorren los demás archivos de Downloads. Puede
copiar manualmente descargas terminadas a esta entrada; se conservan los originales.
No se vigila todo Downloads. `--inbox` acepta otra carpeta dedicada.

La salida está en `project/pcb/vendor_assets_local/`, excluida por `.gitignore`:

La [organización por tipo realizada el 2026-10-24](../audit/organization_by_type.md)
añadió también `datasheets/` y `cad/{symbols,footprints,models_3d}/` dentro de
esa biblioteca local. Es una vista copiada del inventario de esa fecha; el
organizador de este documento conserva su destino por MPN y no mantiene
automáticamente sincronizadas ambas vistas. No cambie la configuración ni
ejecute `init` sobre una biblioteca con información propia sin revisar su estado.

```text
vendor_assets_local/
  components.json
  manifest.csv
  pending_report.md
  component_library/<MPN exacto>/{datasheet,symbol,footprint,3d}/<SHA-256>/<nombre>
  pendiente_revision/<SHA-256>/<nombre>
```

Los caracteres del MPN incompatibles con Windows se codifican reversiblemente
con `%HH`; el MPN exacto se conserva siempre en configuración y manifiesto.
`auxiliary` es una categoría adicional para documentos auxiliares explícitos;
si su formato no tiene validador queda pendiente de inspección manual.

## Configurar componentes seleccionados

Editar `vendor_assets_local/components.json`. Empieza vacío deliberadamente:
la BOM actual no constituye selección de componentes SMD. Este ejemplo es
**ficticio**, no debe usarse como selección ni como código comercial:

```json
{
  "components": [
    {
      "mpn": "EJEMPLO-FICTICIO-123",
      "bom_reference": "U_EJEMPLO",
      "lcsc": "",
      "origin": "URL o proveedor comprobado manualmente",
      "aliases": ["ALIAS_EXCLUSIVO_CONFIRMADO"],
      "files": {"nombre_exacto_confirmado.pdf": "datasheet"}
    }
  ]
}
```

Registrar únicamente MPN y LCSC confirmados. `files` asocia nombres completos
comprobados con categorías; no acepta rutas. Usarlo para PDFs de nombre genérico
o documentación de familia cuya aplicación al MPN haya sido revisada. El origen
es una declaración manual del usuario, nunca una inferencia del nombre.

El identificador MPN, alias o LCSC debe coincidir exactamente (mayúsculas incluidas)
en el nombre, con límites inequívocos; `_` y espacios sirven de separador. Un
guion, punto o carácter alfanumérico contiguo evita coincidencias de prefijo.
No se adivinan sufijos de encapsulado. Dos componentes coincidentes quedan en
revisión. Los alias compartidos se detectan al clasificar y no se resuelven solos.
La configuración se recarga en cada sondeo; no hace falta reiniciar el proceso.

La categoría exige también identidad inequívoca. KiCad moderno, STEP y VRML
reciben controles estructurales básicos. Un PDF exige además `datasheet` como
palabra en su nombre o una entrada explícita en `files`. PDF: cabecera/EOF;
STEP: delimitadores; VRML: cabecera; KiCad: raíz y paréntesis/cadenas balanceados.
Son filtros de corrupción evidente, no validaciones completas de formato o CAD.
Formatos antiguos, CAD relacionados y otros documentos permanecen pendientes
cuando no hay un validador. Archivos vacíos o de estructura sospechosa se copian
a revisión y se registran. Los ZIP se comprueban por CRC con límites de tamaño
y siempre quedan en revisión; nunca se extraen automáticamente. Inspeccionarlos
y descomprimir manualmente solo los archivos pertinentes dentro de la entrada.
No se ejecutan scripts ni programas descargados. Extensiones temporales y
formatos no admitidos se ignoran y permanecen en el origen.

Las copias se verifican con SHA-256 del origen y del destino. Los duplicados en
el mismo componente/categoría reutilizan la copia existente; cada origen tiene
su registro. El mismo contenido en categorías/componentes distintos puede tener
copias independientes para preservar la clasificación. Distintos contenidos con
igual nombre se guardan en directorios hash separados. No se sobrescriben copias
alteradas. El informe registra errores de lectura/copia para su revisión y
reintento. Una copia interrumpida se conserva y puede requerir revisión manual.

El manifiesto mantiene historial al cambiar archivos o configuración y registra
referencia BOM, MPN, LCSC, origen declarado, origen físico, destino, categoría,
SHA-256, clasificación, verificación básica y redistribución pendiente. Un cambio
de configuración puede crear otro registro; no elimina copias ni revisiones
anteriores. El informe cuenta también pendientes históricos. Se registra un
archivo tras copiarlo y verificarlo. Un archivo bloqueado se reintenta en el
próximo sondeo. Solo se permite un proceso por biblioteca mediante un lock.
Si el equipo se apaga sin cierre normal, comprobar que no queda un organizador
activo antes de retirar manualmente `.organizer.lock`.

## Pruebas y registro posterior en KiCad

```powershell
python -m unittest discover -s project/pcb/tools -p test_organize_vendor_assets.py -v
```

Las pruebas usan directorios temporales y componentes ficticios, sin acceder a
Downloads, a archivos comerciales ni al diseño.

Después de revisar manualmente identidad, numeración de pines, geometría y
condiciones de uso, se pueden registrar las bibliotecas desde los administradores
de bibliotecas de símbolos y de huellas de KiCad. Seleccionar el `.kicad_sym`
revisado. Para huellas, crear una carpeta local `.pretty` y copiar dentro las
`.kicad_mod` revisadas; registrar esa carpeta como biblioteca. Mantener tablas y
rutas fuera del repositorio público hasta revisar redistribución. Los modelos
3D se vinculan manualmente desde propiedades de huella después de revisar unidades,
origen y orientación. Este organizador no registra bibliotecas, asigna huellas,
vincula modelos ni acredita compatibilidad eléctrica/mecánica, stock o categoría
Basic. No ejecuta herramientas de generación ni altera el diseño.

No usar `git add -f` con esta biblioteca. Revisar licencias de cada archivo antes
de compartirlo; `.gitignore` evita inclusiones accidentales, no es un control de
publicación ni revoca archivos que alguien haya registrado previamente.
