# Comportamiento esperado y plan de comprobación

Fecha: 2026-10-24. **Estado: cálculos y revisión documental; ensayos físicos pendientes.** No se reejecutó la simulación de la revisión THT ni se validó una nueva revisión SMD. Requisitos de pasivos y escenarios numéricos: [passives_requirements.md](passives_requirements.md).

## Qué se exige y qué se propone

La guía del curso, `classroom/Descripcion Proyecto Buck.pdf` §§3.1–3.4, exige los escalones de duty complementario, referencia y carga. No fija límites de rizado, eficiencia, temperatura, sobreimpulso o tiempo de establecimiento para este rediseño. En las tablas, **C**=escenario del curso, **D**=condición documental del fabricante, **P**=criterio de ingeniería propuesto que requiere aceptación del equipo. **H**=resultado histórico, no una prueba ejecutada ahora.

Nominal:12 V, 10 kHz, 660 µH, 20 µF, 6 Ω, 6 V, d′=0.5. Casos obligatorios independientes: d′0.5→0.4 y 0.5→0.6; 6→5 V y 6→7 V; 6→4.8 Ω y 6→7.2 Ω a referencia6 V. Volver al punto nominal antes de cada ensayo. El caso7 V/4.8 Ω simultáneo y VIN10.8–13.2 V son extensionesP, no obligaciones de la guía. Si sus márgenes de bootstrap o protección no se cierran, limitar ensayo al punto12 V establecido.

## Etapa de potencia

|Criterio|Resultado esperado / intervalo|Fundamento|Método de comprobación|Estado|
|---|---|---|---|---|
|C: polaridad de control|Aumentar d′ reduce salida; D=1−d′|InversorHCT14 y HO en fase con HIN|Captura simultánea d′/HIN/VGS/SW/VO|Definición lógica revisada; físico pendiente|
|C: relación estacionaria ideal|d′0.4/0.5/0.6 →7.2/6.0/4.8 V a 12 V|VO=D·VIN; no incluye pérdidas|Medir medias tras estabilizar y registrarVIN real|Calculado; no exigir estos valores exactos a circuito con pérdidas|
|P: predicción con pérdidas|Ejemplo algebraico d′0.4/0.5/0.6 →6.630/5.441/4.250 V aproximadamente, con parámetros supuestos del informe|Balance de voltios-segundo ycaídas|Recalcular con DCR, VF, RDS medidos; comparar error e incertidumbre|Estimación algebraica calculada; parámetros físicos pendientes|
|C/P: corriente|Nominal ILmedia1 A,ΔIL0.4545 A pp, pico1.2273 A; obligatorio máximo estacionario1.4773 A ideal|Tabla del documento principal|Sonda de corriente; considerar corriente de COUT yno solo carga|Calculado, medición pendiente|
|P: conducción continua|Valle>0 A; casos obligatorios ideales mínimo≈0.582 A|ILmin=IO−ΔIL/2|Corriente de inductor con resolución del rizado|CCM estacionario calculado; arranque/ligera carga pueden serDCM|
|P: rizado de salida|Nominal ≈0.284 V pp capacitivo; cota≈0.352 V con ESR0.15 Ω; objetivo≤0.65 V pp en envolvente propuesta, banda20 MHz|L/C/fs y ESR; tolerancias y estimación con pérdidas|Sonda con lazo mínimo en C4/C5, sin promediado que oculte rizado; separar spikes|Propuesto; no equivale a 20 mV de error medio|
|P: rizado de entrada|≤0.40 V pp en C1/C2 para envolvente dimensionada|CIN≥160 µF y ESR banco≤0.10 Ω, más dinámica de fuente|MedirVIN junto a Q1 yjunto a CIN; registrar cable/fuente|Propuesto; impedancia fuente pendiente|
|P: bobinas|L efectiva total≥528 µH a corriente/temperatura deuso; DCR20 total≤0.20 Ω objetivo|Presupuesto de rizado y pérdidas|LCR, método de L bajoDC, resistencia4hilos; ensayo montadas|MPN ycurvas pendientes|
|P: temperatura|BobinasΔT≤40 °C ycuerpo≤85 °C; capacitoresΔT por rizado≤10 °C; mantenerse bajo límites de fabricante; resistor≤50% potencia útil normal|Márgenes propuestos; derating individual|Termopares/IR conemisividad documentada, TA25/45 °C, hasta equilibrio|Pendiente; ningún cálculo garantiza temperatura|
|P: eficiencia|Modelo algebraico etapa≈88–92%; objetivo inicial medir≥85% a 6 V y 6/4.8 Ω, pendiente presupuesto de núcleo/switching|Pout/(Pout+ΣP); hipótesis de RDS/DCR/tr/tf|Potencia simultáneaVIN/IIN y VO/IO; excluir/incluir electrónica claramente|Estimado, sin validación ni garantía de≥85%|
|P: eficiencia global|Separar cargaBuck de consumo5 V; un ejemplo100 mA a 5 V añade≈1.272 W de entrada, incluyendoIQ máximo supuesto de U2|VIN·I5+VIN·IQ|MedirI5 yconsumo decontrol; consignar qué cuenta como potencia útil|Pendiente; no presentar eficiencia deetapa como global|

