# Revisión de requisitos y próximos pasos

Revisión: 14 de septiembre de 2026. Fuente: `classroom/Descripcion Proyecto Buck.pdf`, páginas 1–3. Estado declarado por el equipo: no se han comprado componentes ni probado hardware. Los pesos siguientes no equivalen a una nota obtenida ni permiten calcular un porcentaje de avance.

| Guía | Requisito | Evidencia actual | Estado / cierre necesario |
|---|---|---|---|
| §2, figura 1 | 12 V, 660 µH, 20 µF, 6 Ω, 10 kHz; entrada d′ | Modelo y CAD; L1/L2 de 330 µH serie, C4/C5 de 10 µF paralelo | Valores nominales; medir componentes |
| §3, formato | Informe IEEE por entrega | Cuatro PDF y fuentes LaTeX/Markdown | Preparado; E2/E4 conservan resultados pendientes |
| §3.1, 20% | Derivación y dinámica de función de transferencia | E1: estados ON/OFF, promedio, polos, amortiguamiento, rizado | Evidencia numérica disponible |
| §3.1 | Comparar circuito completo y modelo, d′ 0.5→0.6 y 0.5→0.4 | E1: ngspice BJT y modelo, dos casos independientes | Evidencia numérica; no corresponde al driver IR2110 posterior |
| §3.1 | Análisis del error | E1: sesgo, RMS absoluto e incremental, error máximo | Evidencia numérica disponible |
| §3.2, 30% | Convertidor funcionando en lazo abierto | PCB, firmware y protocolo | Pendiente montaje y funcionamiento físico |
| §3.2 | Medir R/L/C y ajustar modelo | E2: tabla y modelo parametrizado, analizador | Pendiente medidor, valores e incertidumbre |
| §3.2 | Dos escalones experimentales y errores | E2: protocolo; captura automatizada preparada | Pendiente seis registros (tres por caso, criterio del equipo) |
| §3.3, 20% | Especificaciones, procedimiento de clase y pasos de diseño | E3: cruce, cero, normalización, margen, respuesta | Justificar elección del cero frente a recomendación habitual de clase |
| §3.3 | Referencia 6→7 V y 6→5 V | E3: dos casos, continuo, PWM digital y circuito | Evidencia numérica disponible |
| §3.3 | R +20% y −20%, referencia 6 V | E3: 7.2 Ω y 4.8 Ω | Evidencia numérica disponible |
| §3.4, 30% | Implementar y ajustar compensador | Firmware compilado y probado en computador | Pendiente cargar MCU, calibrar, medir latencia y retocar si procede |
| §3.4 | Repetir cuatro pruebas físicamente | E4: criterios, tablas y captura | Pendiente doce registros (tres por caso) |
| §5 | Potencia de carga mayor de 6 W | Banco nominal 2 × 12 Ω / 10 W en paralelo | Selección preparada; verificar resistencia y temperatura |
| §5 | Definir PWM, controlador y driver | STM32F103, PI digital, IR2110 + HCT14 | Decisiones cerradas; integración física pendiente |
| §4.1 | Fechas de entrega | Guía fechada mayo de 2025 | Confirmar calendario actual; no trasladar fechas automáticamente |

## Relación con el método de clase

`classroom/10 The Frequency-Response Design Method.pdf`, sección 7, lámina 90, presenta el PI y recomienda normalmente un cero muy inferior al cruce para reducir pérdida de fase. El diseño actual usa cero 3000 rad/s y cruce 1000 rad/s. El PI aporta −71.565°; la planta aproximadamente −6.36°, con margen continuo 102.07°. E3 documenta esta desviación, la normalización de ganancia y las comprobaciones de desempeño. Conviene confirmar con el profesor que esta justificación satisface el procedimiento esperado; no hay evidencia de aprobación docente.

## Orden de ejecución

1. **Componentes:** cerrar referencias, stock, dimensiones y precio entregado; especialmente inductores y capacitores. Medir RLC cuando estén disponibles.
2. **Prototipo soldado:** comprobar bootstrap, inversión, apagado por RUN, disparo enclavado, sensores y alimentación con fuente limitada.
3. **Liberación CAD:** corregir hallazgos, repetir ERC/DRC/paridad y obtener cotizaciones PCBWay/JLCPCB. Mantener fabricación retenida hasta cerrar la calificación física.
4. **Montaje y firmware:** inspeccionar, programar, calibrar ADC, verificar temporización y protección; medir rizado y temperatura.
5. **Laboratorio:** tres repeticiones por cada uno de los seis escenarios, con datos originales, instrumentos, fecha, parámetros e incertidumbre. La repetición triple es una decisión metodológica del equipo, no un número exigido explícitamente por la guía.
6. **Informes:** completar tablas E2/E4, comparar modelo ajustado, discutir errores y conservar resultados antes/después del reajuste.

Presupuesto objetivo: COP 350 000 (COP 87 500 por integrante). Estimado actual: COP 281 501.95; reserva COP 68 498.05. Incluye asignaciones sin cotización final. No hay pedidos realizados. Prioridad inmediata: calificación de componentes y prototipo, antes de ordenar PCB.

## Límites de la evidencia

Los renders prueban representación geométrica, ERC/DRC reglas CAD y las pruebas C comportamiento en computador. Ninguno demuestra eficiencia, compatibilidad electromagnética, seguridad térmica, funcionamiento del bootstrap, precisión del ADC o desempeño físico. El anexo muestra modelos estándar y envolventes provisionales identificadas; las holguras deben comprobarse con piezas reales.
