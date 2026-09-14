# Circuito ngspice

`buck.cir.in` es la fuente reproducible del circuito de la figura 1. El ejecutor
genera un `buck.cir` por caso y conserva el netlist, la salida textual y la forma
de onda en el directorio de resultados. Los netlists generados pueden ejecutarse
directamente con `ngspice -n -b buck.cir`.

Incluye fuente, MOSFET, diodo de rueda libre, filtro LC, carga, driver bootstrap
con tres BJT, generador PWM y sensor resistivo. El controlador PI y el comparador
PWM se representan con fuentes comportamentales. Los semiconductores tienen
modelos genéricos explícitos: no son modelos certificados de los componentes
reales. La DCR de 0.1 Ω y la ESR de 0.05 Ω son supuestos que deben medirse.

| Nodo | Significado |
|---|---|
| vin | Fuente de 12 V |
| pwm | Señal lógica de 5 V, fracción alta dprime |
| drive | Base común del par complementario del driver |
| boot | Alimentación bootstrap |
| gate | Compuerta del MOSFET |
| sw | Fuente del MOSFET, cátodo del diodo y entrada del inductor |
| out | Tensión sobre la carga |
| sense | Tensión del divisor, Vo/4 |
| feedback | Tensión reconstruida, 4·Vsense |
| integral | Estado del PI, adimensional |

La inicialización `.ic V(integral)=0` evita que el cálculo de operación CC del
circuito PWM asigne al PI un estado inicial arbitrario. La potencia parte del
reposo calculado; se dejan 10 ms antes del escalón. Los modelos promediados y PWM
ideal parten de 6 V y 1 A. Las comparaciones usan la ventana posterior al escalón.

Solver Gear, reltol=1e-5, abstol=1e-9 A, vntol=1e-7 V y paso máximo 500 ns.
La prueba de convergencia repite dprime+0.1 a 250 ns. `-n` evita configuraciones
locales; todos los dispositivos usados son internos de ngspice. El PI del
circuito es continuo; el digital se valida por separado con PWM en Python.

El circuito con pérdidas no produce exactamente 6 V cuando dprime=0.5.
Se reportan por separado ese sesgo estático y el error dinámico incremental.
