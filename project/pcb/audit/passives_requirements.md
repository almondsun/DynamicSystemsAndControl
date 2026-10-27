# Requisitos y selección preliminar de pasivos del Buck

Fecha de consulta: **2026-10-24**. Resultado: **35 pasivos originales inventariados; selección condicionada, sin liberación para fabricación**. Son 16 resistencias (R1–R15 y RS1), 17 condensadores y dos inductores. No se cambian referencias originales. Las referencias con sufijo A/B y C18 indicadas abajo son propuestas, todavía inexistentes en el circuito.

Documentos relacionados: [comportamiento esperado](expected_behavior.md), [candidatos comerciales](jlc_passives_candidates.md), [cumplimiento de datasheets](datasheet_compliance.md) y [bloqueos](open_issues.md).

## 1. Fuentes, discrepancias y alcance

Se leyeron `../bom.csv`, `../tools/design.py`, `../docs/sources.md`, `../docs/assembly-and-tests.md`, `../VALIDATION.md`, los archivos `buck*.kicad_sch`, `Buck.kicad_sym`, la auditoría local y los PDF en `../vendor_assets_local/datasheets/`. El Excel original está en `C:/Users/justa/Downloads/Auditoria_preliminar_Buck_JLCPCB_2026-10-22.xlsx`; se utiliza su selección histórica, sin editarla. La guía `classroom/Descripcion Proyecto Buck.pdf`, §§3.1–3.4 y §5, establece escenarios y necesidad de medir componentes reales; no establece los nuevos límites térmicos o de rizado de este documento.

La BOM y `design.py` describen la revisión THT. En `Buck.kicad_sym` ya aparecen valores SMD para U1/U3/U4/U5, pero las instancias de esquema de la auditoría mantienen valores/footprints originales. No hay evidencia de una selección SMD definitiva firmada. La exportación de netlist con KiCad CLI falló al intentar acceder a carpetas de configuración/Documentos del usuario; **no se obtuvo una nueva comprobación de paridad eléctrica**. Se conserva la discrepancia y se usa `design.py` como definición explícita para los cálculos, contrastada con valores y etiquetas de los esquemáticos. No ejecutar generadores para resolverla.

|Ref.|Original|Candidato SMD del Excel|Código|Evidencia que afecta pasivos|
|---|---|---|---|---|
|U1|IR2110PBF DIP14|Infineon IR2110STRPBF|C2968|SOIC16 distinto; bootstrap, alimentación flotante y mapa de pines por verificar|
|U2|L7805CV|UMW 78M05 TO-252|C347278|Usar PDF UMW local, no trasladar estabilidad/térmica del ST original|
|U3|SN74HCT14N|TI SN74HCT14DR|C6769|HCT, Schmitt; conservar interfaz TTL y desacoplo|
|U4|SN74HCT00N|TI SN74HCT00DR|C6764|Latch NAND; condiciones de alimentación y arranque|
|U5|LM393P|TI LM393BIDR|C2865059|Variante B; offset, bias y respuesta diferentes del original|
|U6|INA180A1IDBVR|TI INA180A1IDBVR|C122228|A1, ganancia 20; Kelvin y desacoplo|
|Q1|IRFZ44N TO-220|UMW IRFZ44NS|C5199867|No es el Infineon original; Qg y RDS dependen de revisión|
|D1|1N5822|MDD SS34|C8678|Caída y disipación condicionan duty, pérdidas y rizado|
|D2|UF4004|ShunYe US1G|C3034075|Vf, recuperación y fugas deben verificarse para bootstrap|
|Q2|2N3904|Changjing MMBT3904|C20526|PDF local SOT23: 1=B, 2=E, 3=C; no reutilizar orden TO92|

