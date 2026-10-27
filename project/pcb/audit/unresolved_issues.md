# Discrepancias, ambigüedades y riesgos

Fecha: 2026-10-24. Todos los componentes comprables siguen pendientes de validación y selección definitiva.

- **No se alteró el diseño.** Se encontraron cambios previos en .gitignore, Buck.kicad_sym, buck.kicad_pro y los cinco esquemáticos. Se preservaron por hash. La BOM y el Excel coinciden en sus 57 referencias, valores y footprints originales; esto no significa que sean idénticos al estado actual de KiCad.
- **Biblioteca actual distinta de BOM histórica:** Buck.kicad_sym ya declara U1=IR2110STRPBF, U3=SN74HCT14DR, U4=SN74HCT00DR y U5=LM393BIDR; sus propiedades Footprint están vacías. No se atribuyen estos cambios a esta auditoría ni se consideran aprobados. Consultar valores/pines del archivo actual en el inventario.
- **Tabla de footprints:** fp-lib-table se conserva intacta. Su texto compacto tiene una sola raíz y paréntesis balanceados; no se ha probado su carga en KiCad. No se registra como defecto de sintaxis.
- **U1:** las dos descargas ZIP contienen SOLO IR2110STRPBF.STEP; ambos miembros tienen el mismo hash. PRODUCT interno IR2110S confirma familia, no variante de compra ni orientación. No contienen símbolo/footprint. DIP14 y SOIC16 exigen mapa documentado; no se declara equivalencia pin a pin.
- **U3:** ZIP contiene símbolo SN74HCT14DR, footprints D14/D14-M/D14-L y D0014A.stp. Los 14 números de pines coinciden con los 14 pads en las tres variantes. Esto es una comprobación numérica, no aprobación del pinout o de la geometría. Footprint=D14 no tiene prefijo de biblioteca y ningún footprint enlaza el STEP. Verificar orientación y elegir variante por proceso JLC.
- **C11/Altium:** shared_lib.SchLib contiene explícitamente CL21A106KAYNNNE; shared_lib.PcbLib contiene 0805_cap. Se preserva la biblioteca entera en pendiente_revision, no se extrae ni convierte un símbolo aislado. No cuenta como símbolo/footprint KiCad descargado. Su existencia reduce trabajo de búsqueda, no valida geometría ni licencia.
- **D1:** shared_lib incluye SS34-TD de TDSEMIC/C46550832; NO es SS34 de MDD/C8678. No confundir proveedores ni usar el datasheet del primero para aprobar el segundo.
- **R10:** no se verificó MPN exacto 31 kohm. La búsqueda encontró 31.6 kohm (RC0603FR-0731K6L), consignado solo como alternativa no asignada. No reemplazarlo automáticamente: altera umbral OVP y exige nueva comprobación del divisor y comparador.
- **L1/L2:** la descarga LPS3015-153MRC es otro MPN; tampoco LPS3015-152MRC corresponde al XR de la hoja. No usar sus bibliotecas/modelos como evidencia de 330 uH/3 A. Modelo inductor-provisional.wrl y footprint VERIFY del proyecto son provisionales.
- **C1/C2 y C4/C5:** no aprobar por capacitancia nominal. Rizado a 10 kHz, ESR, vida útil, temperatura y montaje pendientes. 865080343009 y otros capacitores descargados no sustituyen EMZR/BXJ por similitud de tamaño. Un catálogo Wave no demuestra aptitud para reflow.
- **U2/Q1:** PDF UMW local no es la ficha del componente original Infineon/ST. Revisar revisión y sufijo exactos, pérdidas y disipación con cobre real. Para regulador 12→5 V, 100 mA implica 0.7 W de caída ideal; no es prueba térmica ni corriente de carga aprobada.
- **Pasivos:** candidatos preliminares conservan tensión/tolerancia cuando hay evidencia; aún requieren potencia y derating, TCR, pulsos, C efectivo bajo DC, ESR y recomendaciones de los IC. Un resistor 10 ohm de 0.125 W no queda aprobado para gate por su potencia media nominal.
- **Conectores:** TB002-500-02BE es THT/Wave; 61201021621 también THT. No se fuerza conversión SMD ni se presume equivalencia mecánica con el terminal Phoenix de la BOM. J3 requiere definir cable y llave; código JLC no verificado.
- **Testpoints TP1–TP9:** pad sin pieza en BOM de ensamblaje. Existen alternativas SMD estándar en instalación KiCad; no se modificaron footprints del proyecto. Campos SELECCIÓN=sin MPN y JLCPCB=no verificado se interpretan junto con jlc_applicable=no.
- **MPN ajenos a BOM:** los nombres de carpetas de otras descargas no equivalen a identidad aprobada. Se registraron metadatos y referencias internas; las asociaciones provisionales permanecen pendientes y no alimentan la matriz Buck. SchLib/PcbLib/IntLib se preservan íntegros como auxiliary para no dividir bibliotecas propietarias; cad_role_by_format indica su papel real.
- **Formatos Altium:** SchLib/PcbLib/IntLib se identificaron mediante firma OLE y cadenas internas; sin Altium/convertidor no se validó su geometría completa. Nunca se consideraron equivalentes a bibliotecas KiCad nativas.
- **PDF sin texto:** C2236.pdf y C9009.pdf no aportan identidad mediante extracción textual; no se asignan a componentes. No se ejecutó OCR ni se dedujeron MPN por código del nombre. Otros documentos sin texto ajenos al Buck permanecen intactos en origen.
- **Cobertura de Descargas:** se enumeró la raíz real y se recorrieron carpetas de componentes/CAD reconocibles, docs, shared_lib y Buck_component_inbox. No se afirma haber inspeccionado recursivamente instaladores, juegos ni cada subdirectorio personal. Las búsquedas de Excel sí recorrieron Descargas y el clon. PDF se leyó hasta ocho páginas; no equivale a revisión técnica íntegra de todos sus contenidos. Se excluyó un libro Ogata >35 MiB por tamaño; no afecta identificación de la BOM.
- **Avisos de PDF:** pypdf informó referencias a objetos con offsets incorrectos en algunos documentos. La extracción terminó sin excepciones de lectura, pero esos avisos no se consideran validación de PDF. No se ocultó stderr. Se guardó el registro de limitaciones.
- **Herramientas:** python no estaba en PATH y el lanzador python3.14 de uv falló por acceso; se usó Python 3.12 del runtime disponible, con openpyxl SOLO para lectura y pypdf para texto. No se editó el XLSX. MATLAB MCP no está expuesto en esta sesión; no fue necesario simular ni abrir modelos para el inventario documental.
- **Organizador anterior:** components.json y manifest.csv vacíos; .organizer.lock existente conservado. No se inició/detuvo el watcher ni se cambió su configuración. La nueva organización usa manifiesto separado audit_20261024_manifest.csv para evitar conflictos con su historial.
- **Web:** algunas rutas comerciales devolvieron error o contenido antiguo. La ficha oficial TB002 dio HTTP 403; enlaces YAGEO de 31kohm no se verificaron. Se empleó NO VERIFICADO para stock y para categorías no recuperables. Ni stock de LCSC, ni texto público cacheado, ni biblioteca EasyEDA prueban disponibilidad JLC de un pedido o archivo KiCad local.