La condición de aceptación del rizado presuponeC efectiva y ESR elegidas. Si20 µF no permiten el rizado que finalmente se quiera exigir, acordar otro objetivo o una modificaciónL/C/fs yrevalidar el control. No cambiar20 µF silenciosamente.

## Driver y conmutación

|Criterio|Resultado esperado / intervalo|Fundamento|Método de comprobación|Estado|
|---|---|---|---|---|
|D: alimentaciones|U1 VCC y VBS dentro10–20 V recomendados; VDD coherente con 5 V; HCT entre 4.5–5.5 V|Datasheets identificados en cumplimiento|MedirVCC-COM, VDD-VSS y VB-VS durante arranque/carga|Pendiente; VIN10.8 V no aprobado para toda condición|
|P/D: nivel gate|ObjetivoVGS alto≥10 V en pulso útil ybajo≤0.5 V; sin exceder±20 V de Q1 ni límitesU1|Objetivo usa puntoRDS10 V; VGS(th) no es conducción plena|Sonda diferencialG-S; medir sobreimpulsos yfin de pulso|Propuesto; no garantizado por UVLO|
|P: tiempos de conmutación|tr+tf≤0.5 µs como objetivo inicial, revisar pérdidas/EMI; presupuesto usado en cálculo200 ns|R1, Qg, impedancia driver; IR2110 medido por fabricante aotras condiciones|Medir10–90% VGS/VDS y energía∫VDS·IDdt si hay sondas adecuadas|Sin medida; datos típicos no son límite de este montaje|
|P/D: bootstrap|C6 efectiva objetivo≥1 µF; caída calculada≤0.260 V/pulso95 µs; VBS mínimo≥10 V ytambiénVGS suficiente|CargaQg, reposo, fugas y R2; límitesU1|CapturarVB−VS a D0.4/0.5/0.6 y, solo tras aprobar, 0.95; comprobar cada ciclo|Pendiente, cálculo histórico insuficiente|
|P: recarga|toff≥5 µs a D0.95; capacidad de reponer al menos0.260 µC por periodo según presupuesto; no caída acumulativa|Qboot/toff≈52 mA promedio duranteoff|Medir corrienteD2 ocaída/VBS y tiempo estable; validar arranque|D2 y Rloop sin cerrar|
|P: arranque/apagado|No encendido no comandado al establecerVIN/5 V; RUN bajo durante estabilización; pulsoRESET solo cuando la falla esté ausente|Latch asincrónico ytransitorios de VREF/U1|Fuente limitada; capturarVIN, 5 V, RUN, SD, VGS desde 0 V|Crítico pendiente; lógica fuera derango no tiene salida garantizada|
|P: MCU desconectado|Con ambos rieles válidos, RUN=0 por R5 y PWMd′ alto por R3:driver apagado|NAND y Schmitt conpulls|Retirar cable completo sin energía, reenergizar yconfirmar; probarPWM ausente con RUN alto porseparado|Razonamiento estático; ensayo pendiente|
|P: MCU detenido/PWM fijo|PWMalto →HINbajo; PWMbajo continuo no debe considerarse funcionamiento válido; pérdida debootstrap no es seguridad certificada|D=1 no tiene recarga normal; vigilanciaMCU yprotección independientes|Forzar fallos controlados conlimitación, sin cortocircuitar la placa|Pendiente; no garantizar apagado solo porausencia de flancos|

No conectar la masa de un osciloscopio referido a tierra al nodoSW. Usar medición diferencial o método adecuado conmasas en GND ylímites de instrumentación respetados. El tab de Q1 esVIN y el de U2 esGND según sus respectivas fichas; verificar variantes compradas.

## Protección

