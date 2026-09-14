# Implementación y protocolo de laboratorio

Estado: no se ha construido ni probado una tarjeta física. Ya existe un
[diseño PCB con IR2110](../pcb/README.md) y un [adaptador STM32F103](../firmware/README.md)
compilado y probado en computador. El núcleo C conserva su interfaz independiente
del hardware. Para componentes, cableado y pruebas de esa revisión usar
[el protocolo específico](../pcb/docs/assembly-and-tests.md); las propuestas
generales siguientes corresponden a la base de los informes del curso.

## Componentes y límites

| Elemento | Valor/propuesta | Verificación antes de energizar |
|---|---|---|
| Fuente | 12 V CC, limitación de corriente | Comenzar con límite bajo; aumentar sólo después de comprobar conmutación |
| Inductor | 660 µH, corriente de saturación propuesta ≥3 A | Medir L y resistencia CC; confirmar temperatura y corriente pico |
| Capacitor | 20 µF, tensión nominal ≥25 V | Medir C y ESR; comprobar corriente de rizado permitida |
| Carga nominal | 6 Ω, propuesta 25 W | A 7 V: 8.17 W; a 7 V/4.8 Ω: 10.21 W |
| Carga +20% | 7.2 Ω, ≥25 W | Conectar 1.2 Ω en serie con 6 Ω |
| Carga -20% | 4.8 Ω, ≥25 W | Conectar 24 Ω en paralelo con 6 Ω |
| MOSFET | IRFZ14 o equivalente adecuado | Confirmar hoja de datos, VDS, VGS y pérdidas; no conducir directo desde GPIO |
| Diodo | 1N5822 o equivalente | Polaridad: ánodo a masa, cátodo al nodo de conmutación |
| Driver | 2N2222, 2N3904, 2N2907; 1 kΩ, 1.2 kΩ; 1N4148; bootstrap 1 µF | Seguir figura 1; identificar terminales en la hoja de datos del encapsulado real |
| Sensor | 30 kΩ/10 kΩ, tolerancia ≤0.1%, divisor 1:4 | 6 V→1.5 V, 7 V→1.75 V; calibrar ganancia y offset |
| Adquisición | ADC de 3.3 V, ≥12 bits, muestreo sincronizado | 3.3 V/4095×4 = 3.22 mV de salida por cuenta |

Los límites son propuestas de selección, no una certificación térmica. Los
modelos genéricos de ngspice no reemplazan hojas de datos ni curvas de pérdidas.
No usar la frecuencia o el valor de inductancia del ejemplo `Ej_Buck.m`.

## Interfaces del controlador digital

1. Generar un PWM de 10 kHz cuya fracción ALTA sea dprime. El driver invierte:
   MOSFET encendido durante d=1-dprime. Con la potencia desconectada, comprobar
   con osciloscopio que dprime=1 mantiene el MOSFET apagado. Un GPIO flotante
   no es un estado seguro: disponer de apagado por hardware al reiniciar.
2. Medir el promedio de tensión durante un periodo completo, no un punto
   arbitrario del rizado. Configurar ADC con disparo de temporizador y DMA;
   promediar las muestras uniformes del periodo y convertir a voltios de salida.
   La impedancia del divisor puede exigir un buffer o mayor tiempo de adquisición.
3. Invocar `buck_update` cada 100 µs con el promedio del periodo terminado.
   Escribir dprime al registro PWM con precarga; aplicar el comando al siguiente
   periodo. El modelo PWM valida esa latencia y la medida promediada.
4. Usar referencia de 6 V en operación. Para las pruebas cambiar a 7 V o 5 V
   en un instante registrado. El escalón de carga cambia sólo la carga.
5. El integrador es adimensional; Ki tiene unidades 1/(V·s), Kp tiene 1/V.
   No pasar directamente voltios del ADC: usar la tensión de salida reconstruida.
6. `buck_reset` sólo se permite tras retirar la causa de una falla. El estado
   deshabilitado y la falla devuelven dprime=1. La saturación normal es
   0.05≤d≤0.95. Confirmar que la periferia puede generar un 100% ALTO real.

El núcleo incluye apagado por medida inválida y sobretensión >8.5 V. Este chequeo
de software no reemplaza un comparador de sobrecorriente/enable independiente.
El ajuste del disparo de corriente requiere datos del inductor/MOSFET reales.
Preparar una rampa de referencia para arranque y verificarla por separado antes
de conectar cargas sensibles; las pruebas de escalón parten de 6 V estabilizados.
No se afirma que este núcleo sea un firmware listo para grabar.

## Entrega 2: lazo abierto

1. Registrar equipo, fecha, componentes reales, L, C, ESR, resistencia CC de L,
   R y Vin medidos; guardar incertidumbre y condiciones del medidor LCR.
2. Comprobar continuidad, polaridad, aislamiento y conexiones sin alimentación.
   Utilizar una sonda diferencial para VGS del MOSFET de lado alto. No conectar
   la pinza de masa de un osciloscopio puesto a tierra al nodo de conmutación.
3. Ensayar PWM y driver con potencia desconectada. Verificar frecuencia, signo,
   amplitud VGS y estado de apagado. Energizar luego con fuente limitada.
4. Establecer dprime=0.5. Medir Vo, IL, rizado, VGS y temperaturas en régimen.
   Vo puede ser menor que 6 V por pérdidas: registrar el valor, no ocultarlo
   ajustando la fuente o el duty nominal.
5. Capturar por separado 0.5→0.6 y 0.5→0.4, con ≥5 ms de pretrigger y ≥20 ms
   posteriores. Registrar PWM y tensión simultáneamente; repetir tres veces.
6. Exportar CSV con las columnas del contrato en `data/README.md`. Conservar
   también el archivo original del osciloscopio; no reemplazarlo por curvas
   suavizadas. Calcular error absoluto e incremental con parámetros medidos.

## Entrega 4: lazo cerrado

1. Integrar y comprobar el adaptador ADC/PWM en la tarjeta elegida. Registrar
   periodo, latencia efectiva, calibración, resolución y revisión del firmware.
2. Arrancar con referencia gradual y límite de corriente; estabilizar a 6 V.
   Si cambia la polaridad del driver, rediseñar explícitamente el signo del lazo.
3. Capturar 6→7 V, 6→5 V, R:6→7.2 Ω y R:6→4.8 Ω. Volver al punto nominal
   entre capturas. Hacer tres repeticiones de cada caso.
4. Medir error estacionario, sobreimpulso, tiempo de establecimiento, desviación
   de carga, rizado y rango de duty. Comparar con las especificaciones del informe 3.
5. Documentar cualquier cambio de Kp/Ki y repetir los cuatro casos. Nunca
   atribuir a hardware los resultados que sólo existen en simulación.

## Evidencia que completa el proyecto físico

- Fotografías y esquema final con referencias reales.
- Registro de R/L/C, incertidumbres, instrumentos y condiciones térmicas.
- Dos capturas de lazo abierto y cuatro de lazo cerrado, con repeticiones.
- CSV originales, análisis reproducible y tablas de comparación.
- Configuración/firmware de la tarjeta real y demostración de apagado seguro.
- Informes 2 y 4 completados con resultados propios y conclusiones sustentadas.
