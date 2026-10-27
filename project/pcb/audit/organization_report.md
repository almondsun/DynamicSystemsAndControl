# Informe de organización e inventario Buck

Fecha: 2026-10-24. Repositorio `C:\dev\7mo\control\DynamicSystemsAndControl`. Rama inicial `Kicad-PCB`; sin checkout, commit, push ni modificación del diseño.

Excel fuente: `C:\Users\justa\Downloads\Auditoria_preliminar_Buck_JLCPCB_2026-10-22.xlsx`; SHA-256 `e4ff7535b1f189998981dc81df44d140134d497f837a3760c102a702df797ffa`. Hoja `BOM auditada`, filas 2–58. BOM: `project/pcb/bom.csv`; SHA-256 `ee5e6b105177c0f80094d2edec0e283c2cb63a9127d42c7936d9741181ae54cd`. No se reemplazó ninguna fuente ni se escribió el XLSX.

## Resultado

|Métrica|Cantidad|
|---|---:|
|Referencias reconciliadas|57|
|Componentes comprables|48|
|Testpoints sin pieza|9|
|Referencias con datasheet + símbolo KiCad + footprint KiCad + 3D descargados|1|
|Referencias comprables sin MPN en Excel histórico|31|
|Referencias sin candidato exacto después de investigación|1|
|Referencias pendientes de selección definitiva|48|
|Referencias sin datasheet descargado identificado|42|
|Referencias sin símbolo KiCad descargado identificado|47|
|Referencias sin footprint KiCad descargado identificado|47|
|Referencias sin 3D descargado identificado|44|
|MPN nuevos candidatos (preliminares)|13|
|Referencias cubiertas por candidatos nuevos|30|
|Alternativas de valor NO asignadas|1|
|Relaciones de procedencia/archivo copiadas o reutilizadas|84|
|Archivos únicos organizados por destino|81|
|Copias reutilizadas por hash (incluye copias creadas en intento previo de esta sesión)|14|

Los faltantes se cuentan por referencia comprable (48), no por MPN único, y sobre descargas identificadas para el candidato. TP1–TP9 están excluidos. Juegos completos indica presencia de cuatro tipos, no aprobación técnica: solo U3 tiene juego completo descargado. Símbolos previos del proyecto, footprints estándar instalados y modelos originales THT se conservan y se enumeran separadamente para reutilización.

## Operaciones y trazabilidad

- Acceso real comprobado a `C:\Users\justa\Downloads` mediante enumeración y lectura. Se inspeccionaron 242 archivos de formatos PDF/ZIP/CAD en el alcance documentado; no se trasladaron descargas originales.
- Se reutilizó `vendor_assets_local/component_library/<MPN>/{datasheet,symbol,footprint,3d}`. MPN con caracteres Windows inválidos usa %HH reversible (por ejemplo `*`→`%2A`). Se agregó auxiliary para ZIP y CAD propietario. Archivos ambiguos van a pendiente_revision/<SHA-256>/.
- Copias creadas con apertura exclusiva, hash SHA-256 de origen/destino; contenido idéntico en igual MPN/categoría reutiliza destino. Nunca se sobrescribe un archivo diferente.
- ZIP inspeccionados en `artifacts/buck_inventory_20261024/zip_inspection_p92zkuq6`: límites de miembros/tamaño/expansión, rechazo de rutas absolutas, traversal y symlinks; lectura comprueba CRC. No se ejecutaron programas descargados. Carpetas temporales conservadas, incluidos intentos interrumpidos. El primer intento tropezó con el límite de longitud de rutas de Windows; se acortaron únicamente directorios temporales y la ejecución final terminó correctamente.
- Procedencia ZIP y hash del contenedor se conservan en asset_manifest.csv; nombre original no se altera.
- Configuración y manifiesto del watcher previo permanecen intactos; el nuevo manifiesto local es vendor_assets_local/audit_20261024_manifest.csv.
- Regla ya existente .gitignore excluye toda vendor_assets_local; no se alteró .gitignore. Licencias/redistribución pendientes antes de incorporar assets a Git.

Las 57 referencias tienen símbolo previo y footprint original localizados. Además se verificaron 39 footprints genéricos candidatos para componentes comprables y 9 pads SMD estándar. Estos archivos están en existing_project_assets.csv con SHA-256. Los 47 faltantes de símbolo/footprint descargado NO implican que deban diseñarse 47 bibliotecas nuevas: primero revisar/reutilizar los archivos existentes.

## Investigación web

Se registraron candidatos nuevos para conectores, MLCC y resistencias sin MPN en el Excel. Preferencias Basic comprobadas: CC0603KRX7R9BB104, CL21B105KBFNNNE, CL21A106KAYNNNE, 0603WAF1002T5E, 0603WAF1001T5E y 0603WAF4701T5E. Extended confirmado: TB002-500-02BE, CL21B334KBFNNNE, 0603CG102J500NT. R1/R8/R14 y J3 conservan clasificación NO VERIFICADO. Los motivos para Extended y las verificaciones eléctricas aparecen en cada fila de jlc_candidates.csv. R10 sigue sin candidato exacto; 31.6kohm no se asignó.

