# Montaje, conexiones y aceptación

## Antes de fabricar

- Imprimir el plano 1:1 sin «ajustar a página». Colocar sobre él **los componentes
  recibidos**, especialmente L1/L2, IR2110 DIP14, TO-220, shunt y conectores.
- Medir L1+L2, DCR total, C4+C5, ESR, resistencias y shunt. Registrar instrumento,
  incertidumbre, fecha y número de muestra. Comprobar inductores bajo corriente.
- Probar una Blue Pill por SWD: reloj HSE 8 MHz, PLL 72 MHz, flash ≥64 KB,
  RAM ≥20 KB, ADC, UART y reset. Una publicación comercial no acredita
  autenticidad ni funcionamiento equivalente de un clon.
- Hacer un prototipo **soldado y compacto** de driver, etapa de potencia y
  protecciones. Verificar polaridad de PWM, carga bootstrap, apagado y sensado
  con fuente limitada. No usar protoboard sin soldadura para la etapa conmutada.
- Repetir ERC, DRC, comparación de conectividad y revisión visual de Gerbers
  después de cualquier cambio. Aprobar el costo entregado antes del pedido.

## Conexiones

J1: pin 1 = +12 V **después de fusible externo rápido de 2 A**; pin 2 = GND.
J2: pin 1 = salida positiva; pin 2 = retorno de carga. El fusible y su portafusible
son accesorios externos obligatorios; no están dibujados como componentes de PCB.
La entrada no incorpora protección contra polaridad inversa: verificar antes
de conectar. No conectar esta placa a la red eléctrica.

J3 se lee por números de pad, vistos desde componentes: pad cuadrado = 1;
columnas 1–3–5–7–9 y 2–4–6–8–10. Construir un cable polarizado, comprobarlo
con continuidad y evitar conectarlo desplazado una fila.

| J3 | Señal | Blue Pill / función |
|---:|---|---|
| 1 | +5V | Pin 5V, alimentación desde U2 |
| 2 | GND | GND |
| 3 | MCU_PWM | PA8 / TIM1_CH1; d′ alto apaga el MOSFET |
| 4 | RUN | PB0; bajo fuerza apagado |
| 5 | RESET | PB1; pulso alto borra latch solo si no persiste la causa |
| 6 | NFAULT_MCU | PB10; **bajo = falla**; transistor colector abierto |
| 7 | VSENSE | PA0 / ADC1_IN0; nominal Vo/4 |
| 8 | GND | Retorno de señal junto al sensado |
| 9 | +3V3 | Salida 3.3 V del STM32 para pull-up de falla |
| 10 | GND | Retorno adicional |

UART externo de **lógica 3.3 V**: PA9 TX→RX del adaptador; PA10 RX←TX;
GND común. No conectar su pin de alimentación. SWD: PA13 SWDIO, PA14 SWCLK,
GND y, si existe, NRST. Consultar el pinout real del ST-LINK mini: su pin
«3.3V» puede ser una **salida**, no una entrada VTref. No unir alimentaciones
de programador, USB-C y U2. Programar inicialmente la Blue Pill desconectada
de J3; en el montaje, alimentar desde U2 con USB-C desconectado.

Los pull-ups de PWM proceden de +5 V: conectar la interfaz completa con la
energía retirada. No mantener la placa de potencia alimentada con un STM32
sin alimentación unido parcialmente por sus señales. Un cable completamente
retirado deja RUN bajo y PWM alto, ambos estados de apagado.

| Punto | Señal / medida |
|---|---|
| TP1 | VIN, respecto de TP2 |
| TP2 | GND |
| TP3 | SW = fuente del MOSFET |
| TP4 | GATE; **VGS = TP4 − TP3**, no TP4 − GND |
| TP5 | VOUT |
| TP6 | ISENSE, nominal 1 V/A |
| TP7 | SD; alto ordena apagar el IR2110 |
| TP8 | NTRIP; bajo indica comparador activo |
| TP9 | PWM d′ antes de la inversión |

Usar sonda diferencial apropiada para VGS, o dos sondas con ambas masas en
GND y resta de canales dentro de sus límites. **Nunca enganchar la masa de
un osciloscopio referido a tierra al nodo SW.** Minimizar el lazo de la sonda
al medir rizado. El tab metálico de Q1 es VIN; el de U2 es GND: no compartir
un disipador conductor sin aislamiento.

## Protección y límites

RS1 = 50 mΩ; INA180A1 tiene ganancia 20: ISENSE ≈ 1 V/A. R8/R9 producen
VREF nominal de 2 V desde +5 V. El primer LM393 dispara aproximadamente a
2 A de **corriente del inductor**, incluyendo corriente del capacitor. El
segundo dispara a Vo ≈ 8.2 V mediante R10/R11 = 31k/10k. No son umbrales
de precisión: incluir regulación de U2, tolerancias, offset, ganancia y
retardo de comparador. Medir ambos umbrales antes de operar normalmente.

