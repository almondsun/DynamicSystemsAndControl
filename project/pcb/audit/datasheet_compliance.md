# Trazabilidad de requisitos a datasheets

Fecha: 2026-10-24. Documento de revisión; **no equivale a aprobación de componentes**. Cálculos completos: [requisitos de pasivos](passives_requirements.md). Códigos de evidencia:

- **E:** condición explícita de fabricante, válida bajo las condiciones de su tabla.
- **R:** recomendación o circuito típico de fabricante; no convertirla en límite garantizado.
- **C:** cálculo propio con hipótesis expresas.
- **H:** hipótesis pendiente de confirmación o medición.

Los números de página siguientes son páginas físicas del PDF indicado, contando la portada como1. Si cambia la revisión del documento, repetir la comprobación. Las copias descargadas se conservan; hashes SHA-256 en `artifacts/passives_20261024/local_datasheet_hashes.json`.

## IC y semiconductores que condicionan los pasivos

|ID|Documento primario y versión consultada|Localizador|Aplicación y límite de evidencia|
|---|---|---|---|
|D1|Infineon [IR2110/IR2113, Rev.V](https://www.infineon.com/assets/row/public/documents/24/49/infineon-ir2110-datasheet-en.pdf); copia local `../vendor_assets_local/datasheets/C2968.pdf`|pp.2–3 tablas de condiciones y características; p.5 conexiones; p.6 temporización|VCC/VBS recomendados10–20 V; IQBS/ILK y UVLO sirven al bootstrap. Los tiempos se especifican con cargas/tensiones de ensayo distintas del montaje real|
|D2|UMW78Mxx, Jan2025, 16 páginas; copia `../vendor_assets_local/datasheets/C347278.pdf`|p.2 límites/térmica; p.3 §7.1 78M05; p.12 §9 circuito típico; p.14 TO252|Fuente de 0.33/0.1 µF, regulación, IQ y térmica. Portal oficial: [UMW78M05](https://www.umw-ic.com/zh-CN/product?search_key=78M05). URL directa oficial de esa revisión no recuperada; no confundir con ST7805|
|D3|TI [SN74HCT14, SCLS225G](https://www.ti.com/lit/ds/symlink/sn74hct14.pdf)|p.4 §6.3; p.5 §6.5; p.10 §§10–11|Rango4.5–5.5 V, umbrales Schmitt y bypass local. Los límites se leen en la condición de temperatura/carga correspondiente|
|D4|TI [SN74HCT00, SCLS062F](https://www.ti.com/lit/ds/symlink/sn74hct00.pdf)|p.4 §5.2; p.5 §5.4; p.8 §§8–9|Bypass100 nF recomendado, entradas sin flotar y niveles TTL; el latch completo deriva de sus conexiones, no del datasheet como circuito de protección certificado|
|D5|TI [LM393B, SLCS005AH, Apr2025](https://www.ti.com/lit/ds/symlink/lm393.pdf)|p.6 §5.5; p.7 §5.7; tabla de pines p.3|Usar tablas **B** para LM393BIDR, no tablas legacy. Offset/rango común/VOL y tiempos típicos condicionan divisores/pull-up. El máximo offset a VS≥5 V no garantiza el caso4.75 V|
|D6|TI [INA180, SBOS741H](https://www.ti.com/lit/ds/symlink/ina180.pdf)|p.3 pines; p.8 tabla eléctrica; p.21 §9.1.1/Fig.9-1; p.22 §9.1.2/Ec.1; p.23 §9.1.3; pp.27–28 §9.4/Fig.9-7|Ganancia A1=20, shunt, bypass cercano y conexiones Kelvin. Confirmar variante A: no usar pinout INA180B|
|D7|UMWIRFZ44N/NS, copia local `../vendor_assets_local/datasheets/C5199867.pdf`, Nov2024, 11 páginas|pp.1–2 límites y tabla eléctrica; gráficos de gate/carga de esa copia|RDS máximo17 mΩ a 10 V y Qg típico50 nC en condiciones de tabla; no son límites garantizados a toda temperatura. [PDF oficial recuperado](https://www.umw-ic.com/static/pdf/a2d981f02a82712386b830ebbbca8b43.pdf) tiene8 páginas: resolver revisión/encapsulado antes de aprobación|
|D8|MDDSS34, copia local `../vendor_assets_local/datasheets/C8678.pdf`, 3 páginas|p.1 tabla y notas térmicas; p.2 curvas; p.3 dibujo/land|VF para pérdidas/recirculación y paqueteSMA; condiciones de cobre del ensayo no son la placa real. Portal [MDD](https://www.microdiode.com); no se obtuvo enlace directo oficial de la copia exacta|
|D9|Changjing [MMBT3904 SOT23V2](https://www.jscj-elec.com/gallery/file/MMBT3904%20SOT-23V2.pdf); copia `../vendor_assets_local/datasheets/C20526.pdf`|p.1 pinout/tabla; p.3 dimensiones|1=B, 2=E, 3=C. Condiciones de VCEsat de tabla no coinciden con las corrientes muy pequeñas de este circuito; comprobar en montaje|

**Diodo bootstrap D2/US1G:** código histórico C3034075. No se recuperó en esta revisión una ficha oficial exacta ShunYe con límites de fuga y recuperación aplicables. VF=0.9 V e ID2=10 µA empleados en el presupuesto son **H**, no especificaciones documentadas de esa pieza. Es un bloqueo explícito, no se reemplaza su ficha por una US1G de otro fabricante.

## Matriz de cumplimiento por subsistema

|Ref./red|Requisito o decisión|Clase|Fundamento/localizador|Estado de cumplimiento|
|---|---|---|---|---|
|C1/C2|≥0.60 A RMS por pieza a 10 kHz, 25 V; ≥160 µF banco efectivo|C|ICIN por carga pulsante en CCM; envolvente y reparto60/40 en requisitos §3|Especificación calculada, montaje por validar; candidato histórico EMZR insuficiente|
|C1/C2 polímero|Corregir rating de 100 kHz a 10 kHz; comprobar vida y ESR|E/C|Panasonic [SVPF](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000C177.pdf), p.2; [SVF](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000C211.pdf), p.2; factor0.7|Corriente corregida calculada; ESR a 10 kHz y temperatura real pendientes|
|C3|100 nF rápido en VIN; 50 V; baja ESL|C|Desacoplo del lazo de conmutación; especificación original y presupuesto de ruido|Requisito de ingeniería; no se atribuye a un mínimo de capacitancia del MOSFET|
|C4/C5|20 µF nominal/≥16 µF efectivos; ESR banco≤0.15 Ω; ≥0.15 A/pieza|C|Balance de carga ΔV≈ΔIL/(8fsC)+ΔIL·ESR, cálculo §3|Polímeros candidatos; hipótesis de C mínima y ESR a 10 kHz por cerrar|
|C4/C5 rating|50SVF10M/50SVPF10M; frecuencia de rizado y polaridad|E|Catálogos Panasonic anteriores pp.1–2, tamañosC6 y tabla de 10 µF/50 V; guía de montaje al final|Evidencia documental; no ensayo ni aprobación de land|
|L1/L2|L efectiva≥528 µH; Irms≥1.5 A; Isat≥3 A con definición; DCR20 total≤0.20 Ω deseable|C/H|Ecuaciones CCM y retardo de falla supuesto10 µs en §4|Irms calculada; margen de saturación requiere curva L(I, T) y ensayo|
|L1/L2 Murata|80 mΩ/330 µH frente a 135 mΩ/680 µH|E parcial|[Guía oficial6000B](https://www.murata.com/-/media/webrenewal/support/library/catalog/products/power-products/power-magnetics.ashx?cvid=20260202012717000000&la=en-gb), tabla6000B|Solo selección preliminar; ficha completa no recuperada; corriente del catálogo no demuestra Isat|
|RS1|50 mΩ; potencia útil≥1 W recomendada, Kelvin y error de cobre|R/C|D6 §9.1.2/Ec.1 y §9.4; P=IRMS²RS; presupuesto de error parásito|Cálculo conforme a método; ruteo físico y TCR sin validar|
|RS1 TA-I|No asumir2 W fuera de condiciones de montaje|E|[TA-I RLP](https://www.tai.com.tw/files/uploads/Prod_spec/RLP.pdf), p.1 codificación, p.4 notas1–2 y p.6 derating|Falta confirmar 300 mm² y cobre105 µm o justificar potencia útil reducida|
|R1|10 Ω; validar pulso≈1.33 A/17.6 W, no solo promedio|C/H|D7 Qg típico; impedancia driver D1; modelo energético Qg·VGS·fs|Sin curva de pulsos aplicable ni medición; ERJ-P6W investigada es NRND|
|R2|10 kΩ G-S; incluir hasta 1.333 mA en carga de C6|C|Ohm13.2 V/9.9 kΩ; conectividad original|Omisión histórica corregida en presupuesto; funcionamiento por medir|
|C6|Dimensionar por Q total y margen VBS; objetivo≥1 µF efectivo|E/C/H|D1 pp.2–3 para VBS/IQBS/ILK; [método InfineonIR2x14](https://www.infineon.com/assets/row/public/documents/24/49/infineon-ir2x14ss-datasheet-en.pdf), §2.2; Qls/Qg/fugas supuestos aquí|No se transfieren parámetros IR2114 al IR2110; C efectiva y recarga pendientes|
|C7/C8|Desacoplos locales VCC/VDD; reservaC18 propuesta|C|D1 esquema de aplicación/pines y carga de recarga estimada|100 nF original conservado como rápido; C18 no es valor obligatorio de fabricante|
|C9/C10|0.33 µF entrada/0.1 µF salida próximos a U2|R|D2 p.12 §9 circuito típico|Se conserva función; ESR admisible con C11 no publicado ni aprobado|
|C11|10 µF de reserva5 V; objetivo≥5 µF efectivos|C/H|Demanda de carga del control; presupuesto de polarización Samsung|No es valor impuesto por UMW; estabilidad con cerámicos pendiente|
|C12/C13|100 nF local, entradas lógicas no flotantes|R/E|D3 §10 p.10 y D4 §8–9 p.8|Capacitancia nominal coincide; colocación y conexiones futuras por revisar|
|C14|100 nF local en U5|C|Presupuesto propio de desacoplo, conservando BOM; alimentación D5|No atribuido como mínimo absoluto a TI; ruido/protección por medir|
|C16|Bypass al menos0.1 µF cercano a INA180|R|D6 p.21 §9.1.1/Fig.9-1|TI indica bypass≥0.1 µF; exigir ese mínimo **efectivo** y proponer 220 nF son margen C, no nuevo mínimo explícito de TI|
|R3/R4|Niveles PWM y corriente con MCU desalimentado|E/C/H|D3 p.5 Schmitt; Ohm con rail5 V y MCU3.3 V; clamp MCU supuesto|Tensiones nominales calculadas; límites VOH/VOL e inyección del STM32 exacto pendientes|
|R5/R6|10 kΩ pull-down y estado de arranque|E/C|D4 §9 entradas definidas; ecuaciones latch `design.py`|Resistencias suficientes estáticamente; arranque/brownout físico pendiente|
|R7|4.7 kΩ; hundimiento≤1.13 mA y VOL compatible HCT|E/C|D5 p.6 §5.5 VOL con 4 mA; D4 niveles entrada; Ohm|Carga menor que condición de tabla; parasíticos/tiempo pendientes|
|R8/R9/C15|VREF2 V nominal y τ0.60 ms; esperar referencia estable|C/H|Divisor de 5 V, Rth6 kΩ y 100 nF; errorU2 D2 §7.1|Umbral por esquinas calculado, arranque y bias/temperatura por cerrar|
|R10/R11|OVP8.2 V nominal, tolerancias y común modo|E/C/H|D5 §5.5 y nota de rango común; divisor31k/10k|No declarar VOUT<8.2 V garantizado. NotaTI permite un input fuera del rango común si el otro permanece válido, dentro de límites indicados; no rechazar por aplicar la restricción a ambos a la vez|
|R12/R13|BaseQ2/pull-up3.3 V:0.43/≈0.35 mA nominales|E/C/H|D9 p.1 y Ohm; conectividad NFAULT_MCU|No se traslada VCEsat garantizado de 50 mA a este punto sin comprobación; pinoutSMD documentado|
|R14/R15|ADC≈VOUT/4; precisión y sobretensión transitoria|C/H|Divisor con 1%; energía almacenada de L; STM32 exacto pendiente|Rangos y errores calculados; falta clamp/secuencia y aprobación del pulsoR14; bloqueante|
|C17|C0G1 nF;τ0.75 µs/fc212 kHz|E/C/H|[FenghuaMPN](https://www.fhcomp.com/zh-cn/product_info/?prod_code=0603CG102J500NT) para dieléctrico/rating; cálculoRC propio|No es filtro que elimine10 kHz; adquisición ADC y aliasing pendientes|

## Reglas que proceden de la ingeniería y no de una guía del curso

Los márgenes de 50% en resistencias, 25% en corriente RMS de capacitores, reparto60/40, ΔT40 °C de bobinas/10 °C de capacitores, techo85 °C de cuerpo, VIN±10%, retardo objetivo10 µs y límites de rizado son **propuestas propias**. No se atribuyen a la tarea académica ni a un fabricante. Deben aceptarse o ajustarse antes de seleccionar definitivamente.

La guía exige medir los componentes reales. Por ello la tolerancia inicial de una bobina/MLCC no sustituye L bajo corriente o C bajo tensión. Los catálogos con curvas típicas orientan el cálculo y pueden exigir medición o especificación de entrega para garantizar mínimos.

## Evidencia de encapsulado y montaje

La comprobación preliminar de ocho archivos de huellas reales de KiCad10 está en [candidatos](jlc_passives_candidates.md), con pads y hashes en `artifacts/passives_20261024/footprint_checks.json`. Para resistores/cerámicos se contrastó tamaño métrico; falta aprobación de terminaciones/land/térmica para cada compra. Para polímeros se consultó [Panasonic, condiciones de montaje y lands](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000COL10.pdf), p.1; la comparación completa de lands sigue pendiente. Ninguna huella descargada queda aprobada por su nombre.

Faltan fichas exactas y/o revisión de: D2ShunYeUS1G, bobinasXR, ficha completa Murata6000B, pulso repetitivo de R1, curvaDCbias de los MLCC, presupuesto de umbral con TCR75 ppm/°C del shunt alternativo y STM32/clon realmente instalado. Esas ausencias se conservan como bloqueos en [open_issues.md](open_issues.md).
