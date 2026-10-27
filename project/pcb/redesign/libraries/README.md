# Bibliotecas CAD locales Buck SMD

Integración local en la rama **Kicad-PCB**. Hay **9 símbolos y25 footprints**
registrados en KiCad bajo el nombre **Buck_SMD**. Son candidatos de la auditoría,
no componentes aprobados eléctricamente. El diseño original permanece intacto.

## Estructura

```text
libraries/
  symbols/Buck_SMD.kicad_sym
  footprints/Buck_SMD.pretty/*.kicad_mod
  3dmodels/                  # seis archivos: cinco vinculados, uno sin pareja
  datasheets/                # siete PDF locales ya disponibles
  pending_review/            # descargas incompatibles o de formato no integrado
  integration_data.json      # procedencia, hashes, pines, pads y transformaciones
  validation_results.json    # resultados de las comprobaciones de esta integración
  validate.py                # comprobación local de solo lectura
  manifest.md
```

Los originales en Descargas y `../vendor_assets_local/` no se movieron ni
eliminaron. Las copias de revisión en `pending_review/` **no están registradas**
como bibliotecas y no deben confundirse con el conjunto utilizable.
Las variantes de densidad de un footprint conservan sus sufijos; no representan
componentes distintos ni quedan todas aprobadas para el proceso de ensamblaje.

## Comprobar personalmente en KiCad sin alterar el diseño

1. Abra `project/pcb/buck.kicad_pro` desde el administrador de proyectos KiCad.
   Si estaba abierto durante esta integración, cierre y vuelva a abrir los
   editores para recargar las tablas locales.
2. Abra el **Editor de símbolos**. En **Preferencias → Gestionar bibliotecas de
   símbolos → Bibliotecas específicas del proyecto**, confirme la entrada
   `Buck_SMD` con URI `${KIPRJMOD}/libraries/symbols/Buck_SMD.kicad_sym`.
   La entrada original `Buck` debe seguir presente.
3. En el árbol del editor filtre `Buck_SMD` o busque `SN74HCT14DR`,
   `INA180A1IDBVR`, `25SVPF100M` o `WSL2512R0500FEA`. Abra el símbolo para
   inspeccionarlo sin guardarlo ni colocar instancias en el esquemático original.
4. En el selector **Añadir símbolo** del editor de esquemas, busque
   `Buck_SMD:SN74HCT14DR`. Compruebe la previsualización y pulse **Cancelar/Esc**;
   no coloque el componente sobre el diseño actual.
5. Abra el **Editor de huellas**. En **Preferencias → Gestionar bibliotecas de
   huellas → Bibliotecas específicas del proyecto**, compruebe `Buck_SMD` con URI
   `${KIPRJMOD}/libraries/footprints/Buck_SMD.pretty`. Las entradas previas se
   conservan. Filtre `Buck_SMD` en el árbol/selector y abra, por ejemplo, `D14`,
   `DBV0005A_N`, `PCAP_SVP_E7_PAN` o `RES_2512_WSL`.
6. En **Propiedades de huella → Modelos3D**, compruebe la ruta relativa
   `${KIPRJMOD}/libraries/3dmodels/...`; use el visor3D para verificar escala,
   cara de montaje y alineación. La huella `RES_2512_WSL` no tiene modelo
   descargado; esa ausencia no impide usarla.
7. Cierre sin guardar cambios en los archivos originales. Para colocar piezas
   y experimentar, use una copia del proyecto en otro directorio. La prueba
   automática de esta sesión está en `artifacts/buck_library_integration/temporary_project/`.

El nombre comercial es el valor del símbolo, no su referencia de instancia:
al colocarlo en un futuro proyecto de rediseño KiCad asignará U/C/R según
corresponda. El fabricante, MPN, LCSC cuando existe y datasheet están en sus
propiedades. El campo `CAD_Validation` recuerda que el uso eléctrico y los lands
requieren revisión.

## Asignar huellas en una fase futura autorizada

Los nueve símbolos tienen un campo **Footprint** que apunta a una huella real
de `Buck_SMD`. No se modificó ninguna asignación de las instancias actuales.
En una copia destinada al rediseño, tras aprobar MPN, pinout y land, use
**Herramientas → Asignar huellas** o el campo **Footprint** del símbolo y elija
`Buck_SMD:<nombre>`. Revise la variante de densidad y pad1 antes de confirmar.
No reasigne todos los símbolos de una familia automáticamente.

## Añadir componentes sin perder trazabilidad

1. Mantenga la descarga original y registre fuente, MPN, fabricante y SHA-256.
   Inspeccione nombres internos y metadatos; no clasifique solo por el ZIP.
2. Compruebe formato y correspondencia comercial. Si es otro fabricante,
   encapsulado o función, déjelo en revisión. Altium/Eagle requieren una
   conversión compatible y verificación posterior de pines/pads; no basta cambiar
   la extensión. No se efectuaron conversiones de esos formatos aquí.
3. Importe un símbolo de nombre único, conservando sus pines, nombres, tipos,
   unidades y representaciones. No cambie tipos eléctricos sin una revisión
   documentada; el LM393B descargado tiene una observación específica en el manifiesto.
4. Copie la huella a la biblioteca `.pretty`; preserve geometría, capas y
   variantes. Resuelva colisiones por identidad/hash. No renombre contenido
   diferente para hacerlo pasar por equivalente. Documente cualquier ajuste.
5. Copie modelos únicamente cuando su identidad sea coherente. Vincule con
   `${KIPRJMOD}` y documente offset, rotación y escala; no estime dimensiones
   para completar una huella incompleta.
6. Actualice el manifiesto y la evidencia de validación. Revise licencias antes
   de redistribuir archivos de terceros. No se realizó commit ni push.

## Validación repetible y prevención de sobrescrituras

Desde la raíz del clon, con Python3.11 o posterior:

```powershell
python project/pcb/libraries/validate.py
```

El comprobador es de solo lectura: revisa sintaxis, referencias, rutas, nombres,
pines/pads, hashes y conservación de entradas previas. La carga nativa con
KiCad10, exportaciones de símbolos y placa temporal también se ejecutaron;
consulte [manifest.md](manifest.md). La inspección geométrica no equivale a
aprobación de ensamblaje o del circuito.

**No ejecutar `../tools/generate.py` sobre este proyecto:** puede sobrescribir
tablas y otros archivos CAD. No modificar `../tools/design.py`, `../Buck.kicad_sym`,
`../Buck.pretty/`, los esquemas, laPCB ni las asignaciones para mantener estas
bibliotecas. Tampoco usar generadores del proveedor sobre archivos ya integrados.
Las tablas `../sym-lib-table` y `../fp-lib-table` contienen ahora una entrada
adicional; deben conservarse junto con `libraries/` al copiar el proyecto.
No se requieren entradas globales ni rutas del usuario de Windows.

Las rutas relativas siguen el mecanismo documentado por [KiCad para bibliotecas
y variables del proyecto](https://docs.kicad.org/8.0/en/kicad/kicad.html).