## Intervención humana requerida

- [ ] Aprobar MPN de las 48 referencias comprables; ninguna aprobación se infiere de las descargas.
- [ ] Resolver R10=31kohm y el umbral OVP antes de sustituir valores.
- [ ] Resolver térmica/rizado/saturación de Q1, D1, L1/L2, RS1, C1/C2, C4/C5 y U2.
- [ ] Revisar mapas de pines U1, U5, U6, Q1 y Q2 contra sus propias fichas; elegir footprints y orientación.
- [ ] Elegir conectores/cable y aceptar THT/Wave o investigar una alternativa apropiada.
- [ ] Revisar bibliotecas compartidas Altium y derechos de uso/conversión; confirmar identidad de CAD/PDF ambiguos.
- [ ] Comprobar stock y clase en JLC al cotizar; confirmar variante/rango exactos C20526 y C5199867.

## Fuentes técnicas consultadas

Guía del curso: classroom/Descripcion Proyecto Buck.pdf, pp.1–3, y project/pcb/docs/requirements-audit.md. Contexto registrado: VIN 12 V; VOUT nominal 6 V; L total 660 uH; C salida 20 uF; R carga 6 ohm; PWM 10 kHz. Son requisitos/documentos existentes, no resultados experimentales. No se simularon respuestas, condiciones iniciales ni solver en esta fase documental.

Se verificaron también 57 símbolos previos del proyecto y las 57 rutas de footprints originales. Hay 48 pistas de footprint estándar candidato realmente existentes (39 componentes comprables y 9 pads). Su disponibilidad física no prueba ajuste al MPN; no es obligatorio descargar otro footprint si se aprueba el estándar existente. Los contadores de faltantes se refieren a descargas identificadas, no a inexistencia absoluta de geometrías reutilizables.

Las URLs por candidato y fecha están en jlc_candidates.csv; enlaces oficiales para IC en missing_components.md. Datos comerciales de candidatos existentes siguen siendo históricos del Excel salvo consulta explícita registrada.
