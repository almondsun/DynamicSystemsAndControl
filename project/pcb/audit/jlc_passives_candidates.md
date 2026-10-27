# Candidatos comerciales de pasivos

Consulta: **2026-10-24**. Selección **preliminar**. Requisitos y cálculos: [passives_requirements.md](passives_requirements.md). Ninguna fila autoriza sustituir componentes ni asignar footprints.

Se priorizan Basic para resistencias y desacoplos cuando cumplen la función. Para almacenamiento de energía, shunt, dieléctrico C0G y resistencia de compuerta se priorizan características técnicas. No se encontró una alternativa Basic demostrada para cada una de esas funciones. Extended no implica disponibilidad y Basic no implica aprobación eléctrica.

## Condición comercial de la consulta

**Stock de todos los candidatos: NO VERIFICADO en tiempo real.** Las páginas accesibles incluyen contenido indexado o cacheado; algunos resultados se contradicen. La columna de clase transcribe la ficha consultada cuando pudo leerse; no certifica la clasificación al realizar el pedido. Precio vigente: **NO VERIFICADO**, salvo las observaciones históricas separadas al final. Confirmar MPN, código, montaje, clase y cantidad con JLC antes de comprar.

## Entrada, salida, shunt e inductores

|Grupo|Fabricante y MPN exacto|Código y catálogo|Clase observada|Parámetros y encapsulado|Motivo y diferencias|Verificaciones pendientes / estado|
|---|---|---|---|---|---|---|
|C1/C2, opción A|Panasonic **25SVPF100M**|[C136279](https://jlcpcb.com/partdetail/PANASONIC-25SVPF100M/C136279)|NO VERIFICADO|100 µF ±20%, 25 V; polímero SMD Ø8 ×6.9 mm; 24 mΩ a 100 kHz; 3.2 A a 100 kHz/105 °C; factor0.7 a 10 kHz|Conserva200 µF nominales con dos piezas; capacidad de rizado documental superior al EMZR preliminar|ESR a 10 kHz, vida, reparto, C efectiva y land pattern; candidato preferido condicional|
|C1/C2, opción B|Panasonic **25SVF100M**|[C454370](https://jlcpcb.com/partdetail/PANASONIC-25SVF100M/C454370)|Extended|100 µF ±20%, 25 V, Ø8 ×6.9 mm; 24 mΩ; 3.2 A hasta 105 °C a 100 kHz, derating adicional hasta 125 °C|Alternativa de serie distinta; no trasladar condiciones de vida de SVPF|Mismos pendientes; stock mostrado escaso y cacheado, no disponible confirmado|
|C4/C5, opción A|Panasonic **50SVF10M**|[C454354](https://lcsc.com/product-detail/Solid-Polymer-Electrolytic-Capacitor_PANASONIC-50SVF10M_C454354.html)|NO VERIFICADO|10 µF ±20%, 50 V, polímero SMD Ø6.3 ×5.9 mm; 40 mΩ a 100 kHz; 2.5 A a 100 kHz hasta 105 °C; factor0.7 a 10 kHz|Dos piezas conservan20 µF nominales; mayor tensión que35 V original; baja ESR|Código encontrado en índice LCSC; ficha comercial no recuperada completa; confirmar asociación y compra. C/ESR a 10 kHz y efecto sobre control pendientes|
|C4/C5, opción B técnica|Panasonic **50SVPF10M**|Código JLC/LCSC **sin confirmar**; [fabricante](https://industrial.panasonic.com/ww/products/pt/os-con/models/50SVPF10M)|NO VERIFICADO|10 µF ±20%, 50 V; Ø6.3 ×5.9 mm; 40 mΩ, 2.5 A a 100 kHz/105 °C|Alternativa documental real; no presentada como componente JLC localizado|Cerrar código/comercialización, land, C efectiva, ESR; no aprobada|
|RS1, opción A|TA-I **RLP25FEER050**|[C160588](https://jlcpcb.com/partdetail/ta_iTech-RLP25FEER050/C160588)|Extended|50 mΩ ±1%; código E2 W; 2512, 6.4 ×3.2 mm; TCR50 ppm/°C según rango|Conserva resistencia; potencia mayor de catálogo condicionada al montaje|**2 W requieren cobre105 µm y 300 mm² de pads/pistas** según fabricante. No acreditar2 W en cobre estándar sin evidencia; Kelvin y derating pendientes|
|RS1, opción B|Vishay Dale **WSL2512R0500FEA**|[C413486](https://www.lcsc.com/de/product-detail/C413486.html)|NO VERIFICADO|50 mΩ ±1%, 1 W; 2512; metal strip; TCR componente±75 ppm/°C a 50 mΩ (tabla oficial p.2)|Potencia nominal original, alternativa de fabricante con ficha técnica|Recalcular umbral con 75 ppm/°C; confirmar derating, land y tolerancia térmica; dos terminales, cuatro trazas Kelvin|
|L1/L2, opción SMD|Murata Power Solutions **60B334C**, dos unidades|[C6823957](https://www.lcsc.com/pl/product-detail/power-inductors_murata-electronics-60b334c_C6823957.html)|NO VERIFICADO|330 µH ±15% en ficha de familia indexada; catálogo oficial4 A y 80 mΩ; serie6000B, altura20 mm|Dos piezas suman660 µH, DCR nominal de catálogo160 mΩ; SMD grande|Ficha completa oficial no recuperada: falta condición de corriente, Isat/L(I, T), núcleo y land. Dimensiones externas discordantes entre fuentes; **sin aprobación**|
|L1/L2, opción THT existente|XR **XR6826TS331MHL65**|[C22447628](https://jlcpcb.com/partdetail/XR-XR6826TS331MHL65/C22447628)|Extended / Wave según catálogo|330 µH ±10%, Ø23 mm; 3.2 A e Isat6.5 A publicados por catálogo|Retener THT puede ser preferible a SMD insuficiente; dos piezas mantienen objetivo|Falta ficha primaria exacta, DCR, definición Isat, temperatura y núcleo; no aprobar por corrientes comerciales|
|L equivalente única, comparación|Murata Power Solutions **60B684C**|Código JLC/LCSC **sin confirmar**; [guía oficial](https://www.murata.com/-/media/webrenewal/support/library/catalog/products/power-products/power-magnetics.ashx?cvid=20260202012717000000&la=en-gb)|NO VERIFICADO|680 µH; 3 A y 135 mΩ publicados; familia6000B|+3.03% sobre660 µH; menor DCR que dos 330 de la misma serie; elimina acoplamiento entre piezas|No es reemplazo autorizado; L(I, T), saturación, pérdidas, land, stock y código pendientes|

Datasheets primarios: [SVPF](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000C177.pdf), [SVF](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000C211.pdf), [TA-I RLP](https://www.tai.com.tw/files/uploads/Prod_spec/RLP.pdf), [Vishay WSL](https://www.vishay.com/docs/30100/wsl.pdf), [guía Murata](https://www.murata.com/-/media/webrenewal/support/library/catalog/products/power-products/power-magnetics.ashx?cvid=20260202012717000000&la=en-gb). La guía Murata no cierra las condiciones de saturación; no inferirlas de 4 A/3 A.

## Resistencias de señal y de compuerta

Todos los valores de señal siguientes son1%, salvo que se indique lo contrario. El presupuesto de precisión requiere revisar TCR/razón/calibración; no están aprobados por compartir valor con la BOM.

|Referencias|Fabricante / MPN|Código y catálogo|Clase observada|Características / encapsulado|Fundamento y pendiente|
|---|---|---|---|---|---|
|R2/R3/R5/R6/R9/R11/R12/R13|UNI-ROYAL **0603WAF1002T5E**|[C25804](https://jlcpcb.com/partdetail/C25804)|Basic|10 kΩ, 0.1 W, 0603; TCR de serie a confirmar para lote|Potencia holgada en cálculos. R9/R11 precisan presupuesto de deriva; R2 afecta directamente al bootstrap|
|R4/R15; R10B solo propuesta|UNI-ROYAL **0603WAF1001T5E**|[C21190](https://jlcpcb.com/partdetail/C21190)|Basic|1 kΩ, 0.1 W, 0603|R4≤27.9 mW en falla presupuestada. R15 exige resolver sobretensión ADC; no aprobar por potencia|
|R7|UNI-ROYAL **0603WAF4701T5E**|[C23162](https://jlcpcb.com/partdetail/23889-0603WAF4701T5E/C23162)|Basic|4.7 kΩ, 0.1 W, 0603|Pull-up≤1.13 mA; revisar VOL/retardo con carga y pistas reales|
|R8|UNI-ROYAL **0603WAF1502T5E**|[C22809](https://lcsc.com/product-detail/Chip-Resistor-Surface-Mount_Uniroyal-Elec-0603WAF1502T5E_C22809.html)|NO VERIFICADO|15 kΩ, 0.1 W, 0603|Conserva referencia nominal; precisión de U2/TCR limita umbral, aunque la potencia sea pequeña|
|R14, opción económica|UNI-ROYAL **0603WAF3001T5E**|[C4211](https://jlcpcb.com/partdetail/0603WAF3001T5E/C4211)|NO VERIFICADO|3 kΩ, 0.1 W, 0603|Adecuada solo al presupuesto continuo13.2 V y derating supuesto; **pulso por energía de L y precisión pendientes**|
|R14, alternativa documental|Yageo **RC0603FR-073KL**|[C126358](https://www.lcsc.com/product-detail/C126358.html)|NO VERIFICADO|3 kΩ, 1%, 0.1 W, 100 ppm/°C, 0603|[Ficha oficial](https://yageogroup.com/component-documentation/download/specsheet/RC0603FR-073KL); no mejora tolerancia respecto al Basic; mismo bloqueo de pulso/ADC|
|R10A, solo propuesta|Yageo **RC0603FR-0730KL**|[C100001](https://www.lcsc.com/product-detail/C100001.html)|Extended observado|30 kΩ, 1%, 0.1 W, 0603|Con R10B1 kΩ suma31 kΩ; requiere nueva referencia futura. **No usar 30 kΩ sola**|
|R1, opción de valor conservado|UNI-ROYAL **0805W8F100JT5E**|[C17415](https://jlcpcb.com/partdetail/C17415)|NO VERIFICADO|10 Ω, 1%, 0.125 W, 0805|Potencia media pequeña, pero falta curva de pulsos repetitivos para≈17.6 W de pico; no aprobada|
|R1, alternativa investigada descartada como preferencia nueva|Panasonic **ERJ-P6WF10R0V**|[C4217693](https://www.lcsc.com/product-detail/C4217693.html), asociación pendiente de reconfirmación|NO VERIFICADO|10 Ω, 1%, 0.5 W, 0805, antisurge|Ficha de fabricante hospedada por [Mouser](https://www.mouser.com/datasheet/2/315/RDO0000C337-1279426.pdf), pp.1–2: serie **no recomendada para diseños nuevos**. No elegida; buscar sucesor con curva de pulso|

Referencia dimensional y de tensión para la serie UNI-ROYAL: [Royal Ohm, resistencias SMD](https://www.royalohm.com/assets/pdf/products/smd/1.pdf). Validar la especificación aplicable al MPN completo. Tensión continua admisible es el menor de la tensión límite del cuerpo y √(Pútil·R), no simplemente75 V por ser0603.

No se localizó una 31 kΩ exacta aprobable en la consulta. **RC0603FR-0731K6L/C185339 de 31.6 kΩ no es equivalente**: OVP nominal8.32 V frente a 8.20 V. Alternativa de precisión0.1%/bajo TCR sin código exacto cerrado: pendiente; no inventar MPN.

## Cerámicos de desacoplo, bootstrap y filtros

|Ref./grupo|Fabricante / MPN exacto|Código y catálogo|Clase observada|Datos / cuerpo|Motivo y verificación pendiente|
|---|---|---|---|---|---|
|C3/C7/C8/C10/C12/C13/C14/C15|Yageo **CC0603KRX7R9BB104**|[C14663](https://jlcpcb.com/partdetail/YAGEO-CC0603KRX7R9BB104/C14663)|Basic|100 nF, 50 V, X7R,±10%; 1.6×0.8 mm|[Ficha oficial](https://yageogroup.com/download/specsheet/CC0603KRX7R9BB104); verificar C efectiva, cercanía y retorno; no sustituye bulk|
|C6; C6A/B y C18 propuestos|Samsung **CL21B105KBFNNNE**|[C28323](https://jlcpcb.com/partdetail/C28323)|Basic|1 µF, 50 V, X7R,±10%, 0805; cuerpo2×1.25×1.25 mm nominal|[Ficha de familia exacta](https://product.samsungsem.com/mlcc/CL21B105KBFNNN.do); una pieza nominal no garantiza1 µF efectiva. Dos en paralelo solo propuesta; comprobar bias y recarga|
|C6, segunda opción de cuerpo|Samsung **CL31B105KAHNNNE**|[C28322](https://www.lcsc.com/product-detail/C28322.html)|NO VERIFICADO|1 µF, 25 V, X7R,±10%, 1206|[Fabricante](https://product.samsungsem.com/mlcc/CL31B105KAHNNN.do); tensión suficiente al régimen previsto, menor reserva que50 V original; C efectiva y recarga siguen pendientes|
|C9|Samsung **CL21B334KBFNNNE**|[C73142](https://jlcpcb.com/partdetail/74255-CL21B334KBFNNNE/C73142)|Extended|330 nF, 50 V, X7R,±10%, 0805; cuerpo2×1.25×1.25 mm nominal|[Fabricante](https://product.samsungsem.com/mlcc/CL21B334KBFNNN.do); valor de aplicación UMW; no confundir valor nominal con mínimo efectivo|
|C11|Samsung **CL21A106KAYNNNE**|[C15850](https://jlcpcb.com/partdetail/CL21A106KAYNNNE/C15850)|Basic|10 µF, 25 V, X5R,±10%, 0805; 2×1.25×1.25 mm nominal|[Fabricante](https://product.samsungsem.com/mlcc/CL21A106KAYNNN.do); objetivo≥5 µF efectivo; estabilidad con 78M05 no demostrada para todo ESR|
|C16, incremento propuesto|Yageo **CC0603KRX7R9BB224**|[C107083](https://jlcpcb.com/partdetail/YAGEO-CC0603KRX7R9BB224/C107083)|Extended|220 nF, 50 V, X7R,±10%, 0603|Se busca sostener≥100 nF efectivos; [ficha oficial](https://yageogroup.com/download/specsheet/CC0603KRX7R9BB224), p.1 y advertencia p.4: gráficas típicas no garantizan mínimos. La opción original100 nF/C14663 sigue como referencia histórica, no rechazada automáticamente|
|C17|Fenghua **0603CG102J500NT**|[C1636](https://jlcpcb.com/partdetail/1988-0603CG102J500NT/C1636)|Extended|1 nF, 50 V, C0G,±5%, 1.6×0.8 mm|[Fabricante](https://www.fhcomp.com/zh-cn/product_info/?prod_code=0603CG102J500NT); estabilidad de τ. No se demostró opción Basic C0G exacta; adquisición ADC pendiente|

Los suffixes de empaque E de Samsung deben verificarse en la ficha comercial; las páginas oficiales enlazadas describen el núcleo del MPN. No se consideró válido automáticamente un modelo CAD por estar descargado.

## Huellas: comprobación realizada y límites

Se inspeccionaron archivos reales de la biblioteca instalada de **KiCad10**, sin asignarlos al proyecto. Su SHA-256, pads y geometría quedan en `artifacts/passives_20261024/footprint_checks.json`. Los nombres siguientes son propuestas de biblioteca, no cambios al esquema:

|Huella instalada|Pads1/2: posición X, Y; tamaño X×Y (mm)|Comparación / estado|
|---|---|---|
|`Resistor_SMD:R_0603_1608Metric`|1: (-0.825 0), 0.8 0.95; 2: (0.825 0), 0.8 0.95|Cuerpo métrico compatible preliminar; land/ensamblaje por aprobar|
|`Resistor_SMD:R_0805_2012Metric`|1: (-0.9125 0), 1.025 1.4; 2: (0.9125 0), 1.025 1.4|Cuerpo métrico compatible preliminar; land/ensamblaje por aprobar|
|`Resistor_SMD:R_2512_6332Metric`|1: (-2.9625 0), 1.225 3.35; 2: (2.9625 0), 1.225 3.35|RLP6.4×3.2 frente a cuerpo métrico6.3×3.2; comparar terminaciones TA-I/Vishay y cobre térmico; pendiente|
|`Capacitor_SMD:C_0603_1608Metric`|1: (-0.775 0), 0.9 0.95; 2: (0.775 0), 0.9 0.95|Cuerpo métrico compatible preliminar; land/ensamblaje por aprobar|
|`Capacitor_SMD:C_0805_2012Metric`|1: (-0.95 0), 1 1.45; 2: (0.95 0), 1 1.45|Cuerpo métrico compatible preliminar; land/ensamblaje por aprobar|
|`Capacitor_SMD:C_1206_3216Metric`|1: (-1.475 0), 1.15 1.8; 2: (1.475 0), 1.15 1.8|Cuerpo métrico compatible preliminar; land/ensamblaje por aprobar|
|`Capacitor_SMD:CP_Elec_8x6.9`|1: (-3.475 0), 4.15 1.9; 2: (3.475 0), 4.15 1.9|Cuerpo compatible con E7/C6 Panasonic; pads1/2 presentes; cerrar polaridad símbolo y land; pendiente|
|`Capacitor_SMD:CP_Elec_6.3x5.9`|1: (-2.8 0), 3.5 1.6; 2: (2.8 0), 3.5 1.6|Cuerpo compatible con E7/C6 Panasonic; pads1/2 presentes; cerrar polaridad símbolo y land; pendiente|


Para los polímeros se contrastó el tamaño de cuerpo con el catálogo Panasonic. La [guía de montaje](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000COL10.pdf), p.1, contiene land patterns y perfiles según código de cuerpo. Falta cerrar la comparación dimensional completa de esos lands con KiCad y con la capacidad de ensamblaje de JLC; geometría externa coincidente no garantiza soldabilidad. En los condensadores polarizados, verificar **pad1 positivo/pad2 negativo** contra símbolo y banda negativa del fabricante; no inferirlo de un modelo3D. Los resistores y cerámicos citados son de dos terminales no polarizados; las bobinas requieren confirmar terminales y construcción de la variante.

## Observaciones de precio/stock, separadas de la disponibilidad

|MPN|Texto observado el 2026-10-24 en páginas recuperadas|Limitación|
|---|---|---|
|25SVPF100M|JLC indexado425 unidades y 1+ USD1.0665; LCSC otra página2236 y 1+ USD0.867; otra URL indica agotado|Resultados contradictorios/cacheados; stock y precio vigente NO VERIFICADOS|
|25SVF100M|JLC cacheado2 unidades; 1+ USD1.2975|No constituye reserva ni consulta de inventario transaccional|
|RLP25FEER050|Página JLC antigua3932 unidades/3822 disponibles; 1+ USD0.0495|Dato antiguo; no utilizar para compra actual|
|CL31B105KAHNNNE|LCSC recuperado14830 unidades; 10+ USD0.0434|Sin garantía de actualización en tiempo real ni de clase JLC|

Para las demás filas no se registra precio o cantidad utilizable: **NO VERIFICADO**. No trasladar stock de DigiKey/Mouser a JLC. Ningún precio incluye una cotización final de montaje.

## Candidatos investigados que no deben aprobarse

- **EMZR250ARA101MF61G/C3829858**, entrada:300 mA por pieza a 100 kHz, insuficiente para el presupuesto a 10 kHz, incluso antes de márgenes.
- **BXJ35V10UF05*05/C20539298**, salida:800 mΩ por pieza publicados y montaje Wave; no cumple objetivo propuesto de ESR y reflow no demostrado.
- **Bourns SRR1260-331K/C2041330**: [datasheet oficial](https://www.bourns.com/pdfs/SRR1260.pdf), p.1:1.15 A RMS, Isat típico1.10 A, DCR580 mΩ; insuficiente. **SRR1260-681K** también insuficiente.
- No se aprueba una bobina por 330/680 µH ni un capacitor por 100/10 µF; las condiciones mínimas se mantienen en el documento principal.