| Condición | Resultado lógico |
|---|---|
| RUN = 0 | SD = 1, driver apagado |
| NTRIP = 0 | FAULT = 1; reset no puede anular la causa activa |
| NTRIP vuelve a 1 | La falla permanece retenida |
| RESET = 1 y NTRIP = 1 | Borra latch; solo RUN puede habilitar |
| PWM d′ = 1 | HIN = 0, MOSFET apagado |

Al encender, el estado del latch no se supone conocido. RUN tiene pull-down;
el firmware inicia apagado y exige borrar la falla. El watchdog interno
provoca reset si faltan interrupciones con ADC fresco, nominalmente en unos
6.4 ms (depende del LSI). No garantiza apagado instantáneo ante cualquier
avería del MCU: el latch de corriente/tensión actúa independientemente.

El bootstrap de 1 µF es una estimación conservadora: comprobar su capacitancia
efectiva a tensión, VBS durante el duty máximo y VGS real. No aplicar duty
físico de 100%; el PI limita a 95%. El tiempo apagado de 5 µs al límite debe
permitir recarga suficiente; se verifica con osciloscopio. Las pistas de
sensado de RS1 se deben revisar como conexiones Kelvin en el prototipo y
contrastar contra corriente externa; la caída de cobre compartido forma parte
del error mientras no se mida.

## Banco de carga externo

- Dos resistencias de **12 Ω / 10 W en paralelo**: 6 Ω nominales.
- Una **1.2 Ω / 5 W en serie**, normalmente puenteada por S1: abrir S1 para 7.2 Ω.
- Una rama de **24 Ω**, hecha con dos 12 Ω / 5 W en serie, conectable con S2
  en paralelo al banco de 6 Ω: cerrar S2 para 4.8 Ω.
- S1/S2 con capacidad DC ≥3 A a 24 V. Partir de S1 cerrado y S2 abierto;
  cambiar solo el interruptor del caso ensayado. Medir la resistencia real.

Los escalones mecánicos tienen rebote: registrar la transición real y repetir
el ensayo si aparecen varios eventos. Mantener las resistencias elevadas de
materiales combustibles y dejar enfriar antes de tocarlas. A 7 V sobre 4.8 Ω
la carga disipa unos 10.2 W en total.

## Puesta en marcha y pruebas

1. Placa sin energía: inspección por dos personas, polaridades, continuidad,
   resistencias entre rieles y ausencia de puentes. Revisar orientación de
   U1 (girado respecto de los otros DIP), cátodos, Q1 y Q2.
2. Sin MCU ni habilitación: aplicar 12 V con límite inicial 50–100 mA;
   verificar +5 V, consumo, SD alto y VGS cercano a cero. Quitar alimentación
   antes de conectar J3. Si el consumo normal supera el límite, investigar
   antes de aumentarlo.
3. Con MCU y carga de 6 Ω: confirmar apagado durante encendido/reset, PWM
   alto en reposo, reloj, ADC y UART. Borrar latch; observar la rampa con
   límite de fuente prudente, subiendo el límite solo según mediciones.
4. Calibrar tensión con DMM en dos puntos; actualizar `calibration.h`, compilar
   y repetir. Comprobar corriente externa frente a TP6 y caídas de RS1/cobre.
5. Verificar overcurrent en ensayo breve usando 1.2 Ω como carga de prueba,
   rampa desde apagado y captura simultánea de corriente/TP8/SD/VGS. Su
   potencia a 2 A es 4.8 W: no mantener el ensayo. No hacer cortocircuito franco.
6. Para OVP, mantener RUN bajo y VIN a 12 V; retirar carga y aplicar a VOUT
   una segunda fuente aislada, limitada a 50 mA, elevando lentamente hacia
   8.2 V. Confirmar el latch y que no pueda borrarse mientras persiste OVP.
   Confirmar previamente con el responsable del laboratorio los retornos
   comunes y la ausencia de corrientes de retorno entre fuentes.
7. Probar reset, retirada completa del cable, ADC detenido mediante depurador
   y watchdog; medir el tiempo real de apagado. Registrar VGS y VBS, ruido,
   rizado, IL pico y temperaturas en MOSFET, diodo, regulador, bobinas y shunt.
8. Ejecutar OL d′: 0.5→0.6 y 0.5→0.4; PI: 6→7 V, 6→5 V y R: 6→7.2 Ω,
   6→4.8 Ω. **Tres repeticiones por caso**; volver a estabilizar antes de cada una.

Para los escalones de referencia/PWM, automatizar captura RAM y comando.
Para carga manual, usar el osciloscopio con pretrigger y disparo por cambio de
Vo; 512 medias en RAM solo cubren 51.2 ms y no garantizan capturar una maniobra
manual. La RAM almacena medias de periodo, no el rizado de 10 kHz: medir este
con osciloscopio a ≥200 kS/s, preferiblemente bastante más para VGS y SW.

Usar el contrato de `project/data/README.md` y adjuntar mediciones reales de
R/L/C/DCR/ESR, fecha, instrumentos, unidades, condiciones iniciales y evento.
Evaluar las mismas bandas y métricas de los informes, con incertidumbre de
ADC y sondas. Si se retoca PI, preservar ganancias originales y justificar
el nuevo ajuste con resultados. Solo entonces completar entregas 2 y 4.
