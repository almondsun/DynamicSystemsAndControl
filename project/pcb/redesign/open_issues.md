# Bloqueos abiertos antes de layout Buck SMD

> **Actualización Rev B (2026-10-27):** el layout, la interfaz entre dominios (U7–U10, D3–D5), el sensado Kelvin, los lands del fabricante y el paquete JLCPCB están en [revB_release_report.md](revB_release_report.md). Cerrados en CAD/cálculo: interfaz ADC/PWM/RUN/RESET, lands de L1/L2/Q1/D2/J1–J3, courtyard de U5, vías de HO. L1+L2 (2 × 60B334C, sin stock JLCPCB/LCSC) se sustituyeron por una sola Murata 60B684C de 680 µH (+3 % frente a 660 µH), comprada aparte y soldada a mano (reflujo máx. 245 °C frente a 255 ± 5 °C de Economic PCBA). Siguen abiertos: revisión del visualizador JLCPCB, compilación ARM y toda la validación física (bootstrap, ADC, protecciones, térmica). La tabla siguiente es el estado previo a Rev B.

Estado tras revisión NUCLEO: **NO LIBERAR para potencia o fabricación**. Existe esquemático exportable y firmware compilado de revisión; no existe validación física. Una fase posterior puede definir reglas preliminares, sin convertir estos pendientes en aprobaciones.

|Prioridad|Elemento|Bloqueo|Criterio de cierre|
|---|---|---|---|
|P0|BootstrapC6/U1/D2/R2/Q1|C6 aumentada no garantizaVBS≥10V; techo9.9V en el contraejemplo al mínimo; Ceff desconocida; recarga y arranque con salida precargada noverificados|Ceffgarantizada/medida yVBS/VGS/ID2 en10.8–13.2V, duty/arranque/brownout; cerrarD2/Q1|
|P0|ADCVSENSE|Divisor15k/2.2k no protege ante VOUT sin límite, negativos o apagado;24 V puede saturar con VREF bajo|Definir límites de energía y tiempo, y seleccionar aislamiento o clamp validado; comprobar inyección positiva de 0 mA y error|
|P0|Alimentación por señales|USBindependiente no evita5VdeR3/R4enMCU apagado niNUCLEO encendida/Buck apagado|Circuito y garantías de aislamiento, estados seguros y prueba de cada secuencia; no conectar potencia como está|
|P0|Puentes NUCLEO|SB17, SB18 y revisión física no inspeccionados|SB17 abierto para A0, SB18 abierto para PB7 independiente; registrar continuidad y revisión de placa|
|P1|L1/L2Murata|Land 60B334C no acreditado; huella THT histórica no aplicable;L(I,T)/pérdidas/acoplamiento|Land dimensional y volumen real yLtotal≥528µH conI/T, térmica y ensayos|
|P1|Q1/D2|Q1: familia UMW/TO-263 no resuelta;D2: descarga US1G contiene CLD incompatible|MPN, datasheet y encapsulado unívocos, y simulación o ensayo relevante|
|P1|RS1|2512 provisional no igual al land TA-I; cobre 1 oz no acredita 2 W|Land Kelvin, cobre, derating y temperatura con corriente normal y falla|
|P1|C1/C2/C4/C5|C efectiva/ESR10kHz/vida ypolaridad/landE7/C6|Medida/documentofabricante yrespuestaPI, revisión mecánica|
|P1|C16|220nFaceptadonominal;curvastípicassugierenmargen, no mínimogarantizado|RetenciónDC/T/edad≥59.42%delpresupuestoycolocacióncerca del INA180|
|P1|InterfazJ3|MPN, cable y llave del conector no elegidos;UART reservadaimplicaarnésespecífico|Pin1/orientación/fotoscontinuidad, longitudes/retornos y lista de cableado aprobada|
|P1|Firmware L432|Solo compilado;RUN bloqueado;una muestra síncrona reemplaza el promedio de 20 del F103|RelojPWM/ADC/DMA/frescura/tiempoISR/IWDG medidos; revalidar PI y calibrar|
|P1|Mecánica|U5 sin courtyard; inductor y testpoint sin modelo 3D declarado|Completar aprobación de encapsulados, clearances, altura, orientación y ensamblaje|
|P2|R1/MLCC/otros|Pulsos, C efectiva y temperaturas reales no ensayados|Cerrarpendientes individuales de la matriz e informe original|

No se ha añadido protección ADC definitiva, fuente auxiliar para bootstrap, clamps ni aisladores digitales. Se documentaron alternativas concretas, pendientes de selección y validación. R10=30.9k yC16=220nF sí están aceptados como cambios nominales. Los valores de 20/24 V y 2.5 A son hipótesis de evaluación, no fallas acotadas por hardware.

ERCactual:0errores,2avisosdocumentadosUARTsolo conector. Tener una netlist coherente o ERC sin error **no cierra** los riesgos anteriores. Fuentes y resultados en los otros cuatro informes de esta revisión.