|Criterio|Resultado esperado / intervalo|Fundamento|Método de comprobación|Estado|
|---|---|---|---|---|
|C/P: corriente de disparo|Nominal2 A deinductor; intervalo estático heredado1.825–2.184 A; con TCR/bias no es cota final|G20×RS0.05=1 V/A y VREF2 V; ecuación por esquinas|Inyectar diferencial pequeño controlado o carga breve según protocolo; medir corriente real|Pendiente; no confundir umbral conlímite pico garantizado|
|C/P: OVP|Nominal8.2 V; intervalo heredado7.561–8.867 V, más términos pendientes|R10/R11 y VREF compartida|RUN bajo, carga retirada, fuente aislada limitada en VOUT; comprobar retornos|Pendiente; no aplicar un valor sobre límitesADC sin protegerlo|
|P: retardo OCP|Objetivo deingeniería≤10 µs desde cruce de umbral real hasta VGSbajo; corriente posterior objetivo≤2.5 A enensayo definido|INA350 kHz típico, comparador≈1 µs típico, NAND+SD; márgenes pendientes|Captura corriente/ISENSE/NTRIP/SD/VGS; varios valores de overdrive ytemperaturas|No es un máximo garantizado pordatasheets; bloqueo si no se cumple|
|P: retardo OVP|Objetivo≤10 µs desde cruce real a apagado; sin asumir descarga instantánea|Comparador+latch+driver; RCdelVREF no filtra señalOVP|CapturaVOUT, OVSENSE, NTRIP, SD, VGS|Pendiente|
|P: latch|NTRIPbajo activaFAULT; permanece al recuperarseNTRIP; RESET no borra causa persistente|EcuacionesNAND de`design.py`|Inyección lógica encircuito, todas las combinaciones; repetir tras brownout|Tabla lógica histórica existente; hardwareSMD sinprobar|
|P: reinicio|RUNbajo fuerzaSDalto; estabilizar5 V/VREF, comprobar NTRIPalto, pulsar RESET, rehabilitar RUN|Estado deinicio del latch no se supone conocido; 5τVREF≈3 msnominal|Captura desdearranque yfallarepetida|Pendiente; tiempo final incluir regulador y MCU|
|P: inmunidad a disparos espurios|No disparo en los seis escalones obligatorios a 12 V; ILpico y VOpico debajo del menor umbral caracterizado, conincertidumbre|Margen estático ilustrativo pequeño para 7 V/4.8 Ω|Capturar picos, no solo medias; ensayar tolerancias de muestras/T|No demostrado; escenario combinado más limitante|
|P: falla persistente|Reset no rehabilitaMOSFET mientrasNTRIPbajo; desligarRUN antes deensayo|Latch prioritario a falla|Sobrecarga controlada con fuente limitada; no corto franco|Pendiente|
|P: límites del sistema|No protege por sísolo contraQ1cortocircuitado, entrada invertida, energía de C/L, todos los fallos MCU o cable parcial|Topología Buck asincrónica ycamino dediodo|Análisis de falla yensayos aprobados conlimitación; fusible externo2 A yfuente limitada|Requiere medidas adicionales si se necesita cobertura|

**Energía después de apagar.** DeshabilitarQ1 no absorbe la energía de L. Como cota lossless conservadora sin carga:

\[
V_{final}=\sqrt{V_0^2+LI_0^2/C}.
\]

Con V0=6 V, L660 µH, I0=2.5 A, C16 µF: Vfinal≈**17.14 V**. No es una simulación del evento ni un pronóstico de pico real, pero demuestra queOVP8.2 V **no garantiza** VOUT<8.2 V después del apagado. Las pérdidas y la carga lo reducen; su mínimo durante una desconexión no está demostrado. Exige revisarADC, carga, capacitores y eventual clamp/supresión. Con 12 V y 200 µF, CIN almacena14.4 mJ; el fusible no impide la descarga inicial de ese banco.

## Control y sensado