Todos son **candidatos**, no aprobaciones. El PDF UMW local de Q1 (nov.2024, 11 páginas) y el publicado en la [web oficial](https://www.umw-ic.com/static/pdf/a2d981f02a82712386b830ebbbca8b43.pdf) (8 páginas) difieren en presentación. El local muestra Qg típico 50 nC y RDS máximo 17 mΩ a 10 V; 12 mΩ es típico, no el máximo de la tabla. El Qg de 63 nC del Infineon original no se adopta como límite del UMW. Se presupuesta **100 nC** solo como hipótesis de dimensionamiento hasta confirmar ficha del encapsulado/lote SMD.

## 2. Condiciones y modelos

**Condiciones del curso:** VIN=12 V, fs=10 kHz, T=100 µs, L=660 µH, COUT=20 µF, R=6 Ω, d′=0.5; pruebas d′=0.4/0.6, referencias 5/7 V y cargas 4.8/7.2 Ω. Duty físico del MOSFET: D=1−d′.

**Envolvente adicional propuesta de ingeniería:** VIN=10.8–13.2 V, salida regulada 5–7 V, R=4.8–7.2 Ω, ambiente de ensayo 25–45 °C. Se estudia además 7 V/4.8 Ω simultáneos; no se atribuye este caso combinado a la guía. Para dimensionamiento: L efectiva total ≥528 µH, COUT efectiva ≥16 µF. Estos mínimos deben incluir temperatura, corriente y tolerancias; no basta tomar tolerancia de catálogo y olvidar saturación o polarización. Operar a VIN distinto de 12 V requiere aprobar esa extensión, especialmente el margen de bootstrap.

Se distinguen cuatro clases de evidencia:

- **Ideal:** balance estacionario CCM, componentes sin pérdidas.
- **Estimación algebraica con pérdidas:** DCR total a temperatura=0.251 Ω (0.20 Ω a 20 °C y cobre a 85 °C), RS=0.050 Ω, RDS=0.0255 Ω, VF=0.55 V, ESR salida=0.15 Ω. RDS caliente es un factor supuesto 1.5 sobre 17 mΩ, no una garantía de fabricante. Se supone tr+tf=200 ns para estimar conmutación; no se ha medido.
- **Simulación histórica:** archivos `../release/simulation/`, con supuestos distintos, conservados sin reejecutar ni recalificar para SMD.
- **Medición:** no realizada en esta sesión. Cálculos estacionarios no predicen por sí solos los picos de arranque o escalón.

Fórmulas ideales, en SI:

\[
V_O=D V_{IN},\quad I_O=V_O/R,\quad
\Delta I_L=\frac{(V_{IN}-V_O)D}{Lf_s},\quad
I_{pk, min}=I_O\pm\Delta I_L/2.
\]

\[
I_{L, RMS}=\sqrt{I_O^2+\Delta I_L^2/12},\quad
I_{COUT, RMS}=\Delta I_L/\sqrt{12},\quad
I_{CIN, RMS}=\sqrt{I_O^2D(1-D)+D\Delta I_L^2/12}.
\]

\[
\Delta V_{OUT, pp}\lesssim\frac{\Delta I_L}{8f_sC_{OUT}}+\Delta I_L ESR_{OUT}.
\]

La suma de rizado capacitivo y ESR es una cota aproximada conservadora; sus máximos no son necesariamente simultáneos. Se desprecia ESL, ruido de conmutación y la pequeña componente de corriente de carga debida al rizado.

### Escenarios estacionarios ideales a 12 V

|Caso|VO (V)|D|IO (A)|ΔIL (A pp)|IL pico (A)|IL RMS (A)|ICIN RMS (A)|ICOUT RMS (A)|
|---|---|---|---|---|---|---|---|---|
|Nominal|6.0000|0.5000|1.0000|0.4545|1.2273|1.0086|0.5085|0.1312|
|OL dprime0.4|7.2000|0.6000|1.2000|0.4364|1.4182|1.2066|0.5959|0.1260|
|OL dprime0.6|4.8000|0.4000|0.8000|0.4364|1.0182|0.8099|0.3999|0.1260|
|REF 5V|5.0000|0.4167|0.8333|0.4419|1.0543|0.8430|0.4190|0.1276|
|REF 7V|7.0000|0.5833|1.1667|0.4419|1.3876|1.1736|0.5834|0.1276|
|Carga 4.8ohm|6.0000|0.5000|1.2500|0.4545|1.4773|1.2569|0.6318|0.1312|
|Carga 7.2ohm|6.0000|0.5000|0.8333|0.4545|1.0606|0.8436|0.4269|0.1312|
|Combinado 7V 4.8ohm|7.0000|0.5833|1.4583|0.4419|1.6793|1.4639|0.7255|0.1276|

### Estimación algebraica con pérdidas

Para referencia/carga se regula VO; para los dos escalones de duty se conserva D y cambia VO. No es simulación temporal.

|Caso|VO (V)|D|IL pico (A)|ΔIL (A pp)|Pcu L (W)|Pshunt (W)|PMOS conducción (W)|Pdiodo (W)|η etapa estimada (%)|
|---|---|---|---|---|---|---|---|---|---|
|Nominal|6.0000|0.5470|1.2351|0.4702|0.2556|0.0509|0.0142|0.2491|91.08|
|OL dprime0.4|6.6305|0.6000|1.3327|0.4553|0.3109|0.0619|0.0189|0.2431|91.80|
|OL dprime0.6|4.2496|0.4000|0.9361|0.4557|0.1303|0.0259|0.0053|0.2337|88.07|
|REF 5V|5.0000|0.4630|1.0693|0.4720|0.1790|0.0357|0.0084|0.2461|89.59|
|REF 7V|7.0000|0.6311|1.3875|0.4417|0.3457|0.0689|0.0222|0.2367|92.17|
|Carga 4.8ohm|6.0000|0.5533|1.4844|0.4688|0.3968|0.0790|0.0223|0.3071|90.06|
|Carga 7.2ohm|6.0000|0.5428|1.0689|0.4711|0.1789|0.0356|0.0099|0.2095|91.76|
|Combinado 7V 4.8ohm|7.0000|0.6385|1.6771|0.4376|0.5378|0.1071|0.0349|0.2900|91.11|

Modelo de balance: D=[VO+IO(RL+RS)+VF]/[VIN+VF−IO·RDS]. Para D fijo, VO=[D·VIN−(1−D)VF]/[1+(RL+RS+D·RDS)/R]. Se estiman además Psw≈VIN·IO·(tr+tf)·fs/2, PCOUT=ICOUT²·ESR y PCIN=ICIN²·0.012 Ω. La eficiencia omite pérdidas de núcleo y otros términos no caracterizados; no es un límite inferior garantizado.


En nominal: ΔIL=6×0.5/(660 µH×10 kHz)=**0.4545 A pp**; IL, RMS=1.0086 A; ICOUT=0.1312 A; ICIN=0.5085 A. Rizado puramente capacitivo: 0.4545/(8×10000×20 µF)=**0.2841 V pp**; con ESR=0.15 Ω, cota≈0.3523 V pp. No se puede prometer un rizado de 20 mV con esos L/C/fs.

En la envolvente adicional, la evaluación de esquinas ideal arroja ILpk≤1.770 A, IL, RMS≤1.470 A, ICIN≤0.740 A. Al repetir la estimación con pérdidas: ΔIL≤0.650 A pp, ICOUT≤0.188 A e ILpk≤1.775 A. Con COUT=16 µF y ESR=0.15 Ω: cota de rizado≈**0.606 V pp**. Se propone medir ≤0.65 V pp, sin atribuir este límite al curso y sin incluir picos de alta frecuencia. El presupuesto de transitorios se valida aparte.

## 3. Entrada y filtrado de potencia

|Ref.|Función|Valor original|Requisito eléctrico|Requisito térmico|Margen recomendado|Candidato JLC|Estado|
|---|---|---|---|---|---|---|---|
|C1, C2|Reserva y corriente pulsante de entrada|100 µF/25 V cada uno|200 µF nominal total; ≥160 µF efectivos; ≥25 V; cada uno ≥0.60 A RMS a 10 kHz; ESR banco objetivo ≤0.10 Ω|≥105 °C; ΔT por rizado ≤10 °C propuesto; verificar vida y reparto|Tensión: 25/13.2=1.89; reparto de corriente 60/40, con factor 1.25|25SVPF100M C136279; 25SVF100M C454370|Preferidos condicionales; EMZR preliminar insuficiente en rizado|
|C3|Desacoplo rápido VIN|100 nF/50 V|X7R; mantener 50 V; C efectiva objetivo ≥70 nF; baja ESL junto al lazo Q1/D1|−55 a 125 °C o mejor; lejos de bobinas calientes|50/13.2=3.79 en continua; medir sobreimpulsos|CC0603KRX7R9BB104 C14663|Candidato Basic; no reemplaza bulk|
|C4, C5|Filtro de salida|10 µF/35 V low ESR cada uno|20 µF nominal; ≥16 µF efectivos totales; ≥35 V; ESR banco ≤0.15 Ω a 10 kHz; cada uno ≥0.15 A RMS a 10 kHz|ΔT por rizado ≤10 °C propuesto; comprobar temperatura/vida|Banco ≥0.25 A RMS deseable; 35/13.2=2.65 aun ante paso de VIN|50SVF10M C454354; 50SVPF10M (código sin confirmar)|Polímero preferido condicional; BXJ no aprobado|

**Entrada.** Para 7 V/4.8 Ω, IO=1.4583 A y D=0.5833: ICIN=0.7255 A RMS ideal. Con reparto desfavorable 60/40 y factor de diseño 1.25, cada capacitor necesita 0.740×0.60×1.25=**0.555 A RMS**; redondeo propuesto ≥0.60 A a 10 kHz, temperatura de uso. No sumar corrientes de catálogo sin considerar ESR/ESL y reparto entre piezas.

El candidato histórico EMZR250ARA101MF61G declara 0.300 A a 100 kHz por pieza. Incluso dos piezas ideales dan 0.600 A, inferior a 0.6319 A del caso obligatorio 6 V/4.8 Ω, antes de corregir frecuencia y margen. **Se rechaza ese candidato para C1/C2 bajo este presupuesto**, salvo otra ficha exacta que demuestre una capacidad distinta. Su valor y tensión nominales no bastan.

Panasonic SVPF/SVF aporta un coeficiente de rizado **0.7 a 10–100 kHz** en la segunda página de sus catálogos: 25SVPF100M y 25SVF100M, 3.2 A a 100 kHz hasta 105 °C, dan **2.24 A a 10 kHz**. Ese margen es documental para corriente RMS, no una prueba térmica de esta PCB. Véanse [catálogo SVPF](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000C177.pdf) y [SVF](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000C211.pdf), p.2. ESR de catálogo a 100 kHz debe contrastarse a 10 kHz.

La variación aproximada de entrada es IO·D(1−D)/(CIN·fs). Nominal: 1×0.25/(200 µF×10 kHz)=0.125 V pp. Caso 7 V/4.8 Ω, CIN=160 µF: ≈0.222 V pp, más ≈0.146 V por un salto IO sobre ESR banco0.10 Ω. **≤0.40 V pp es un criterio propuesto**, no un resultado medido. Fuente, cable e inductancia de conexión pueden empeorarlo.

**Salida.** ICOUT≈0.188 A RMS en la envolvente con pérdidas; a 60/40, cada pieza recibe≈0.113 A. Con factor1.25:0.141 A; se pide ≥0.15 A a 10 kHz. Para 50SVF10M, la tabla oficial da2.5 A a 100 kHz hasta 105 °C y factor0.7: **1.75 A a 10 kHz por pieza**. Los40 mΩ de ESR a 100–300 kHz sugieren buen margen, pero no garantizan ESR a 10 kHz ni capacitancia a toda temperatura.

BXJ35V10UF05*05 declara800 mΩ por pieza a 100 kHz: dos iguales en paralelo dan400 mΩ. Solo ESR contribuiría0.650×0.4=0.260 V pp y, con 16 µF, la cota total≈0.768 V pp. Además se cataloga Wave, no reflow confirmado. **No cumple el objetivo propuesto de ESR/rizado; no aprobado para liberación.**

Un MLCC10 µF no es equivalente directo: su C efectiva depende de sesgo, tolerancia, temperatura y envejecimiento. Para una hipotética retención DC=0.70:20×0.90×0.85×0.70=10.71 µF, antes de envejecimiento. Es un ejemplo de riesgo, no una curva atribuida a un MPN. No reemplazar C4/C5 con MLCC hasta demostrar C efectiva y recalificar el control/ESR. Los polímeros tampoco garantizan exactamente20 µF: ±20% inicial y variación térmica/vida requieren ficha o medición para sostener el mínimo16 µF propuesto.

## 4. Inductores y resistencia de sensado

|Ref.|Función|Valor original|Requisito eléctrico|Requisito térmico|Margen recomendado|Candidato JLC|Estado|
|---|---|---|---|---|---|---|---|
|L1, L2|Almacenamiento de energía en serie|330 µH cada uno, Isat≥3 A por verificar|660 µH nominal; L efectiva total≥528 µH a temperatura/corriente; ≥1.5 A RMS normal; Isat≥3 A con definición documentada; DCR total≤0.20 Ω a 20 °C deseable|ΔT≤40 °C y cuerpo≤85 °C propuestos; núcleo+pérdidas cobre; no aprobar por Irated|3 A frente a corriente limitada propuesta2.5 A; comprobar L(I), no solo Isat|2×Murata60B334C, C6823957; XR6826TS331MHL65 C22447628 THT|SMD candidato identificado, ficha completa/stock/huella pendientes|
|L1+L2 → L_EQ, solo propuesta|Alternativa de una bobina|660 µH equivalentes|680 µH es+3.03%; no 660 exactos; mismas condiciones de corriente; DCR135 mΩ publicado|Temperatura y L(I) deben verificarse|Rizado disminuye2.94% si L real680; no supone aprobación del cambio|Murata60B684C; código JLC/LCSC exacto no confirmado|Alternativa técnica, sin autorización de cambio|
|RS1|Shunt antes del nodo de salida y de C4/C5|50 mΩ, 1%, 1 W|Mantener50 mΩ; ≥1 W útil a temperatura; ≤50 ppm/°C deseable; cuatro trazas Kelvin aunque componente sea dos terminales|P normal máx≈0.109 W; 0.316 W a 2.5 A; verificar derating/área cobre|≥2×P de ensayo después de derating; 2 W comercial no implica2 W en esta placa|RLP25FEER050 C160588; WSL2512R0500FEA C413486|Condicional; TA-I impone condiciones de cobre específicas|

**Corrientes y saturación.** En los casos obligatorios a 12 V ideal, el máximo estacionario es1.4773 A pico (6 V/4.8 Ω); en el caso combinado y tolerancias propuestos llega≈1.775 A. Saturación durante arranque/falla exige otro cálculo: con IL inicial en el disparo máximo2.184 A y retardo supuesto10 µs, ΔI≈VIN·td/Lmin=13.2×10 µs/528 µH=0.250 A. Resultado≈2.434 A; se redondea a **2.5 A como presupuesto de ensayo**, no como protección garantizada. Isat≥3 A solo sirve si la definición de caída y la curva L(I, T) mantienen el mínimo usado por el cálculo. Los retardos y la saturación están por medir.

**DCR.** Con DCR20=0.20 Ω y T=85 °C, R(T)=R20[1+0.00393(T−20)]≈0.251 Ω. Pcu=IL, RMS²·DCR:≈0.255 W nominal y≈0.542 W con 1.470 A RMS. Dos inductores iguales reparten≈0.271 W cada uno; para ΔT40 °C su resistencia térmica efectiva debería ser≤148 °C/W, antes de sumar pérdidas de núcleo. No se dispone de esa resistencia térmica ni de pérdidas de núcleo de XR: **bloqueo**, no cero vatios.

La guía oficial Murata6000B publica80 mΩ para 60B334C y 135 mΩ para 60B684C; dos 330 darían160 mΩ y un 680, 135 mΩ a la temperatura de referencia. Las pérdidas DC ideales a 1.470 A son0.346 W/0.292 W respectivamente, antes de calentamiento. La ficha completa no se recuperó de su URL oficial (404/acceso fallido); la [guía oficial de selección](https://www.murata.com/-/media/webrenewal/support/library/catalog/products/power-products/power-magnetics.ashx?cvid=20260202012717000000&la=en-gb) da valores de catálogo, no prueba la saturación. Sus corrientes de catálogo4 A/3 A **no se rebautizan como Isat garantizada**.

Se revisó además BournsSRR1260-331K: su [tabla oficial](https://www.bourns.com/pdfs/SRR1260.pdf), p.1, indica1.15 A RMS, Isat típico1.10 A y 580 mΩ. **Rechazado**, aunque tenga330 µH y sea SMD. El SRR1260-681K también es insuficiente (0.80 A RMS, Isat0.75 A típico).

Para dos bobinas Ltotal=L1+L2±2M; para iguales, Ltotal=660 µH·(1±k). Exigir |k|≤0.05 es una propuesta para limitar ese término a 5%; medir inductancia total en la disposición final. No sumar una caída20% por tolerancia y otra por saturación y seguir utilizando528 µH: el mínimo debe ser efectivo. Una bobina única elimina ese acoplamiento entre piezas, pero cambia volumen, radiación, DCR y el modelo. Faltan datos de núcleo (material, B, volumen, curvas a 10 kHz); no se calcula una pérdida ficticia con Steinmetz.

**Shunt.** Nominal P=(1²+0.4545²/12)×0.05=0.0509 W. En la envolvente P≈1.470²×0.0505=0.109 W. A2.5 A y Rmax50.5 mΩ: P=0.3156 W, V=0.1263 V. Una resistencia Kelvin parásita de 1 mΩ sobre50 mΩ introduce2% de error; objetivo propuesto≤0.25 mΩ equivalentes para≤0.5%. Con TCR50 ppm/°C y ΔT60 °C, cambio de R≤0.3%, que se añade al presupuesto de umbral, no se elimina con la tolerancia inicial.

El [datasheet TA-I RLP](https://www.tai.com.tw/files/uploads/Prod_spec/RLP.pdf), p.4 notas1–2, condiciona2/3 W en RLP25 a **300 mm² de pads/pistas y cobre mínimo105 µm**. No se ha confirmado ese cobre en el proyecto; no se acredita potencia2 W en una PCB de cobre distinto. El [WSL Vishay](https://www.vishay.com/docs/30100/wsl.pdf) es alternativa1 W, con TCR de componente±75 ppm/°C a 50 mΩ según p.2 del datasheet; recalcular deriva del umbral si se elige; no es un shunt de cuatro terminales.

## 5. Driver, bootstrap y compuerta

|Ref.|Función|Valor original|Requisito eléctrico|Requisito térmico|Margen recomendado|Candidato JLC|Estado|
|---|---|---|---|---|---|---|---|
|R1|Resistencia de compuerta|10 Ω|1%; ≥0.125 W en continua; preferir0.25–0.5 W antipulso; pico calculado1.33 A/17.6 W; comprobar pulso repetitivo|P media presupuesto≤13.2 mW, pero domina pulso; lejos del MOSFET caliente|No aprobar por potencia media; curva de pulso a duración real|0805W8F100JT5E C17415; ERJ-P6WF10R0V C4217693|Preliminar; curva pulso/EMI pendientes; ERJ-P6W no recomendado para diseños nuevos|
|R2|Descarga G-S, estado apagado|10 kΩ|1%; ≥0.1 W; soportar13.2 V continuos; su corriente debe entrar en Cboot|≤17.6 mW, antes de duty; comprobar derating|≥4× potencia a temperatura propuesta|0603WAF1002T5E C25804|Valor conservado; condiciona bootstrap|
|C6|Alimentación flotante VB−VS|1 µF/50 V X7R|Dimensionar por C efectiva, objetivo≥1.0 µF; ≥25 V, mantener 50 V preferido; baja ESR/ESL|X7R; mantener lejos de calor; fugas de C y D2 a Tmax|Q presupuesto0.260 µC; caída≤0.26 V con 1 µF efectivo|CL21B105KBFNNNE C28323; alternativa2×mismo MPN C6A/C6B|Una pieza1 µF nominal no demuestra1 µF efectiva; pendiente|
|C7|Desacoplo VCC−COM driver|100 nF/50 V|X7R rápido; añadir reserva local si la impedancia de VIN lo requiere; objetivo de reserva efectiva≥1 µF|≥50 V preferido; minimizar lazo y ESL|C7 solo puede caer varios voltios durante descarga bootstrap|C14663 + C18 propuesto C28323|C18 es propuesta, no incorporado|
|C8|Desacoplo lógico VDD−VSS driver|100 nF/50 V|X7R; objetivo C efectiva≥70 nF a 5.25 V; conexión junto a pines del SOIC correcto|−55 a 125 °C o mejor|50 V nominal conserva requisito previo|CC0603KRX7R9BB104 C14663|Preliminar|

El [IR2110](https://www.infineon.com/assets/row/public/documents/24/49/infineon-ir2110-datasheet-en.pdf), pp.2–3, exige condiciones recomendadas VCC/VBS10–20 V. UVLO positivo VBS puede llegar9.7 V; estar apenas por encima de UVLO **no sustituye cumplir VBS≥10 V ni obtener VGS suficiente**.

Presupuesto adicional para ton=95 µs (límite de duty del proyecto, no ensayo obligatorio):

\[
Q_{boot}=Q_g+Q_{ls}+[I_{QBS}+I_{LK}+I_{D2}+I_{R2}]t_{on}.
\]

Con Qg=100 nC supuesto, Qls=5 nC supuesto, IQBS=230 µA, ILK=50 µA, ID2=10 µA supuesto y IR2≤13.2/9.9 kΩ=1.333 mA:

Qboot=100+5+(0.230+0.050+0.010+1.333) mA×95 µs≈**259.2 nC**.

ΔVBS=Q/Ceff:0.259 V con 1 µF; 0.518 V con 0.5 µF. El cálculo histórico de≈90 nC omite R2 y usa el Qg del MOSFET original; no basta para aprobar C6. Las fugas de D2 a temperatura y el Qls real no están cerrados. La fórmula de carga es una aplicación propia del método de [Infineon, sizing de bootstrap](https://www.infineon.com/assets/row/public/documents/24/49/infineon-ir2x14ss-datasheet-en.pdf), §2.2; **no se trasladan sus parámetros de IR2114 al IR2110**.

Durante recirculación SW≈−VF(D1), VBS, carga≈VCC−VF(D2)+VF(D1). Si VCC=12 V, VF(D2)=0.9 V supuesto y VF(D1)=0.55 V, carga≈11.65 V; fin de pulso≈11.39 V con 1 µF efectivo. Al arrancar SW≈0 V, el valor inicial es menor. A VIN=10.8 V ese margen se vuelve estrecho; la caída HO y el rizado de VIN pueden impedir VGS≥10 V. La hoja UMW también caracteriza RDS a 4.5 V, pero eso no autoriza ignorar las condiciones del IR2110. **No se garantiza el margen del driver en toda la extensión10.8–13.2 V.**

En toff=5 µs, la recarga media debe ser al menos0.259 µC/5 µs=51.8 mA; en arranque la carga es del orden de 11 µC por 1 µF. La constante Rloop·Cboot y el diodo limitan el proceso. Para95% desde descargado:3RloopC≤5 µs implicaRloop≤1.67 Ω con 1 µF. Es una comprobación conservadora de recarga, no un requisito universal para cada ciclo. No aumentar arbitrariamente C6 sin revisar corriente inicial, D2 y el suministro local.

Para C18, ΔV≈Q/C:0.259 µC/100 nF=2.59 V si C7 tuviera que aportar sola esa carga; con 1 µF efectivo≈0.259 V. C1/C2 pueden aportar carga, pero su cableado introduce impedancia de alta frecuencia. Se propone añadir C18 de reserva junto al driver y validarlo con osciloscopio; no se atribuye un valor1 µF obligatorio al datasheet IR2110.

R1: Pmedia≤Qg·VGS·fs=100 nC×13.2 V×10 kHz=13.2 mW como presupuesto energético de carga/descarga, no I²R calculado con la corriente pico durante todo el periodo. Ipico≤13.2/9.9=1.333 A y Ppico≤17.6 W antes de resistencia del driver/MOSFET. Para Qgd típico15 nC y un plateau supuesto4 V: I≈(11−4)/10=0.7 A, tMiller≈21 ns sin impedancias internas. No se adopta ese tiempo como resultado real; medir tr/tf, ringing y energía de conmutación para cerrar R1/snubber.

## 6. Regulador y desacoplos de los IC

|Ref.|Función|Valor original|Requisito eléctrico|Requisito térmico|Margen recomendado|Candidato JLC|Estado|
|---|---|---|---|---|---|---|---|
|C9|Entrada regulador|330 nF/50 V|Conservar0.33 µF nominal X7R del circuito UMW; documentar C efectiva; si se exige≥0.33 µF efectiva, proponer 1 µF y validar|X7R−55 a 125 °C; proximidad IN-GND|50/13.2=3.79|CL21B334KBFNNNE C73142; alternativa C28323 de 1 µF|Recomendación fabricante, no mínimo absoluto demostrado|
|C10|Salida regulador rápida|100 nF/50 V|0.1 µF nominal del circuito UMW; verificar estabilidad con C11 y carga real|X7R; alejar de TO252 caliente|Mantener capacitancia y baja ESL|CC0603KRX7R9BB104 C14663|Preliminar; ESR admisible UMW no publicado|
|C11|Reserva5 V|10 µF/25 V|≥10 µF nominal; objetivo efectivo≥5 µF; tecnología/ESR condicionadas al U2 exacto|≥85 °C en MLCC, preferir125 °C si hay calor; comprobar sesgo|25/5.25=4.76; no usar ese cociente para deducir C efectiva|CL21A106KAYNNNE C15850 X5R|Pendiente estabilidad y capacitancia efectiva|
|C12|VCC-GND U3|100 nF|X7R100 nF nominal, 50 V; objetivo efectivo≥70 nF; conexión local|−55 a 125 °C|Reserva local adicional si cable lógico largo|C14663|Preliminar|
|C13|VCC-GND U4|100 nF|Igual desacoplo local; esencial durante cambios del latch|−55 a 125 °C|No compartir retorno de carga|C14663|Preliminar|
|C14|VCC-GND U5|100 nF|Desacoplo local; no confundir con filtro de entrada del comparador|−55 a 125 °C|Evaluar ruido/retardo sin añadir RC a ciegas|C14663|Preliminar|
|C16|VS-GND U6|100 nF|TI exige bypass de al menos0.1 µF; para mínimo efectivo conservador proponer 220 nF/50 V X7R|−55 a 125 °C|220 nF×0.9×0.85=168 nF antes de DC/edad; exigir retención restante≥60%|CC0603KRX7R9BB224 C107083|Cambio de valor propuesto, no aplicado|

El PDF UMW `C347278.pdf`, p.12 §9, ilustra CI=0.33 µF y CO=0.1 µF. No publica un intervalo de ESR para aprobar todas las combinaciones cerámicas; ensayar C10+C11 y transitorios de carga. C11 no tiene que ser automáticamente un electrolítico ni automáticamente un MLCC.

Térmica de U2: P≈(VIN−5)I5+VIN·IQ. Con 12 V, 100 mA eIQ máximo6 mA del PDF local: P≈0.700+0.072=**0.772 W**. A VIN13.2 V:≈0.899 W. El valor0.7 W histórico omite IQ. RθJC12.5 °C/W no es RθJA; para TA45 °C y TJ objetivo105 °C, RθJA efectiva tendría que ser≤60/0.899=66.7 °C/W. No está demostrada con TO252/cobre actual. A5mA mínimos de la tabla, confirmar también el consumo mínimo: no extrapolar regulación con placa sin MCU a corriente nula.

Para MLCC, Ceff=Cnom·factortolerancia·factorDC·factorT·factorenvejecimiento. Los factores deben provenir de curvas/condiciones del MPN o medirse; los gráficos típicos no son mínimos garantizados. La interpretación de 0.1 µF como mínimo **efectivo** para C16 es margen de ingeniería conservador; se separa de la recomendación nominal de circuito de TI. No se ha aprobado un capacitor220 nF sin verificar su curva.

## 7. Resistencias de interfaz, referencia y sensado

Todos los valores indicados se conservan salvo propuesta explícita R10A/R10B. Tolerancia mínima recomendada1%; resistencias de precisión/pares de divisor: preferir0.1% y≤25–50 ppm/°C si el presupuesto de medida lo exige. Los Basic1%/100 ppm/°C son candidatos económicos, no una garantía de exactitud de umbral. A ΔT60 °C, 100 ppm/°C implica0.6% por resistor; para una razón con TCR opuestos puede aproximarse1.2% antes de otras fuentes.

|Ref.|Función|Valor original|Requisito eléctrico|Requisito térmico|Margen recomendado|Candidato JLC|Estado|
|---|---|---|---|---|---|---|---|
|R3|PWM d′ por defecto alto|10 kΩ|1%; 5.25 V máx presupuesto; 1 µA de bias HCT considerado|0.1 W útil; carga normal≈2.3 mW máx|>30× potencia; controlar backpower del MCU|0603WAF1002T5E C25804|Valor conservado|
|R4|Serie MCU_PWM|1 kΩ|1%; verificar niveles con R3; presupuesto de falla5.25 V, 5.3 mA|P≤27.9 mW en falla; 0.1 W a T propuesta|>2× potencia después de derating|0603WAF1001T5E C21190|Pendiente secuencia MCU/5 V|
|R5, R6|Pull-down RUN/RESET|10 kΩ|1%; niveles MCU hasta 3.465 V supuestos; corriente≈0.35 mA|P≤1.22 mW cada uno; 0.1 W|Entradas no flotantes; asegurar estado antes de reset|C25804|Conservar; revisar arranque|
|R7|Pull-up NTRIP colector abierto|4.7 kΩ|1%; hasta 1.13 mA; VOL comparador compatible HCT|≤5.93 mW; 0.1 W|Carga muy inferior a 4 mA de ensayo LM393B|0603WAF4701T5E C23162|Conservar; medir transitorios|
|R8, R9|Referencia común de protecciones|15 kΩ/10 kΩ, 1%|Razón0.4; VREF=2 V nominal; TCR≤50 ppm/°C deseable|P≤0.680/0.457 mW; 0.1 W|Mejorar tolerancia no elimina error de U2|0603WAF1502T5E C22809 / C25804|Candidatos1%; precisión mejorable|
|R10, R11|Divisor OVP|31 kΩ/10 kΩ, 1%|Razón1/4.1; soportarVOUT hasta 13.2 V propuesto; TCR≤50 ppm/°C deseable|≤3.28/1.08 mW; 0.1 W|No cambiar31k por 31.6k ni30k sin redimensionar|R10 sin MPN exacto; alternativa30k+1k; R11 C25804|R10 bloqueado como pieza única|
|R12|Base Q2|10 kΩ|1%; Ibase≈(5−0.7)/10k=0.43 mA; máximo≈0.48 mA|≤2.28 mW; 0.1 W|Q2 hunde≈0.35 mA, beta forzada<1 nominal|C25804|Verificar saturación a corriente real|
|R13|Pull-up NFAULT_MCU a 3.3 V|10 kΩ|1%; corriente≤0.35 mA; no conectar a 5 V|≤1.22 mW; 0.1 W|VOL Q2 y VIH MCU medidos|C25804|Valor conservado|
|R14, R15|Divisor ADC de tensión|3 kΩ/1 kΩ, 1%|Razón0.25; Rth750 Ω; a 13.2 V/fallaVADC puede≈3.35 V con tolerancias|P presupuestada≤33.4/11.4 mW; 0.1 W a 85 °C con margen≥2|1% permite≈±1.5% en razón; 0.1% preferido si se requiere precisión sin calibrar|0603WAF3001T5E C4211 / C21190|Aprobar margen ADC y tolerancia; sin sustitución por 3.3k|
|C15|Filtro VREF|100 nF|X7R50 V; capacitancia/tolerancia compatibles con retardo de referencia|125 °C; bajo calentamiento|τ=0.60 ms; esperar≈3 ms tras establecer5 V|C14663|Conservar; validar arranque|
|C17|Filtro ADC|1 nF|C0G50 V±5% preferido; τ objetivo0.75 µs±aprox6%; no filtra mucho a 10 kHz|C0G estable; minimizar fugas/contaminación|Verificar adquisición ADC y fase de muestreo|0603CG102J500NT C1636|Preliminar; Extended por estabilidad|

### Potencias, tensiones y corrientes calculadas por resistencia

|Ref.|R nominal (Ω)|V nominal (V)|V máx presupuesto (V)|I máx (mA)|P nominal (mW)|P máx presupuesto (mW)|
|---|---|---|---|---|---|---|
|RS1|0.05|0.0500|0.1263|2500.000|50.861|315.625|
|R1|10|11.0000|13.2000|1333.333|5.500|13.200|
|R2|10000|11.0000|13.2000|1.333|12.100|17.600|
|R3|10000|4.5455|4.7813|0.483|2.066|2.309|
|R4|1000|0.4545|5.2500|5.303|0.207|27.841|
|R5|10000|3.3000|3.4650|0.350|1.089|1.213|
|R6|10000|3.3000|3.4650|0.350|1.089|1.213|
|R7|4700|5.0000|5.2500|1.128|5.319|5.924|
|R8|15000|3.0000|3.1751|0.214|0.600|0.679|
|R9|10000|2.0000|2.1253|0.215|0.400|0.456|
|R10|31000|4.5366|10.0289|0.327|0.664|3.277|
|R11|10000|1.4634|3.2684|0.330|0.214|1.079|
|R12|10000|4.3000|4.7500|0.480|1.849|2.279|
|R13|10000|3.3000|3.4650|0.350|1.089|1.213|
|R14|3000|4.5000|9.9493|3.350|6.750|33.329|
|R15|1000|1.5000|3.3497|3.384|2.250|11.334|


Los máximos conservadores de la tabla no son todos simultáneos: para resistencias comunes se usa Vmax²/Rmin, con Rmin=0.99R; R1 usa energía de gate y RS1 un presupuesto de corriente de falla. Se separa error térmico del de valor. Para Basic0603 de 0.1 W, usando como hipótesis de derating lineal entre 70 y 155 °C, Pdisponible(85)=0.0824 W; R14 queda por debajo de 41%, R4 por debajo de 34%. Confirmar esa curva para el MPN/lote real; no convertir la hipótesis en un dato de fabricante no recuperado.

### Umbrales y tolerancias

\[
V_{REF}=V_5\frac{R9}{R8+R9};\quad I_{trip}=\frac{(V_{REF}\pm V_{OS, cmp})/G\mp V_{OS, INA}}{R_S};\quad
V_{OVP}=(V_{REF}\pm V_{OS, cmp})(1+R10/R11).
\]

Con V5=5±5%, resistencias±1%, G=20±1%, offset INA±0.5 mV y comparador±5 mV (hipótesis conservadoras heredadas de `verify.py`): VREF=1.87725–2.12525 V; Itrip=**1.82545–2.18360 A**; OVP=**7.56128–8.86744 V**. No son cotas certificadas de toda temperatura. El LM393BIDR publica±4 mV a−40…85 °C y VS5–36 V; no se ha demostrado ese offset en 4.75 V. Se conserva±5 mV como supuesto, explicitando el hueco. Bias del comparador50 nA sobreRth≤7.56 kΩ agrega hasta 0.378 mV por entrada; TCR, bias y error de cobre no están incluidos en los intervalos anteriores.

Ejemplo térmico propio: resistencias1%+0.6% de TCR independiente por ΔT60 °C, shunt1%+0.3%, offsets INA0.56 mV ycmp5 mV dan aproximadamente Itrip1.806–2.207 A y OVP7.439–9.013 V (envolvente ilustrativa, no garantizada). La suma de temperatura reduce el margen frente a 1.775 A pico normal a solo decenas de miliamperios. No prometer ausencia de disparos transitorios sin medir y revisar tolerancias.

Para R10 se propone, si no se consigue31 kΩ exactos, **R10A=30 kΩ + R10B=1 kΩ en serie**, manteniendo suma31 kΩ y OVP nominal8.2 V. Es una pieza adicional y una modificación futura que requiere revisión; no se implementa. Una31.6 kΩ daría8.32 V (+1.46%), y 30 kΩ sola8.0 V (−2.44%); ninguna es equivalencia exacta.

### Interfaz PWM y filtros

Con MCU bajo0 V: VDPRIME=5×1k/(10k+1k)=0.4545 V. Con MCU alto3.3 V: VDPRIME=(3.3×10k+5×1k)/11k=3.4545 V. Verificar con límites VOL/VOH reales del MCU y umbrales Schmitt del HCT14; no sustituir HCT por HC a 5 V. La interfaz puede inyectar corriente si el MCU está apagado pero el pull-up5 V sigue activo: aproximadamente(5−0.3)/(10k+1k)=0.427 mA bajo una hipótesis de diodo clamp. No garantiza cumplimiento de STM32 exacto; confirmar ficha/pines/secuencia.

ADC: VADC=VOUT/4 →1.25/1.50/1.75 V para 5/6/7 V. Con 1% independiente, razón entre 990/(3030+990)=0.246269 y 1010/(2970+1010)=0.253769: error−1.493/+1.508%. A7 V se traduce en≈±0.106 V reconstruidos antes de errores ADC/VDDA; un objetivo±20 mV requiere calibración o mejores divisores/referencia. Rth=3k||1k=750 Ω;τ=750×1 nF=0.750 µs; fc≈212 kHz. A10 kHz la atenuación es≈0.9989: C17 no elimina el rizado10 kHz. Asentamiento a 0.5 LSB de 12 bits para un escalón de escala completa requiere≈ln8192·τ=6.76 µs por el RC externo; agregar la adquisición interna del STM32 y comprobar los intervalos de muestreo de 5 µs. Para20 muestras uniformes por periodo, el promedio puede reducir rizado periódico, pero su fase y aliasing necesitan validación real.

C15:τ=(15k||10k)×100 nF=0.600 ms; 5τ=3.0 ms. Una subida de 5 V dejaVREF temporalmente baja; RUN debe permanecer deshabilitado hasta estabilización y reset válido. No añadir un filtro grande en ISENSE/OVSENSE sin calcular el retardo de protección. U6 alimenta el comparador, no el ADC de tensión; la recomendación TI de RC en salida haciaADC no se impone automáticamente en ISENSE.

## 8. Elementos nuevos y decisiones pendientes

|Propuesta|Motivo|Cambio respecto a original|Estado|
|---|---|---|---|
|C6A/C6B, dos 1 µF/50 V X7R si una pieza no asegura Ceff|Reducir caída bootstrap incluyendoR2|Añade capacitor; objetivo Ceff combinado≥1 µF; revalidar recarga|No incorporado|
|C18, reserva VCC driver|C7 de 100 nF no demuestra baja impedancia de recarga|≥1 µF efectivo local; puede necesitar2.2–4.7 µF nominal según bias|Propuesta de ingeniería, no valor exigido por IR2110|
|C16 de 220 nF|Margen para bypass efectivo INA180|Cambia100 nF nominal; no afecta L/C del convertidor|Propuesta conservadora|
|R10A/R10B|Obtener31k sin cambiar umbral nominal|30k+1k en lugar de una 31k|Revisión de selección/layout futura|
|RC snubber o clamp de SW/G-S; resistorbootstrap|Solo si mediciones muestran ringing/sobrecarga|No se fijan valores sin energía, frecuencia y parásitos reales|No poblar/no aprobar todavía|
|Protección ADC/secuenciación lógica|ExtensiónVIN y alimentación parcial pueden violar rangos|Definir clamp/limitación o secuencia; calcular inyección|Bloqueo antes de ampliar envolvente|

La compensación es digital; ningún datasheet de estos IC exige una redRC analógica de compensación del Buck. CambiarL/C/ESR requiere volver a validar el modelo discreto/PI, no añadir una red inventada.

Banco de carga **externo**, fuera de la BOM de placa: 2×12 Ω/10 W en paralelo; 1.2 Ω/5 W con bypass para 7.2 Ω; rama2×12 Ω/5 W en serie para 4.8 Ω. A7 V/4.8 Ω se disipan10.208 W en total: cada 12 Ω del banco base, 4.083 W; cada 12 Ω de la rama24 Ω, 1.021 W. La1.2 Ω a 7 V/7.2 Ω disipa1.134 W. Conservar soportes, temperatura admisible y capacidadDC de interruptores; no sustituir por resistenciasSMD pequeñas.

## 9. Evidencia calculada y estado

Los cálculos reproducibles están aislados en `artifacts/passives_20261024/`; se ejecutaron con Python 3.12.14 y unidades SI. No hay MATLAB MCP expuesto en esta sesión; no se abrió una sesión MATLAB ni se simularon modelos. Comprobaciones algebraicas no equivalen a ERC/DRC ni a ensayo. Los cinco documentos permiten elegir piezas y preparar revisión, pero **ninguna selección de potencia, driver o huella queda aprobada para fabricar** hasta cerrar [open_issues.md](open_issues.md).

## 10. Presupuesto separado para sobretensión transitoria

La tabla de resistencias anterior limita el escenario de salida forzada a 13.2 V; **no cubre la transferencia de energía de L al retirar carga**. El ejemplo del [plan de pruebas](expected_behavior.md) da17.14 V sin pérdidas, con L660 µH/I2.5 A/C16 µF. No es un máximo físico: otra L, corriente o retardo cambia el resultado.

Para dimensionar provisionalmente la evaluación de pulsos se propone20 V en VOUT, sin aceptar operación continua a esa tensión. Con 1% de tolerancia, cotas conservadoras V²/Rmin: R14≈76.5 mW y R15≈26.0 mW; R10≈7.53 mW y R11≈2.47 mW. R14 de 0.1 W no conserva margen2× a 85 °C para ese presupuesto; buscar≥0.25 W con curva de pulso o demostrar duración/energía y un clamp adecuado. No se ha cerrado un MPN JLC para esa variante. A20 V, VADC puede alcanzar5.075 V: **bloqueo eléctrico del MCU incluso si el resistor sobrevive**. La tensión nominal35/50 V de C4/C5 ofrece reserva respecto a este ejemplo, pero no demuestra ausencia de picos.

## 11. Trazabilidad individual contra la BOM original

Se cotejaron las 35 referencias pasivas de`bom.csv` contra las definiciones de`tools/design.py`: coinciden referencias y valores. Esta comparación no demuestra paridad de conexiones con la PCB. Los nodos siguientes proceden de las definiciones estáticas; la exportación de netlist actual sigue pendiente. Los puntos de prueba y conectores no se cuentan como pasivos comprables.

|Ref. original|Valor literal de BOM|Nodos según definición (pad:nodo)|Función|Propuesta / estado|
|---|---|---|---|---|
|L1|330uH >=3A Isat VERIFY|1:SW; 2:LMID|Inductancia de potencia, SW–LMID|Conservar función/valor; candidato y validación pendientes|
|L2|330uH >=3A Isat VERIFY|1:LMID; 2:IP|Inductancia de potencia, LMID–IP|Conservar función/valor; candidato y validación pendientes|
|RS1|0.050R 1% 1W|1:IP; 2:VOUT|Shunt/Kelvin|Conservar función/valor; candidato y validación pendientes|
|C1|100uF 25V|1:VIN; 2:GND|Reserva entrada|Conservar función/valor; candidato y validación pendientes|
|C2|100uF 25V|1:VIN; 2:GND|Reserva entrada|Conservar función/valor; candidato y validación pendientes|
|C3|100nF 50V|1:VIN; 2:GND|Desacoplo VIN|Conservar función/valor; candidato y validación pendientes|
|C4|10uF 35V low ESR|1:VOUT; 2:GND|Filtro salida|Conservar función/valor; candidato y validación pendientes|
|C5|10uF 35V low ESR|1:VOUT; 2:GND|Filtro salida|Conservar función/valor; candidato y validación pendientes|
|C6|1uF 50V X7R|1:BOOT; 2:SW|Bootstrap VB–VS|C efectiva por cerrar; C6A/B solo propuesta|
|C7|100nF 50V|1:VIN; 2:GND|Bypass driver potencia|Conservar función/valor; candidato y validación pendientes|
|C8|100nF 50V|1:+5V; 2:GND|Bypass driver lógica|Conservar función/valor; candidato y validación pendientes|
|R1|10R|1:HO; 2:GATE|Gate serie|Conservar función/valor; candidato y validación pendientes|
|R2|10k|1:GATE; 2:SW|Descarga gate/bootstrap|Conservar función/valor; candidato y validación pendientes|
|C9|330nF 50V|1:VIN; 2:GND|Entrada regulador|Conservar función/valor; candidato y validación pendientes|
|C10|100nF 50V|1:+5V; 2:GND|Salida regulador|Conservar función/valor; candidato y validación pendientes|
|C11|10uF 25V|1:+5V; 2:GND|Reserva5 V|Conservar función/valor; candidato y validación pendientes|
|R3|10k|1:DPRIME; 2:+5V|Pull-up PWM invertido|Conservar función/valor; candidato y validación pendientes|
|R4|1k|1:MCU_PWM; 2:DPRIME|Interfaz PWM serie|Conservar función/valor; candidato y validación pendientes|
|C12|100nF|1:+5V; 2:GND|Bypass HCT14|Conservar función/valor; candidato y validación pendientes|
|C13|100nF|1:+5V; 2:GND|Bypass HCT00|Conservar función/valor; candidato y validación pendientes|
|R5|10k|1:RUN; 2:GND|Pull-down RUN|Conservar función/valor; candidato y validación pendientes|
|R6|10k|1:RESET; 2:GND|Pull-down RESET|Conservar función/valor; candidato y validación pendientes|
|R7|4.7k|1:NTRIP; 2:+5V|Pull-up comparador|Conservar función/valor; candidato y validación pendientes|
|C14|100nF|1:+5V; 2:GND|Bypass comparador|Conservar función/valor; candidato y validación pendientes|
|R8|15k 1%|1:+5V; 2:VREF|Referencia: resistencia superior|Conservar función/valor; candidato y validación pendientes|
|R9|10k 1%|1:VREF; 2:GND|Referencia: resistencia inferior|Conservar función/valor; candidato y validación pendientes|
|C15|100nF|1:VREF; 2:GND|Filtro referencia|Conservar función/valor; candidato y validación pendientes|
|R10|31k 1%|1:VOUT; 2:OVSENSE|OVP: resistencia superior|31 kΩ sin MPN único; R10A30k +R10B1k solo propuesta|
|R11|10k 1%|1:OVSENSE; 2:GND|OVP: resistencia inferior|Conservar función/valor; candidato y validación pendientes|
|C16|100nF|1:+5V; 2:GND|Bypass INA180|100 nF original; 220 nF propuesto con margen efectivo|
|R12|10k|1:FAULT; 2:FB|Base Q2|Conservar función/valor; candidato y validación pendientes|
|R13|10k|1:+3V3; 2:NFAULT_MCU|Pull-up estado hacia MCU|Conservar función/valor; candidato y validación pendientes|
|R14|3k 1%|1:VOUT; 2:VSENSE|ADC: resistencia superior|Revisar pulso20 V/ADC y posible≥0.25 W; pendiente|
|R15|1k 1%|1:VSENSE; 2:GND|ADC: resistencia inferior|Conservar función/valor; candidato y validación pendientes|
|C17|1nF|1:VSENSE; 2:GND|Filtro ADC|Conservar función/valor; candidato y validación pendientes|
