# Fuentes y supuestos técnicos

Fuentes recuperadas durante la implementación (14 de septiembre de 2026):

- [IR2110/IR2113, Infineon, PD60147 rev.V](https://www.infineon.com/assets/row/public/documents/24/49/infineon-ir2110-datasheet-en.pdf):
  pinout **DIP14** revisado visualmente en página 5; salida HO en fase con HIN,
  apagado SD, alimentación driver 10–20 V, bootstrap y UVLO. No intercambiar
  con el encapsulado SOIC16. Retardos típicos 120/94 ns con condiciones de
  ensayo distintas de este montaje; no son mediciones ni límites garantizados aquí.
- [IRFZ44NPbF, Infineon, PD-94787B](https://www.infineon.com/assets/row/public/documents/24/49/infineon-irfz44n-datasheet-en.pdf):
  55 V, TO-220 G/D/S, tab D; RDS(on) máxima 17.5 mΩ bajo condiciones indicadas;
  Qg máxima 63 nC a VGS=10 V. No interpretar «49 A» como corriente continua
  permitida en esta PCB sin condiciones térmicas.
- [INA180, TI, SBOS741H](https://www.ti.com/lit/ds/symlink/ina180.pdf):
  **A1, pinout A**, SOT23-5: OUT=1, GND=2, IN+=3, IN−=4, VS=5;
  ganancia 20 V/V, modo común −0.2 a 26 V. La variante B cambia pines.
- [LM393, TI](https://www.ti.com/lit/ds/symlink/lm393.pdf):
  salidas colector abierto, rango de modo común y retardo; exigir **DIP8**.
- [SN74HCT00, TI](https://www.ti.com/lit/ds/symlink/sn74hct00.pdf) y
  [SN74HCT14, TI](https://www.ti.com/lit/ds/symlink/sn74hct14.pdf):
  puertas NAND/inversores y umbrales compatibles con lógica TTL a 5 V.
- [1N5820–1N5822, Vishay](https://www.vishay.com/docs/88526/1n5820.pdf):
  1N5822 de 40 V / 3 A, DO-201AD, polaridad del cátodo.
- [ST RM0008, copia de Keil](https://www.keil.com/dd/docs/datashts/st/stm32f10xxx.pdf):
  revisión 9 de 995 páginas. Tabla 62: ADC1 EXTSEL=100 para TIM3_TRGO;
  tabla de interconexión TIM3: ITR0=TIM1; capítulos ADC, DMA, TIM1,
  temporizadores generales y watchdog. Es una revisión antigua: contrastar
  erratas de la referencia exacta recibida antes de laboratorio.
- [Definiciones oficiales STM32F103xB de ST](https://github.com/STMicroelectronics/cmsis-device-f1/blob/master/Include/stm32f103xb.h):
  contrastadas para mapa de memoria y registros. El firmware propio no copia
  HAL/CMSIS ni presupone un bootloader de terceros.

El entorno local conserva los documentos recuperados en
`artifacts/buck-pcb-reference/`. Algunos enlaces alternativos de ST/Infineon
fallaron o agotaron tiempo; no se usan como evidencia. No se consiguió una
ficha completa del toroide local ni se cerró un MPN de capacitor con su curva
de rizado: son condiciones explícitas de retención de fabricación.

## Estimación de bootstrap y protección

Con Cboot efectivo de 1 µF, Qg=63 nC y corriente de reposo bootstrap máxima
de 230 µA, un pulso de 95 µs extrae aproximadamente 85 nC antes de otras
fugas. Incluyendo 50 µA adicionales resulta ≈90 nC, o ≈0.09 V de caída.
La carga inicial aproximada a Vin=12 V es 11.3 V después del diodo: hay
margen nominal frente al UVLO superior de 9.7 V. Esta cuenta no modela
inductancias parásitas, arranque, temperatura, tolerancia ni pérdida de
capacitancia cerámica por tensión. Verificar VBS y VGS reales a duty alto.

La auditoría `tools/verify.py` calcula límites conservadores de disparo con
regulación de +5 V ±5%, resistencias ±1%, ganancia INA ±1%, offset de entrada
±0.5 mV y comparador ±5 mV. Son estimaciones estáticas, no una calificación
de todas las temperaturas o de transitorios. Los resultados numéricos se
guardan con la validación; medir y ajustar resistencias si se necesita un
umbral de corriente más preciso.

## Modelos y diseños de referencia

Se consultaron [ikajdan/stm32-buck-converter](https://github.com/ikajdan/stm32-buck-converter)
y [HakanD1/24v-to-5v-50w-buck-converter-stm32](https://github.com/HakanD1/24v-to-5v-50w-buck-converter-stm32).
Sus tensiones, frecuencias, drivers y plataformas difieren del curso. No se
copió una PCB suponiendo que fuera equivalente ni se acredita una fabricación
previa de esta revisión. Los símbolos del proyecto son propios; las huellas
estándar proceden de las bibliotecas KiCad 10. El ruteo utiliza Freerouting 2.4.1.

La simulación aislada usa L=660 µH, C=20 µF, DCR total=0.20 Ω, shunt=0.05 Ω,
RDS(on)=0.022 Ω, Vf=0.45 V y ESR total=0.15 Ω. Parte de IL=0 A y VC=0 V,
incluye la rampa, conversión ADC nominal de 12 bits, promediado y latencia.
El sensado incluye el polo nominal (3k || 1k) × 1nF = 0.75 µs.
Emplea integración Euler a 0.5 µs con resolución fraccional de los flancos PWM;
se contrasta a 0.25 µs. No modela fielmente capacitancias del MOSFET,
recuperación inversa, saturación del núcleo, ESR dependiente de frecuencia,
bootstrap dinámico ni rebote mecánico. Actualizar el modelo solo con datos
medidos y mantener separado el resultado original del curso.