|Criterio|Resultado esperado / intervalo|Fundamento|Método de comprobación|Estado|
|---|---|---|---|---|
|D/P: niveles|MCU3.3 V, HCT5 V; VDPRIME≈0.455 V bajo/3.455 V alto nominal; medir extremosVOH/VOL|R3/R4 yumbralesSchmitt, no lógicaHC|Capturar ambos lados de R4; fichaSTM32 exacto|Pendiente a extremos y alimentación parcial|
|P: ADCtensión|1.25/1.50/1.75 V para 5/6/7 V; códigos aproximados1551/1861/2172 con Vref3.3 V y 12bits|VO/4×4095/3.3|DMM+ADC, calibración de dos puntos, VDDA real|Nominal calculado; sin calibración ±1.5% del divisor másADC/VDDA|
|P: rangos de fallaADC|Nunca exceder rango analógico niinyección permitidos del STM32 exacto|Divisor1/4 a 13.2 V puede llegar3.35 V; energíaLpuede subir más|Revisar fichaSTM32F103 exacto/clon y simular/medir clamp confuente limitada|CRÍTICO pendiente; no realizar ensayoOVP externo sinrevisarlo|
|P: corriente sensada|ISENSE≈1 V/A; 1 A→1 V; 2 A→2 V|INA180A1×50 mΩ; precisión depende de offset/ganancia/cobre|Carga/sensor externo yvoltímetro TP6; comprobar Kelvin|Pendiente; no suponer±1% total|
|P: filtros|C17:τ0.75 µs, fc212 kHz; C15:τ0.60 ms|Resistencias Thevenin; los nodos tienen funciones distintas|Inyección de escalón pequeño, captura ymedición de capacitancias|Calculado; no introducir retardoOCP arbitrario|
|C/P: seguimiento|Alcanzar5/6/7 V en media de periodo; objetivo inicialerror≤20 mV tras calibración yestablecimiento≤10 ms; permanecer sin disparo|C exige seguimiento; números sonP y referencia histórica|Promediar periodosPWM completos; registrar transitorios y señal cruda|Propuesto, no obtenido en hardware|
|P: picos de salida|Vo instantánea inferior al menor umbralOVP caracterizado menos incertidumbre; no aplicar automáticamente5% sobreimpulso si invademargen|Rizado ytransitorio comparten presupuestoOVP|Osciloscopio, tabla de umbrales medidos ybandas|Pendiente; imposible deducirlo deerror medio|

No se equipara promedio de periodo conrizado: un error medio20 mV puede coexistir con 0.35 V pp. Tampoco es correcto exigir20 mV sincalibración conresistencias1% y VDDA no medida. Respuesta5→6/7 V depende deganancias y L/Cefectivos; cambiarESR puede cambiar amortiguamiento aun sin cambiarvalores nominales.

## Resultados históricos disponibles, sin reejecución

Fuente:`project/pcb/release/simulation/results.json` y`simulation/simulate.c`. Modelo con L660 µH, C20 µF, DCR0.20 Ω, shunt0.05 Ω, RDS0.022 Ω, VF0.45 V, ESR0.15 Ω; IL(0)=0 A, VC(0)=0 V; Euler0.5 µs contrastado0.25 µs yflancos fraccionarios. El CSV exporta mediasde periodo; evento a 0.010 s en el eje relativo del registro. No modela bien núcleo, saturación, bootstrap, recuperación ni dinámica completa de MOSFET.

|CasoH|Resultado archivado|Qué no demuestra|
|---|---|---|
|d′0.6|4.339596 Vfinal|No valida nuevoDCR/VF/MPN|
|d′0.4|6.721912 Vfinal|No es7.2 Vsin pérdidas|
|Referencia7 V|6.999636 Vfinal; establecimiento≈4.3 ms|No validaADC, bootstrap niPicoSMD|
|Referencia5 V|5.000988 Vfinal;≈4.3 ms|No acredita absorción de energía|
|Carga7.2 Ω|5.999747 Vfinal;≈0.8 ms|No valida rebote/temperatura|
|Carga4.8 Ω|6.000176 Vfinal;≈0.9 ms; máximo IL histórico1.549272 A|No cubre7 V/4.8 Ωsimultáneos|
|Convergencia|Diferencia máxima1.344655 mV en mediasde periodo|No escomparación contra medición física|

## Secuencia y evidencia mínima de ensayos

1. Aprobar MPN, documentos, polaridad, continuidad yhuellas antes deenergizar. MedirRLC/ESR/DCR yregistrarincertidumbre.
2. Prototipo soldado compacto; fuente limitada; sin MCU comprobar 5 V/RUN/SD/VGS. Revisararranque, latch ybootstrap antes decarga plena.
3. Caracterizar OCP/OVP coninyección controlada, ADC protegido yretornos comprobados. No usar cortocircuito franco. Mantener fusible externo2 A prescrito; no sustituye limitación de ensayo.
4. Calibrar sensado; estabilizar nominal; ejecutar los seis escalones por separado, tres repeticiones según procedimiento actual del proyecto (no requisito explícito del curso).Registrar VIN, VO, IL, VBS, VGS, SD ytemperaturas.
5. Autorizar por separado envolvente ampliada yfallas. Para escalones partir del régimen estable; para arranque partir de IL≈0 A y VO≈0 V, comprobando descarga previa. No confundircondiciones iniciales.
6. Medir rizado conancho de banda ymuestreo documentados; 200 kS/s puede servir para 10 kHz, pero para flancos/ringing usar osciloscopio/resolución muy superiores. Registrar sondas, diferencial, duración, puntos de medida y TA.
7. Repetir simulación aislada con parámetros definitivos, y convergencia temporal, antes de pasar a layout. Si se ajustaPI, preservarresultados anteriores yjustificar. Ninguna prueba numérica sustituye ensayo térmico.
