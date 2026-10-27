# Validación documental del bootstrap: C6 2.2µF

**Candidato implementado; bootstrap NO aprobado.** No hay medición ni simulación transitoria nueva. Unidades: V, A, s, F, C. VIN ampliado 10.8–13.2V y duty95% son presupuestos, no límites garantizados del montaje. La guía docente mantiene12V/10kHz; este estudio no cambia L ni COUT.

## Selección y CAD

C6: Samsung **CL31B225KBHNNNE**, **C50254**, Basic. [Fabricante](https://product.samsungsem.com/mlcc/CL31B225KBHNNN.do), [datos del componente](https://weblib.samsungsem.com/mlcc/mlcc-ec-data-sheet.do?partNumber=CL31B225KBHNNN), [JLCPCB](https://jlcpcb.com/partdetail/C50254). Nominal2.2µF/50V/X7R/±10%; cuerpo1206, L3.20±0.20mm, W/T1.60±0.20mm. Basic es clasificación comercial consultada, no calificación eléctrica ni promesa de stock.

Se conserva símbolo no polar Buck:C6. Huella local `Capacitor_SMD:C_1206_3216Metric`: pads1/2, centros x=±1.475mm, pads1.15×1.80mm; gap1.80mm. Compatible con el formato y cuerpo; el land genérico IPC no sustituye aprobación de terminaciones, tolerancias y soldadura Samsung. Modelo3D local accesible, orientación mecánica pendiente. Conectividad conservada: **C6.1=BOOT=U1.7/VB; C6.2=SW=U1.6/VS**. No son VB-GND.

## Capacitancia efectiva

La biblioteca Samsung dice explícitamente “Graphs for the item are not supported”. No se recuperó curva DC bias del MPN ni mínimo combinado garantizado DC/T/edad. No se inventa una curva. El enlace LCSC antiguo devolvió HTML, conservado como HTML en artifacts; no se presenta como datasheet PDF.

Modelo de sensibilidad propio: `Ceff=2.2µF×0.9×0.85×β=1.683µF×β`; β representa conjuntamente retención DC/edad desconocida. El0.85 representa X7R−15% y se multiplica conservadoramente con tolerancia; los efectos reales no necesariamente son separables. A25°C y0V, solo tolerancia da1.98µF. Los β siguientes son HIPÓTESIS de ensayo, no valores Samsung.

| β supuesto | Ceff µF | ΔV95% V | VBS min VCC10.8/VF0.9/VS0 | VBS min VCC12/VF0.9/VS0 |
| --- | --- | --- | --- | --- |
| 1 | 1.6830 | 0.1540 | 9.7460 | 10.9460 |
| 0.75 | 1.2623 | 0.2054 | 9.6946 | 10.8946 |
| 0.5 | 0.8415 | 0.3080 | 9.5920 | 10.7920 |
| 0.25 | 0.4208 | 0.6161 | 9.2839 | 10.4839 |

No se confirma Ceff≥1µF: exigiría β≥0.5942 con esa envolvente. Se necesita curva de entrega del fabricante o medida de muestras con polarización10–13V, temperatura de aplicación y envejecimiento; medir también impedancia/frecuencia, sin confundir corriente nominal de50V con retención de C.

## Presupuesto de carga

`Q=Qg+Qls+(IQBS+Iextra+VGS/R2min)×ton`; Ts=100µs. R2=10k±1%: Rmin9.9k, presupuesto VGS13.2V →1.333mA. Driver IR2110: IQBSmax230µA y fuga offset50µA en las condiciones de su ficha. [Infineon rev.V, pp.2–3](https://www.infineon.com/assets/row/public/documents/24/49/infineon-ir2110-datasheet-en.pdf). D2 aporta10µA SUPUESTOS; su pieza SMD exacta sigue bloqueada. No se atribuye esa fuga o VF a ShunYe sin ficha.

Q1 sigue siendo el original IRFZ44N/TO-220, con candidato UMW NS pendiente. La copia UMW indica Qg típico50nC en su punto de ensayo; aquí se usa **100nC como presupuesto**, sin convertirlo en máximo garantizado de la pieza instalada. Qls5nC también supuesto. No se incluyen garantías de Qrr/D2, capacitancias parásitas o gate caliente. R1 y la impedancia del driver fijan picos/dinámica, no los determina únicamente C6. Ihold calculada=1.62333mA; Q95%=259.217nC.

| d físico | ON µs | OFF µs | Q nC | ΔV con2.2µF V | ΔV con0.8415µF V | Recarga media mínima mA |
| --- | --- | --- | --- | --- | --- | --- |
| 0.05 | 5.0 | 95.0 | 113.117 | 0.0514 | 0.1344 | 1.481 |
| 0.4 | 40.0 | 60.0 | 169.933 | 0.0772 | 0.2019 | 3.122 |
| 0.5 | 50.0 | 50.0 | 186.167 | 0.0846 | 0.2212 | 4.013 |
| 0.6 | 60.0 | 40.0 | 202.400 | 0.0920 | 0.2405 | 5.350 |
| 0.65 | 65.0 | 35.0 | 210.517 | 0.0957 | 0.2502 | 6.305 |
| 0.95 | 95.0 | 5.0 | 259.217 | 0.1178 | 0.3080 | 52.133 |

d=.4/.5/.6 corresponde a escalones previstos; .65 aproxima7V/10.8V ideal; .05/.95 son extremos de saturación del PI existente. **d′=1−d** es la señal PWM del MCU antes de HCT14. Reducir el rango operativo puede ayudar a recarga, pero no modifica el firmware/control original ni elimina el problema de VBS bajo.

## Techo de carga y alimentación mínima

`Vceiling≈VCC−VF_D2−VS_off−Icharge×Rpath`; `VBS_min≈Vceiling−Q/Ceff`. Con VCC10.8V, VF0.9V SUPUESTA, VSoff0V y Rpath0, el techo es **9.9V incluso con C infinita**. IR2110 recomienda VBS10–20V. Por tanto, este contraejemplo incumple el rango recomendado; UVLO inferior no lo aprueba. Para β=.5, pérdida mínima95%≈0.308V y VBS≈9.592V antes de pérdidas de recarga.

Si D1 mantiene SW a−0.5V, aparece0.5V de ayuda, pero depende de conducción continua, corriente, temperatura y tiempos; no se garantiza en arranque/DCM/carga abierta. Evaluar también VSoffpositivo y sobretensiones negativas. Condición necesaria ideal: `VCC≥10+VF_D2+VSoff+ΔV`, más caída resistiva y margen de recarga. Aumentar C6 no corrige por sí solo un techo inferior a10V.

## Recarga finita y carga inicial

Modelo RC ilustrativo, solo con VS fijado bajo: `α=exp(−toff/(Rpath×Ceff))`; caída mínima periódica `ΔVmin=(Q/Ceff)/(1−α)`. Ignora no linealidad del diodo, inductancias y demanda instantánea; no es simulación validada. Rpath no está medido; no se insertaron resistencias nuevas.

| Rpath supuesto Ω | Ceff µF | τ µs | Caída periódica95% V | Arranque hasta10V desde0, techo11.1V: µs |
| --- | --- | --- | --- | --- |
| 1 | 2.2000 | 2.200 | 0.131 | 5.086 |
| 1 | 0.8415 | 0.842 | 0.309 | 1.945 |
| 5 | 2.2000 | 11.000 | 0.323 | 25.428 |
| 5 | 0.8415 | 4.207 | 0.443 | 9.726 |
| 10 | 2.2000 | 22.000 | 0.580 | 50.856 |
| 10 | 0.8415 | 8.415 | 0.688 | 19.452 |
| 25 | 2.2000 | 55.000 | 1.356 | 127.140 |
| 25 | 0.8415 | 21.038 | 1.456 | 48.631 |

A95%, recuperar≈0.259µC en5µs demanda≈52.13mA medios durante OFF, además de picos iniciales. Una constante RC corta y trayectoria real de retorno son necesarias; en el límite de C grande persiste aproximadamente `Q×Rpath/toff`. Más C reduce caída instantánea y aumenta carga inicial.

Desde VBS=0, Qinitial nominal=24.42µC para11.1V y27.06µC para12.3V; la corriente de irrupción depende de la trayectoria. El tiempo RC hasta10V solo existe si el techo supera10V; al techo9.9V es imposible. El Buck asíncrono **no tiene MOSFET low-side controlado** para forzar SW aGND. El retorno inicial pasa por L1/L2 y carga/COUT: L660µH y C6 nominal dan f0≈4.18kHz como indicador de que una aproximación RC sola es insuficiente. Con VOUT precargado6V y SW≈6V, techo nominal≈12−0.9−6=5.1V: arranque potencialmente bloqueado por UVLO. No se garantiza recuperación por emitir PWM.

Condiciones iniciales para ensayo: C6=0V/COUT=0V y COUT precargado5/7V; fuente limitada, RUNinactivo y sonda diferencial VB−VS. Ensayar arranque, brownout10.8V, cambios .4/.6, límite95%, carga mínima/abierta, recuperación de fallas, R2 presente y Q1 real. Registrar VBS/VGS mínimos/máximos, corriente D2, tiempo OFF efectivo y temperatura. No se ejecutó este ensayo ni se seleccionó solver temporal; los resultados anteriores son cálculos algebraicos y sensibilidad.

**Bloqueo antes de layout liberado:** garantizar alimentación/recarga y Ceff, cerrar D2/Q1, definir duty admisible y arranque con salida precargada. No se añadió C18 ni un circuito auxiliar de carga sin decisión de diseño.
