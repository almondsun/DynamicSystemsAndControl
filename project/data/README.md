# Datos experimentales

Esta carpeta no contiene mediciones ni datos sintéticos presentados como reales.

Cada captura debe ser un CSV UTF-8 con encabezado:

```csv
time_s,voltage_V,dprime,load_ohm,reference_V
```

Usar segundos, voltios, dprime entre 0 y 1 y resistencia en ohmios. El tiempo
debe ser estrictamente creciente y todas las columnas deben ser finitas.
`voltage_V` debe ser tensión de salida calibrada, no tensión cruda del ADC.
El archivo debe contener el periodo anterior y posterior al escalón. Registrar
el instante del escalón y la frecuencia de muestreo. Para estudiar rizado,
capturar al menos 20 muestras por periodo PWM (≥200 kS/s).

Guardar un JSON por montaje con claves `Vin`, `L_H`, `C_F`, `R_ohm`,
`inductor_DCR_ohm`, `capacitor_ESR_ohm`, `step_time_s`, `instrument`, `date` y
`initial_current_A` si se midió. Los valores R/L/C deben provenir del medidor.
El analizador usa el modelo ideal y reporta el sesgo que producen pérdidas no
incluidas; no ajusta R/L/C para hacer coincidir artificialmente las curvas.