Ejemplos de fuentes primarias: [JLC 100nF Basic](https://jlcpcb.com/partdetail/YAGEO-CC0603KRX7R9BB104/C14663), [ficha YAGEO](https://yageogroup.com/download/specsheet/CC0603KRX7R9BB104), [Samsung 1uF/50V](https://product.samsungsem.com/mlcc/CL21B105KBFNNN.do), [Royal Ohm](https://www.royalohm.com/assets/pdf/products/smd/1.pdf), [conector Würth](https://www.we-online.com/components/products/datasheet/61201021621.pdf). Fecha de consulta por fila: 2026-10-24. URL identificada en web no se contó como descarga en disco.

## Entregables
- component_inventory.csv: una fila por designator; estados independientes, localizadores Excel/CSV, rutas de archivos, símbolos y geometría existente.
- missing_components.md: checklist de 48 referencias y 9 testpoints.
- jlc_candidates.csv: MPN, fabricante, código, clase, consulta, características, URLs y riesgos de candidatos nuevos.
- unresolved_issues.md: discrepancias, riesgos e intervención humana.
- asset_manifest.csv: vínculo origen/ZIP/miembro/destino/SHA-256 y evidencia de identidad.
- existing_project_assets.csv: bibliotecas del proyecto y geometrías estándar consultadas sin copiarlas ni reemplazarlas.
- verification_results.json: controles ejecutados y preservación de archivos.

## Estado Git previo
```text
 M .gitignore
 M project/pcb/Buck.kicad_sym
 M project/pcb/buck.kicad_pro
 M project/pcb/buck.kicad_sch
 M project/pcb/buck_1.kicad_sch
 M project/pcb/buck_2.kicad_sch
 M project/pcb/buck_3.kicad_sch
 M project/pcb/buck_4.kicad_sch
?? project/pcb/.history/
?? project/pcb/Buck.bak
?? project/pcb/docs/vendor-assets-organizer.md
?? project/pcb/tools/organize_vendor_assets.py
?? project/pcb/tools/test_organize_vendor_assets.py
```

## Archivos organizados
|MPN o revisión|Tipo|Archivo destino|Evidencia/procedencia|
|---|---|---|---|
|IRFZ44NS|datasheet|project/pcb/vendor_assets_local/component_library/IRFZ44NS/datasheet/ebcbb210b448e54f27f8ae13686619e83c1ca18d60dfc7d3fe8cbfd7609456b5/C5199867.pdf|C:\Users\justa\Downloads\C5199867.pdf|
|SS34|datasheet|project/pcb/vendor_assets_local/component_library/SS34/datasheet/fb4970875779696914d235bcf954240569302fb325399838f2861d474cbf9760/C8678.pdf|C:\Users\justa\Downloads\C8678.pdf|
|IR2110STRPBF|datasheet|project/pcb/vendor_assets_local/component_library/IR2110STRPBF/datasheet/3de3f1ff4244dc9ffb5542cd5ad52bd970f4c0fc1cc45e67aa8962b52166786c/C2968.pdf|C:\Users\justa\Downloads\C2968.pdf|
|78M05|datasheet|project/pcb/vendor_assets_local/component_library/78M05/datasheet/162df1416fa16eadefc4d9fb2f46121df5c48569a40255a0ddfb9a01e14c166f/C347278.pdf|C:\Users\justa\Downloads\C347278.pdf|
|SN74HCT14DR|datasheet|project/pcb/vendor_assets_local/component_library/SN74HCT14DR/datasheet/925eabf18762f43fff8c774e33c0b9d6e22293e95833adebfaab86728eb2cb0e/sn74hct14.pdf|C:\Users\justa\Downloads\sn74hct14.pdf|
|MMBT3904|datasheet|project/pcb/vendor_assets_local/component_library/MMBT3904/datasheet/6c2034cb0bd0d85be51c9c4f82aad838a688aa70c20de1a71681be8ec02b659b/C20526.pdf|C:\Users\justa\Downloads\C20526.pdf|
|IR2110STRPBF|auxiliary|project/pcb/vendor_assets_local/component_library/IR2110STRPBF/auxiliary/e50329e32e4c2d1ab5a75433b42e5e1c60892591881915e9b301e905f48f48ef/IR2110STRPBF.zip|C:\Users\justa\Downloads\IR2110STRPBF.zip|
|IR2110STRPBF|3d|project/pcb/vendor_assets_local/component_library/IR2110STRPBF/3d/7e327f3c93074ecca454949da7f087027f6122871c91d868631358b25752f9f3/IR2110STRPBF.STEP|C:\Users\justa\Downloads\IR2110STRPBF.zip :: IR2110STRPBF.STEP|
|IR2110STRPBF|auxiliary|project/pcb/vendor_assets_local/component_library/IR2110STRPBF/auxiliary/663f6048f1c33474fefaab52236021fa3d0a8968f446199fdb41d33e5c6f9927/IR2110STRPBF (1).zip|C:\Users\justa\Downloads\IR2110STRPBF (1).zip|
|IR2110STRPBF|3d|project/pcb/vendor_assets_local/component_library/IR2110STRPBF/3d/7e327f3c93074ecca454949da7f087027f6122871c91d868631358b25752f9f3/IR2110STRPBF.STEP|C:\Users\justa\Downloads\IR2110STRPBF (1).zip :: IR2110STRPBF.STEP|
|SN74HCT14DR|auxiliary|project/pcb/vendor_assets_local/component_library/SN74HCT14DR/auxiliary/da7eb641de5e939280d2f965c132b26595d266b5e91197230cac1648cdbef484/SN74HCT14DR.zip|C:\Users\justa\Downloads\SN74HCT14DR.zip|
|SN74HCT14DR|3d|project/pcb/vendor_assets_local/component_library/SN74HCT14DR/3d/bf9112576a5c64b5b450fc4ca996247ce4f2e4a825a44dafc2453e0dfe2be627/D0014A.stp|C:\Users\justa\Downloads\SN74HCT14DR.zip :: D0014A.stp|
|SN74HCT14DR|symbol|project/pcb/vendor_assets_local/component_library/SN74HCT14DR/symbol/d899201bfed6f29ab2a57f574279e259425659f25f477928baff0f92cffca202/2026-10-23_16-23-33.kicad_sym|C:\Users\justa\Downloads\SN74HCT14DR.zip :: KiCADv6/2026-10-23_16-23-33.kicad_sym|
|SN74HCT14DR|footprint|project/pcb/vendor_assets_local/component_library/SN74HCT14DR/footprint/aa00bba6e51820c722d005b58b6b71cf2d0c03eaaa65558e8ccff5973adce216/D14-L.kicad_mod|C:\Users\justa\Downloads\SN74HCT14DR.zip :: KiCADv6/footprints.pretty/D14-L.kicad_mod|
|SN74HCT14DR|footprint|project/pcb/vendor_assets_local/component_library/SN74HCT14DR/footprint/29ab4ddb098891a9248f7c421f8b2f3e1d27fdb0a3e4814d2bb4575b81607ef7/D14-M.kicad_mod|C:\Users\justa\Downloads\SN74HCT14DR.zip :: KiCADv6/footprints.pretty/D14-M.kicad_mod|
|SN74HCT14DR|footprint|project/pcb/vendor_assets_local/component_library/SN74HCT14DR/footprint/36e8106a581c150117874a1373ff7d6e3adc3acffd55a01ce064db1b6fee9d7b/D14.kicad_mod|C:\Users\justa\Downloads\SN74HCT14DR.zip :: KiCADv6/footprints.pretty/D14.kicad_mod|
|TB002-500-02BE|auxiliary|project/pcb/vendor_assets_local/component_library/TB002-500-02BE/auxiliary/513b4ed719fdc5ba893195aff0836a2e77d2d210e7be5caca8fcdea9b9e50902/TB002_500_02BE.zip|C:\Users\justa\Downloads\TB002_500_02BE.zip|
|TB002-500-02BE|auxiliary|project/pcb/vendor_assets_local/component_library/TB002-500-02BE/auxiliary/9d4957b8127e2fc43cf222d60000e4dd07e67ced11b9c3b82016a181790abd82/TB002-500-02BE.IntLib|C:\Users\justa\Downloads\TB002_500_02BE.zip :: TB002-500-02BE.IntLib|
|TB002-500-02BE|auxiliary|project/pcb/vendor_assets_local/component_library/TB002-500-02BE/auxiliary/f39ef20eb77abdfd45860d382242e99771e5a117b5541944c97ace4245bc203f/TB002_500_02BE (1).zip|C:\Users\justa\Downloads\TB002_500_02BE (1).zip|
|TB002-500-02BE|3d|project/pcb/vendor_assets_local/component_library/TB002-500-02BE/3d/fa62702c8916ee04ce4087cb57de963c527c6e9044eb377342c3b46d104673bc/TB002-500-02BE.STEP|C:\Users\justa\Downloads\TB002_500_02BE (1).zip :: TB002-500-02BE.STEP|
|50PK4700MEFC18X40|auxiliary|project/pcb/vendor_assets_local/component_library/50PK4700MEFC18X40/auxiliary/2c37edeb0dc41aa8eaf2a41b1d389b61f9850f5b50659030d6ca789fe539a646/50PK4700MEFC18X40.zip|C:\Users\justa\Downloads\50PK4700MEFC18X40.zip|
|50PK4700MEFC18X40|auxiliary|project/pcb/vendor_assets_local/component_library/50PK4700MEFC18X40/auxiliary/d38cd2384a71d2a750ce8c57da6351dbf14d8fbf9181bb117d04df343757633c/50PK4700MEFC18X40.PcbLib|C:\Users\justa\Downloads\50PK4700MEFC18X40.zip :: Altium/50PK4700MEFC18X40/50PK4700MEFC18X40.PcbLib|
|50PK4700MEFC18X40|auxiliary|project/pcb/vendor_assets_local/component_library/50PK4700MEFC18X40/auxiliary/28ba9abc1d18fd6c300d94479737e8684b6f1cb6c2e11970da0722f182d9f7e6/50PK4700MEFC18X40.SchLib|C:\Users\justa\Downloads\50PK4700MEFC18X40.zip :: Altium/50PK4700MEFC18X40/50PK4700MEFC18X40.SchLib|
|50PK4700MEFC18X40|3d|project/pcb/vendor_assets_local/component_library/50PK4700MEFC18X40/3d/550f258cddf4dff6c2bc8b54b2ae4abdde4adec9bb0358c1f9a70e9ae72e069e/CAP_PKPZ_18X40_RUB.step|C:\Users\justa\Downloads\50PK4700MEFC18X40.zip :: Altium/50PK4700MEFC18X40/CAP_PKPZ_18X40_RUB.step|
|50YXJ47M6-3X11|auxiliary|project/pcb/vendor_assets_local/component_library/50YXJ47M6-3X11/auxiliary/93b9b10089a5ac79e3b89575d7bd65c19ca6e87998e1e44d9cffaeb40725504a/50YXJ47M6_3X11.zip|C:\Users\justa\Downloads\50YXJ47M6_3X11.zip|
|50YXJ47M6-3X11|auxiliary|project/pcb/vendor_assets_local/component_library/50YXJ47M6-3X11/auxiliary/eb8a790e0bbbb64ac5dbf6fcdb173a96ae7ae2b9b9845ed0cacfb9eb0d4825aa/50YXJ47M6P3X11.PcbLib|C:\Users\justa\Downloads\50YXJ47M6_3X11.zip :: Altium/50YXJ47M6-3X11/50YXJ47M6P3X11.PcbLib|
|50YXJ47M6-3X11|auxiliary|project/pcb/vendor_assets_local/component_library/50YXJ47M6-3X11/auxiliary/c186d548f48762952312df04e77e88e4c509496248556d2b65f9ddb46a580a61/50YXJ47M6P3X11.SchLib|C:\Users\justa\Downloads\50YXJ47M6_3X11.zip :: Altium/50YXJ47M6-3X11/50YXJ47M6P3X11.SchLib|
|50YXJ47M6-3X11|3d|project/pcb/vendor_assets_local/component_library/50YXJ47M6-3X11/3d/02fdd37d53c1686b6d768f4178745558741d1bcefffbae73143248d64d078d9b/CAP_YX_6P3X11_RUB.step|C:\Users\justa\Downloads\50YXJ47M6_3X11.zip :: Altium/50YXJ47M6-3X11/CAP_YX_6P3X11_RUB.step|
|865080343009|auxiliary|project/pcb/vendor_assets_local/component_library/865080343009/auxiliary/726d9dd09fdb56d2da29cd60173522ead776dc92e5727a4cc4e4dd11d4f7f569/865080343009.zip|C:\Users\justa\Downloads\865080343009.zip|
|865080343009|auxiliary|project/pcb/vendor_assets_local/component_library/865080343009/auxiliary/e6e8995b002330557c54f9d5389dbe0f0ebd73d62e6f9afd77cc08ded3493a79/WCAP-ASLI_6.3X5.5.IntLib|C:\Users\justa\Downloads\865080343009.zip :: WCAP-ASLI_6.3X5.5.IntLib|
|865080343009|auxiliary|project/pcb/vendor_assets_local/component_library/865080343009/auxiliary/29489b891de44fd553bad8e18a2defde00063b23229755a5e7344ad5397ef3d0/865080343009 (1).zip|C:\Users\justa\Downloads\865080343009 (1).zip|
|865080343009|3d|project/pcb/vendor_assets_local/component_library/865080343009/3d/ee8afdf89cd43acf69067f0790bf4b4c3871669b66938e36a665ddfa04b00daf/STP_WCAP-ASLI_6.3x5.5x2+%28rev1%29.stp|C:\Users\justa\Downloads\865080343009 (1).zip :: STP_WCAP-ASLI_6.3x5.5x2+%28rev1%29.stp|
|C0402C473K3RECTU|auxiliary|project/pcb/vendor_assets_local/component_library/C0402C473K3RECTU/auxiliary/53aac7851e59446a9884105412a460adbc5e89701d5d4b34a111ef9b9c3fc5fc/C0402C473K3RECTU.zip|C:\Users\justa\Downloads\C0402C473K3RECTU.zip|
|C0402C473K3RECTU|3d|project/pcb/vendor_assets_local/component_library/C0402C473K3RECTU/3d/b5aa94e32e4bf59005a74ef2209b2b097b1ed0d5540f2085fdc3c6d09e8e757c/CCS_CCSTD_0402_L1.05W0.55T0.55B0.3.step|C:\Users\justa\Downloads\C0402C473K3RECTU.zip :: CCS_CCSTD_0402_L1.05W0.55T0.55B0.3.step|
|C0402C473K3RECTU|auxiliary|project/pcb/vendor_assets_local/component_library/C0402C473K3RECTU/auxiliary/5ca1d5db804bb6de91ea8f9244ee4b4dd826188efb52f6e926aed2b7c02466af/C0402C473K3RECTU.PcbLib|C:\Users\justa\Downloads\C0402C473K3RECTU.zip :: Altium/C0402C473K3RECTU.PcbLib|
|C0402C473K3RECTU|auxiliary|project/pcb/vendor_assets_local/component_library/C0402C473K3RECTU/auxiliary/fc2bf81acaa4d185d0ad6630e1ce285a4f9ebc68612bbd7b571aa99315030502/C0402C473K3RECTU.SchLib|C:\Users\justa\Downloads\C0402C473K3RECTU.zip :: Altium/C0402C473K3RECTU.SchLib|
|C0402C473K3RECTU|3d|project/pcb/vendor_assets_local/component_library/C0402C473K3RECTU/3d/2a0ccdbab7375362d519562b8427e201558859054d9cb11a4b803cd090c8ed50/CAPC10555_55N_KEM.step|C:\Users\justa\Downloads\C0402C473K3RECTU.zip :: Altium/CAPC10555_55N_KEM.step|
|ECQ-E2104KB|auxiliary|project/pcb/vendor_assets_local/component_library/ECQ-E2104KB/auxiliary/a1f6ce418ac6c0c8e5652624572210f75d3771f6d6582276b53aa54c4b74f8ee/ECQ_E2104KB.zip|C:\Users\justa\Downloads\ECQ_E2104KB.zip|
|ECQ-E2104KB|3d|project/pcb/vendor_assets_local/component_library/ECQ-E2104KB/3d/9a834ee91ae22857431d16f3a9d7ceeb2748cdf195b93fd1a298e10057367ea1/EC-2_PAN.step|C:\Users\justa\Downloads\ECQ_E2104KB.zip :: Altium/EC-2_PAN.step|
|ECQ-E2104KB|auxiliary|project/pcb/vendor_assets_local/component_library/ECQ-E2104KB/auxiliary/1e02dd1bfbb1f242780828e2d2a0934fda44b9d38157dc71f7bc2a3d60ccf814/ECQ-E2104KB.PcbLib|C:\Users\justa\Downloads\ECQ_E2104KB.zip :: Altium/ECQ-E2104KB.PcbLib|
|ECQ-E2104KB|auxiliary|project/pcb/vendor_assets_local/component_library/ECQ-E2104KB/auxiliary/39f5a17878cb5af39b02d5416ad0df89844f08db39481de7bcca7fae4efb8e7d/ECQ-E2104KB.SchLib|C:\Users\justa\Downloads\ECQ_E2104KB.zip :: Altium/ECQ-E2104KB.SchLib|
|LPS3015-152MRC|auxiliary|project/pcb/vendor_assets_local/component_library/LPS3015-152MRC/auxiliary/5b9a09b9433ef3ddd0c8c1870e6706dde1e6e835eb319ed542dd3ed612d1383a/LIB_LPS3015-152MRC.zip|C:\Users\justa\Downloads\LIB_LPS3015-152MRC.zip|
|LPS3015-152MRC|3d|project/pcb/vendor_assets_local/component_library/LPS3015-152MRC/3d/1e4448e6d381b2a96e5fd476e6aa01dccd7a44ecd4c235ee6e9111a5e520f050/LPS3015-152MRC.stp|C:\Users\justa\Downloads\LIB_LPS3015-152MRC.zip :: LPS3015-152MRC/3D/LPS3015-152MRC.stp|
|LPS3015-153MRC|auxiliary|project/pcb/vendor_assets_local/component_library/LPS3015-153MRC/auxiliary/22c2a1c565ed5753922818ad19eeed5b1518e396eaa1cbb991681e348209f4f0/LPS3015-153MRC.zip|C:\Users\justa\Downloads\LPS3015-153MRC.zip|
|LPS3015-153MRC|symbol|project/pcb/vendor_assets_local/component_library/LPS3015-153MRC/symbol/a968989a8982e367298265b6d5fe29b9742bc06a1bd772616eedfdc03db47783/LPS3015-153MRC.kicad_sym|C:\Users\justa\Downloads\LPS3015-153MRC.zip :: LPS3015-153MRC.kicad_sym|
|LPS3015-153MRC|3d|project/pcb/vendor_assets_local/component_library/LPS3015-153MRC/3d/1e4448e6d381b2a96e5fd476e6aa01dccd7a44ecd4c235ee6e9111a5e520f050/LPS3015-153MRC.step|C:\Users\justa\Downloads\LPS3015-153MRC.zip :: LPS3015-153MRC.step|
|LPS3015-153MRC|footprint|project/pcb/vendor_assets_local/component_library/LPS3015-153MRC/footprint/e2a87626a07d2726256b61a1a785f4d27a5e34a5e9f07ca5d1b84e400bb96ff6/IND_LPS3015-153MRC.kicad_mod|C:\Users\justa\Downloads\LPS3015-153MRC.zip :: IND_LPS3015-153MRC.kicad_mod|
|MCP73871-2CCI/ML|auxiliary|project/pcb/vendor_assets_local/component_library/MCP73871-2CCI%2FML/auxiliary/8adf2122debee1cd8e1654955e38fbb00a9a36536733a8763b86123dcc440c41/MCP73871-2CCI_ML.zip|C:\Users\justa\Downloads\MCP73871-2CCI_ML.zip|
|MCP73871-2CCI/ML|symbol|project/pcb/vendor_assets_local/component_library/MCP73871-2CCI%2FML/symbol/2deddd1f0854551df85bebe8e4045ee6ada1b927d2b45dd59a99ad2b87f22dd7/MCP73871-2CCI_ML.kicad_sym|C:\Users\justa\Downloads\MCP73871-2CCI_ML.zip :: MCP73871-2CCI_ML.kicad_sym|
|MCP73871-2CCI/ML|footprint|project/pcb/vendor_assets_local/component_library/MCP73871-2CCI%2FML/footprint/7440f480b06d07fd31a01bc9ddf79067e47011fe01282fcc5cfeb694b58fa055/QFN50P400X400X100-21N.kicad_mod|C:\Users\justa\Downloads\MCP73871-2CCI_ML.zip :: QFN50P400X400X100-21N.kicad_mod|
|RN73H1JTTD8762B25|auxiliary|project/pcb/vendor_assets_local/component_library/RN73H1JTTD8762B25/auxiliary/2b9292d2a8f9be4397edecbf112bba336d8e4a06140b5460c6feb99f0636d79f/RN73H1JTTD8762B25 (1).zip|C:\Users\justa\Downloads\RN73H1JTTD8762B25 (1).zip|
|RN73H1JTTD8762B25|3d|project/pcb/vendor_assets_local/component_library/RN73H1JTTD8762B25/3d/7d544bf881b374142e5f7bb976fd7435469a1d191fef4bbffdb01402db1d139f/RN73H1JTTD8762B25.STEP|C:\Users\justa\Downloads\RN73H1JTTD8762B25 (1).zip :: RN73H1JTTD8762B25.STEP|
|NRF52840-QFAA-R7|auxiliary|project/pcb/vendor_assets_local/component_library/NRF52840-QFAA-R7/auxiliary/7fc1cb989b85e1cb6ad1165fe2f8c20e022b96bbab37943e4f7e7b525dfa17ed/ul_NRF52840-QFAA-R7.zip|C:\Users\justa\Downloads\ul_NRF52840-QFAA-R7.zip|
|NRF52840-QFAA-R7|symbol|project/pcb/vendor_assets_local/component_library/NRF52840-QFAA-R7/symbol/2ad4e9c43b2df7201f0f6057e76e9986876356ba2a5772924484a0876a2234a0/2026-07-20_03-01-55.kicad_sym|C:\Users\justa\Downloads\ul_NRF52840-QFAA-R7.zip :: KiCADv6/2026-07-20_03-01-55.kicad_sym|
|NRF52840-QFAA-R7|footprint|project/pcb/vendor_assets_local/component_library/NRF52840-QFAA-R7/footprint/2bcfbb0c73fa3c67efa487ebcd68b6ab3c308b560ffaacdfee91a01c6bbffde9/QFN48_NRF52840-QFAA-R7_NOR-L.kicad_mod|C:\Users\justa\Downloads\ul_NRF52840-QFAA-R7.zip :: KiCADv6/footprints.pretty/QFN48_NRF52840-QFAA-R7_NOR-L.kicad_mod|
|NRF52840-QFAA-R7|footprint|project/pcb/vendor_assets_local/component_library/NRF52840-QFAA-R7/footprint/c7ab0dbf822f61df230566c61e87ae23eca778c34d2a976b75d06b364e1c12a6/QFN48_NRF52840-QFAA-R7_NOR-M.kicad_mod|C:\Users\justa\Downloads\ul_NRF52840-QFAA-R7.zip :: KiCADv6/footprints.pretty/QFN48_NRF52840-QFAA-R7_NOR-M.kicad_mod|
|NRF52840-QFAA-R7|footprint|project/pcb/vendor_assets_local/component_library/NRF52840-QFAA-R7/footprint/055bf5c12e296ee8c2ac0df0f1895712be077f5cc850ef22786b3336f246f0ae/QFN48_NRF52840-QFAA-R7_NOR.kicad_mod|C:\Users\justa\Downloads\ul_NRF52840-QFAA-R7.zip :: KiCADv6/footprints.pretty/QFN48_NRF52840-QFAA-R7_NOR.kicad_mod|
|pendiente revisión|auxiliary|project/pcb/vendor_assets_local/pendiente_revision/275a4fa7f258104179c5bbdc287d77bf11e797a63af9cd2e619bcab084384e0f/KBL406G.IntLib|C:\Users\justa\Downloads\KBL406G.IntLib|
|pendiente revisión|3d|project/pcb/vendor_assets_local/pendiente_revision/1e4448e6d381b2a96e5fd476e6aa01dccd7a44ecd4c235ee6e9111a5e520f050/LPS3015-152MRC.stp|C:\Users\justa\Downloads\LPS3015-152MRC.stp|
|pendiente revisión|3d|project/pcb/vendor_assets_local/pendiente_revision/63924dd75e4e6b6dde6b5f8b42b4b1d3e8c8aca816f466f4183768221205b64a/LPS3015.STEP|C:\Users\justa\Downloads\LPS3015.STEP|
|pendiente revisión|auxiliary|project/pcb/vendor_assets_local/pendiente_revision/3c1ba2a994d26a92a9dd8d8ed9851deac0b1fe0d7be27d71fec60b9fd2f8ee19/Miscellaneous Connectors.IntLib|C:\Users\justa\Downloads\Miscellaneous Connectors.IntLib|
|pendiente revisión|auxiliary|project/pcb/vendor_assets_local/pendiente_revision/91594ede8aadf6449fff5b44b7443deafeb73cfaf0bc1eb1ff434d8ac1fb6159/shared_lib.IntLib|C:\Users\justa\Downloads\shared_lib.IntLib|
|pendiente revisión|auxiliary|project/pcb/vendor_assets_local/pendiente_revision/d38cd2384a71d2a750ce8c57da6351dbf14d8fbf9181bb117d04df343757633c/50PK4700MEFC18X40.PcbLib|C:\Users\justa\Downloads\50PK4700MEFC18X40\Altium\50PK4700MEFC18X40\50PK4700MEFC18X40.PcbLib|
|pendiente revisión|auxiliary|project/pcb/vendor_assets_local/pendiente_revision/28ba9abc1d18fd6c300d94479737e8684b6f1cb6c2e11970da0722f182d9f7e6/50PK4700MEFC18X40.SchLib|C:\Users\justa\Downloads\50PK4700MEFC18X40\Altium\50PK4700MEFC18X40\50PK4700MEFC18X40.SchLib|
|pendiente revisión|3d|project/pcb/vendor_assets_local/pendiente_revision/550f258cddf4dff6c2bc8b54b2ae4abdde4adec9bb0358c1f9a70e9ae72e069e/CAP_PKPZ_18X40_RUB.step|C:\Users\justa\Downloads\50PK4700MEFC18X40\Altium\50PK4700MEFC18X40\CAP_PKPZ_18X40_RUB.step|
|pendiente revisión|auxiliary|project/pcb/vendor_assets_local/pendiente_revision/eb8a790e0bbbb64ac5dbf6fcdb173a96ae7ae2b9b9845ed0cacfb9eb0d4825aa/50YXJ47M6P3X11.PcbLib|C:\Users\justa\Downloads\50YXJ47M6_3X11\Altium\50YXJ47M6-3X11\50YXJ47M6P3X11.PcbLib|
|pendiente revisión|auxiliary|project/pcb/vendor_assets_local/pendiente_revision/c186d548f48762952312df04e77e88e4c509496248556d2b65f9ddb46a580a61/50YXJ47M6P3X11.SchLib|C:\Users\justa\Downloads\50YXJ47M6_3X11\Altium\50YXJ47M6-3X11\50YXJ47M6P3X11.SchLib|
|pendiente revisión|3d|project/pcb/vendor_assets_local/pendiente_revision/02fdd37d53c1686b6d768f4178745558741d1bcefffbae73143248d64d078d9b/CAP_YX_6P3X11_RUB.step|C:\Users\justa\Downloads\50YXJ47M6_3X11\Altium\50YXJ47M6-3X11\CAP_YX_6P3X11_RUB.step|
|pendiente revisión|3d|project/pcb/vendor_assets_local/pendiente_revision/05dbb59f488662db2ab66ed02ebfc7d4292c3ee651be7722db1ff0d95e98ab52/C5750X7R1V476M230KC.step|C:\Users\justa\Downloads\C5750X7R1V476M230KC (1)\C5750X7R1V476M230KC.step|
|pendiente revisión|3d|project/pcb/vendor_assets_local/pendiente_revision/9a834ee91ae22857431d16f3a9d7ceeb2748cdf195b93fd1a298e10057367ea1/EC-2_PAN.step|C:\Users\justa\Downloads\ECQ_E2104KB\Altium\EC-2_PAN.step|
|pendiente revisión|auxiliary|project/pcb/vendor_assets_local/pendiente_revision/1e02dd1bfbb1f242780828e2d2a0934fda44b9d38157dc71f7bc2a3d60ccf814/ECQ-E2104KB.PcbLib|C:\Users\justa\Downloads\ECQ_E2104KB\Altium\ECQ-E2104KB.PcbLib|
|pendiente revisión|auxiliary|project/pcb/vendor_assets_local/pendiente_revision/39f5a17878cb5af39b02d5416ad0df89844f08db39481de7bcca7fae4efb8e7d/ECQ-E2104KB.SchLib|C:\Users\justa\Downloads\ECQ_E2104KB\Altium\ECQ-E2104KB.SchLib|
|pendiente revisión|auxiliary|project/pcb/vendor_assets_local/pendiente_revision/c7773ac45e87a7d957122a8c804020a226eac2ec0335d7bc87b9efb885161ba7/KBL406G.SchLib|C:\Users\justa\Downloads\KBL406G\KBL406G.SchLib|
|pendiente revisión|auxiliary|project/pcb/vendor_assets_local/pendiente_revision/8418e3ad63700681ea2a1486c96345742056a860945ab38b86dd0fccfa3a3df5/SIP600W130P510L1900H1630Q4.PcbLib|C:\Users\justa\Downloads\KBL406G\SIP600W130P510L1900H1630Q4.PcbLib|
|LPS3015-153MRC|footprint|project/pcb/vendor_assets_local/component_library/LPS3015-153MRC/footprint/e2a87626a07d2726256b61a1a785f4d27a5e34a5e9f07ca5d1b84e400bb96ff6/IND_LPS3015-153MRC.kicad_mod|C:\Users\justa\Downloads\LPS3015-153MRC\IND_LPS3015-153MRC.kicad_mod|
|LPS3015-153MRC|symbol|project/pcb/vendor_assets_local/component_library/LPS3015-153MRC/symbol/a968989a8982e367298265b6d5fe29b9742bc06a1bd772616eedfdc03db47783/LPS3015-153MRC.kicad_sym|C:\Users\justa\Downloads\LPS3015-153MRC\LPS3015-153MRC.kicad_sym|
|pendiente revisión|3d|project/pcb/vendor_assets_local/pendiente_revision/1e4448e6d381b2a96e5fd476e6aa01dccd7a44ecd4c235ee6e9111a5e520f050/LPS3015-153MRC.step|C:\Users\justa\Downloads\LPS3015-153MRC\LPS3015-153MRC.step|
|pendiente revisión|auxiliary|project/pcb/vendor_assets_local/pendiente_revision/ba8ca519bcff8694db7ed4c112c89ba0fe41a5a92836ba9edc0d0496831328af/Miscellaneous Connectors.PcbLib|C:\Users\justa\Downloads\Miscellaneous Connectors\Miscellaneous Connectors.PcbLib|
|pendiente revisión|auxiliary|project/pcb/vendor_assets_local/pendiente_revision/96ad24cf8da42e976fb8e797a7136c4ce8d7eb5f3ba244ace94af573aac1645a/Miscellaneous Connectors.SchLib|C:\Users\justa\Downloads\Miscellaneous Connectors\Miscellaneous Connectors.SchLib|
|pendiente revisión|auxiliary|project/pcb/vendor_assets_local/pendiente_revision/099c2bd29df1714c0132d3b227703c505c0dd75fb68cd626ac6af1a5ff89615d/Miscellaneous Connectors.IntLib|C:\Users\justa\Downloads\Miscellaneous Connectors\Project Outputs for Miscellaneous Connectors\Miscellaneous Connectors.IntLib|
|pendiente revisión|3d|project/pcb/vendor_assets_local/pendiente_revision/7d544bf881b374142e5f7bb976fd7435469a1d191fef4bbffdb01402db1d139f/RN73H1JTTD8762B25.STEP|C:\Users\justa\Downloads\RN73H1JTTD8762B25 (1)\RN73H1JTTD8762B25.STEP|
|pendiente revisión|3d|project/pcb/vendor_assets_local/pendiente_revision/779b96c02aef8d5f53d7118609f123d8c41c8388e42c553aa685d25baae33e5e/RESC1005X35N.step|C:\Users\justa\Downloads\RT0402DRE0739K7L\RESC1005X35N.step|
|pendiente revisión|auxiliary|project/pcb/vendor_assets_local/pendiente_revision/2d1b10918b7deed86376eb052f961fc6a72b6fa43ef0105fecb371ff6ef692d9/shared_lib.PcbLib|C:\Users\justa\Downloads\shared_lib\shared_lib.PcbLib|
|pendiente revisión|auxiliary|project/pcb/vendor_assets_local/pendiente_revision/84dbceee0491c7971d2baad97a299f01a93a41e075adcf2d13b83fe7f1f246f4/shared_lib.SchLib|C:\Users\justa\Downloads\shared_lib\shared_lib.SchLib|

## Limitaciones y validación
El stock se mantiene NO VERIFICADO; las páginas públicas no garantizan cantidad reservable en JLC. Hubo rutas web inaccesibles, una ficha oficial con 403, CAD Altium sin conversión y avisos de extracción PDF. Detalle en unresolved_issues.md. No se probaron eléctricamente componentes, no se corrió simulación y no se aprobó el diseño. El resultado de verificaciones de archivos figura en verification_results.json. La siguiente fase queda sujeta a revisión humana de este inventario.

