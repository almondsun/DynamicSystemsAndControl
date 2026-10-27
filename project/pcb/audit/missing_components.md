# Checklist de componentes y archivos pendientes

Consulta: 2026-10-24. Fuentes: Excel `BOM auditada` (57 filas de datos), BOM CSV (57 referencias), manifiesto de archivos con SHA-256. Coincidencia de designators/valores/footprints históricos: sin discrepancias.

Disponibilidad adicional: las 57 referencias tienen símbolo previo y footprint original en disco; 39 componentes comprables tienen también un footprint genérico candidato existente, pendiente de cotejar con fabricante. Reutilizarlos puede evitar descargas nuevas.

Los indicadores DS/S/F/3D siguientes cuentan archivos descargados identificados para el candidato, conservados en vendor_assets_local. Una biblioteca genérica instalada o un símbolo previo del proyecto se registra aparte en component_inventory.csv y existing_project_assets.csv; no se considera biblioteca comercial ya validada. Un URL web NO cuenta como archivo local.

Componentes comprables: 48. Juegos completos de cuatro tipos descargados: 1. Pendientes de selección definitiva: 48. Sin MPN en Excel: 31; sin candidato exacto tras investigación: 1.

|Ref|MPN candidato|Faltantes descargados|Estado archivos|Acción técnica pendiente|
|---|---|---|---|---|
|J1|TB002-500-02BE|datasheet, símbolo KiCad, footprint KiCad|parcial|Conector 12V: revisar corriente, torque y proceso de ensamblaje SMD/THT; faltan protección polaridad y fusible on-board ; PDF oficial devolvió 403; verificar torque, agujeros, cable y proceso Wave; conservar THT hasta decidir montaje|
|Q1|IRFZ44NS|símbolo KiCad, footprint KiCad, 3D|parcial|No asumir misma referencia ni pinout; validar Rds(on), Qg, Tj, cobre para disipación|
|D1|SS34|símbolo KiCad, footprint KiCad, 3D|parcial|Validar pérdidas a corriente real y cobre; estudiar picos de tensión SW|
|L1|XR6826TS331MHL65|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|Irated 3.2 A, Isat 6.5 A publicados; verificar stock, DCR, geometría, soldadura JLC y acoplamiento|
|L2|XR6826TS331MHL65|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|Irated 3.2 A, Isat 6.5 A publicados; verificar stock, DCR, geometría, soldadura JLC y acoplamiento|
|RS1|RLP25FEER050|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|50 mΩ 1% 2 W; validar pad Kelvin, MPN y térmica|
|J2|TB002-500-02BE|datasheet, símbolo KiCad, footprint KiCad|parcial|Conector de carga: corriente ≥3A, holgura y zona caliente, sin carga en placa ; PDF oficial devolvió 403; verificar torque, agujeros, cable y proceso Wave; conservar THT hasta decidir montaje|
|C1|EMZR250ARA101MF61G|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|100 uF 25 V; ESR 260mΩ y 300mA@100 kHz; verificar corriente admisible a 10 kHz|
|C2|EMZR250ARA101MF61G|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|100 uF 25 V; ESR 260mΩ y 300mA@100 kHz; verificar corriente admisible a 10 kHz|
|C3|CC0603KRX7R9BB104|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|Desacoplo VIN: escoger 100 nF X7R >= 25 V; muy cerca del lazo de potencia ; Capacitancia efectiva, temperatura, ESL y ubicación por IC; conservar 50 V; C10 depende del regulador|
|C4|BXJ35V10UF05*05|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|ESR 800mΩ@100kHz, 155mA@100kHz; revisar a 10kHz y adecuación a SMT automático|
|C5|BXJ35V10UF05*05|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|ESR 800mΩ@100kHz, 155mA@100kHz; revisar a 10kHz y adecuación a SMT automático|
|U1|IR2110STRPBF|símbolo KiCad, footprint KiCad|parcial|Reasignar pines 14 DIP a 16 SOIC; comprobar disponibilidad y fixture; boot, VGS y SD|
|D2|US1G|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|400 V, 1 A, trr 50 ns listado; verificar Vf y recuperación a corrientes del bootstrap|
|C6|CL21B105KBFNNNE|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|Bootstrap: 1uF >=25V X7R con C efectivo al VBS real, posicionar pegado VB/VS ; Bootstrap: C efectivo a VBS, Qg total, fugas, UVLO y tiempo de recarga; aprobación depende de U1 y Q1|
|C7|CC0603KRX7R9BB104|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|Desacoplo VCC driver 12V: 100 nF cerca COM/VCC y baja impedancia ; Capacitancia efectiva, temperatura, ESL y ubicación por IC; conservar 50 V; C10 depende del regulador|
|C8|CC0603KRX7R9BB104|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|Desacoplo VDD driver 5V: 100 nF junto VDD/VSS ; Capacitancia efectiva, temperatura, ESL y ubicación por IC; conservar 50 V; C10 depende del regulador|
|R1|0805W8F100JT5E|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|10Ω compuerta: revisar resistencia de pulso, ubicación y ringing; preferir 0805 ; No aprobar por valor: verificar curva de sobrecarga pulsada con Qg/frecuencia, corriente de gate y ringing; ficha JLC no recuperable|
|R2|0603WAF1002T5E|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|10k puerta a fuente; 0603/0805 1% ; Calcular potencia y derating, TCR y tolerancia de divisores/umbrales, corriente de base/pull-up según referencia|
|U2|78M05|símbolo KiCad, footprint KiCad, 3D|parcial|12->5V: 0.7 W a 100mA; revisar RthJA y cobre, consumo Blue Pill + lógica|
|C9|CL21B334KBFNNNE|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|Regulador 5 V: confirmar mínimo en datasheet del MPN ; Confirmar recomendación de 78M05 exacto, C efectivo y montaje|
|C10|CC0603KRX7R9BB104|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|Regulador 5 V: confirmar ESR/estabilidad y capacitor recomendado ; Capacitancia efectiva, temperatura, ESL y ubicación por IC; conservar 50 V; C10 depende del regulador|
|C11|CL21A106KAYNNNE|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|Regulador: 10uF >=10V para reservorio; escoger tecnología y footprint ; Cambio electrolítico a MLCC: verificar estabilidad/ESR regulador, C efectivo a 5 V y temperatura; biblioteca Altium localizada; convertir pendiente|
|U3|SN74HCT14DR|ninguno; validar integración|completo|Mismo principio HCT/Schmitt e interfaz TTL; verificar pines y Vih a 5 V|
|R3|0603WAF1002T5E|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|10k pull-up a 5V; 0603 1% ; Calcular potencia y derating, TCR y tolerancia de divisores/umbrales, corriente de base/pull-up según referencia|
|R4|0603WAF1001T5E|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|1k interfaz PWM MCU; 0603 1% ; Calcular potencia y derating, TCR y tolerancia de divisores/umbrales, corriente de base/pull-up según referencia|
|C12|CC0603KRX7R9BB104|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|HCT14: 100nF al lado de los pines de alimentación ; Capacitancia efectiva, temperatura, ESL y ubicación por IC; conservar 50 V; C10 depende del regulador|
|U4|SN74HCT00DR|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|Verificar numeración y simulación de latch durante inicio, reset y falla|
|C13|CC0603KRX7R9BB104|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|HCT00: 100nF al lado de los pines de alimentación ; Capacitancia efectiva, temperatura, ESL y ubicación por IC; conservar 50 V; C10 depende del regulador|
|R5|0603WAF1002T5E|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|10k RUN a tierra; 0603 1% ; Calcular potencia y derating, TCR y tolerancia de divisores/umbrales, corriente de base/pull-up según referencia|
|R6|0603WAF1002T5E|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|10k RESET a tierra; 0603 1% ; Calcular potencia y derating, TCR y tolerancia de divisores/umbrales, corriente de base/pull-up según referencia|
|R7|0603WAF4701T5E|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|4.7k pull-up salida colector abierto LM393; 0603 1% ; Calcular potencia y derating, TCR y tolerancia de divisores/umbrales, corriente de base/pull-up según referencia|
|U5|LM393BIDR|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|Comparador variante B; comprobar pinout, offset, entradas, retardo y falsas detecciones|
|C14|CC0603KRX7R9BB104|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|LM393: 100nF al lado de los pines de alimentación ; Capacitancia efectiva, temperatura, ESL y ubicación por IC; conservar 50 V; C10 depende del regulador|
|R8|0603WAF1502T5E|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|15k 1% divisor de VREF; 0603 1%, considerar dependencia de +5V ; Calcular potencia y derating, TCR y tolerancia de divisores/umbrales, corriente de base/pull-up según referencia; R8 categoría JLC no recuperable|
|R9|0603WAF1002T5E|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|10k 1% divisor de VREF; 0603 1% ; Calcular potencia y derating, TCR y tolerancia de divisores/umbrales, corriente de base/pull-up según referencia|
|C15|CC0603KRX7R9BB104|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|Filtro VREF: 100 nF, tolerancia y posicionamiento cerca del comparador ; Capacitancia efectiva, temperatura, ESL y ubicación por IC; conservar 50 V; C10 depende del regulador|
|R10|**SIN MPN EXACTO**|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|31k 1% divisor OVP; 0603 1% ; No se verificó MPN exacto 31kohm. 31.6kohm solo alternativa NO asignada; cambia umbral OVP|
|R11|0603WAF1002T5E|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|10k 1% divisor OVP; 0603 1% ; Calcular potencia y derating, TCR y tolerancia de divisores/umbrales, corriente de base/pull-up según referencia|
|U6|INA180A1IDBVR|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|Conservar variante A1 (OUT=1, IN+=3, IN-=4), comprobar trazas Kelvin y alimentación|
|C16|CC0603KRX7R9BB104|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|INA180: 100nF junto VS-GND ; Capacitancia efectiva, temperatura, ESL y ubicación por IC; conservar 50 V; C10 depende del regulador|
|Q2|MMBT3904|símbolo KiCad, footprint KiCad, 3D|parcial|Verificar pines E/B/C contra su propia hoja de datos|
|R12|0603WAF1002T5E|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|10k a base NPN; 0603 1% ; Calcular potencia y derating, TCR y tolerancia de divisores/umbrales, corriente de base/pull-up según referencia|
|R13|0603WAF1002T5E|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|10k pull-up NFAULT_MCU a +3.3V; 0603 1% ; Calcular potencia y derating, TCR y tolerancia de divisores/umbrales, corriente de base/pull-up según referencia|
|R14|RC0603FR-073KL|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|3k 1% divisor ADC; 0603 1% ; Comprobar error ADC y tolerancia frente a R15, potencia, TCR y muestreo; categoría JLC no confirmada|
|R15|0603WAF1001T5E|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|1k 1% divisor ADC; 0603 1% ; Calcular potencia y derating, TCR y tolerancia de divisores/umbrales, corriente de base/pull-up según referencia|
|C17|0603CG102J500NT|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|Filtro ADC 1nF, definir X7R/C0G y mantener τ=(3k;;1k)C ; Verificar settling ADC, tolerancia total del divisor y filtro; tau nominal 0.75 us|
|J3|61201021621|datasheet, símbolo KiCad, footprint KiCad, 3D|ausente|Conector MCU 2x5: elegir polarizado de llave y acoplar a Blue Pill externa ; Confirmar cable complementario, llave, orden de señales, huecos y montaje JLC; código JLC no localizado|

## Puntos de prueba: sin componente comprable

- [ ] TP1 (VIN): revisar pad superficial y acceso. Existe `C:\Program Files\KiCad\10.0\share\kicad\footprints\TestPoint.pretty\TestPoint_Pad_D2.0mm.kicad_mod`. No requiere datasheet, MPN ni modelo 3D comercial. Sin cambios en PCB.
- [ ] TP2 (GND): revisar pad superficial y acceso. Existe `C:\Program Files\KiCad\10.0\share\kicad\footprints\TestPoint.pretty\TestPoint_Pad_D2.0mm.kicad_mod`. No requiere datasheet, MPN ni modelo 3D comercial. Sin cambios en PCB.
- [ ] TP3 (SW): revisar pad superficial y acceso. Existe `C:\Program Files\KiCad\10.0\share\kicad\footprints\TestPoint.pretty\TestPoint_Pad_D2.0mm.kicad_mod`. No requiere datasheet, MPN ni modelo 3D comercial. Sin cambios en PCB.
- [ ] TP4 (GATE): revisar pad superficial y acceso. Existe `C:\Program Files\KiCad\10.0\share\kicad\footprints\TestPoint.pretty\TestPoint_Pad_D2.0mm.kicad_mod`. No requiere datasheet, MPN ni modelo 3D comercial. Sin cambios en PCB.
- [ ] TP5 (VOUT): revisar pad superficial y acceso. Existe `C:\Program Files\KiCad\10.0\share\kicad\footprints\TestPoint.pretty\TestPoint_Pad_D2.0mm.kicad_mod`. No requiere datasheet, MPN ni modelo 3D comercial. Sin cambios en PCB.
- [ ] TP6 (ISENSE): revisar pad superficial y acceso. Existe `C:\Program Files\KiCad\10.0\share\kicad\footprints\TestPoint.pretty\TestPoint_Pad_D2.0mm.kicad_mod`. No requiere datasheet, MPN ni modelo 3D comercial. Sin cambios en PCB.
- [ ] TP7 (SD): revisar pad superficial y acceso. Existe `C:\Program Files\KiCad\10.0\share\kicad\footprints\TestPoint.pretty\TestPoint_Pad_D2.0mm.kicad_mod`. No requiere datasheet, MPN ni modelo 3D comercial. Sin cambios en PCB.
- [ ] TP8 (NTRIP): revisar pad superficial y acceso. Existe `C:\Program Files\KiCad\10.0\share\kicad\footprints\TestPoint.pretty\TestPoint_Pad_D2.0mm.kicad_mod`. No requiere datasheet, MPN ni modelo 3D comercial. Sin cambios en PCB.
- [ ] TP9 (MCU_PWM): revisar pad superficial y acceso. Existe `C:\Program Files\KiCad\10.0\share\kicad\footprints\TestPoint.pretty\TestPoint_Pad_D2.0mm.kicad_mod`. No requiere datasheet, MPN ni modelo 3D comercial. Sin cambios en PCB.

## Recuperación de documentación de candidatos existentes

|Ref|URL oficial o estado|Comprobación|
|---|---|---|
|U1|https://www.infineon.com/assets/row/public/documents/24/49/infineon-ir2110-datasheet-en.pdf|SOIC16 ancho; comprobar tabla DIP14/SOIC16|
|U3|https://www.ti.com/lit/ds/symlink/sn74hct14.pdf|SOIC14 D; paso 1.27; cuerpo 8.65 x 3.9 nominal|
|U4|https://www.ti.com/lit/ds/symlink/sn74hct00.pdf|SOIC14 D; paso 1.27; cuerpo 8.65 x 3.9 nominal|
|U5|https://www.ti.com/lit/ds/symlink/lm393.pdf|SOIC8 D; comprobar sufijo B y rango térmico I|
|U6|https://www.ti.com/lit/ds/symlink/ina180.pdf|SOT23-5 DBV; variante A1, ganancia 20 V/V|
|Q1|https://www.umw-ic.com/static/pdf/a2d981f02a82712386b830ebbbca8b43.pdf|PDF fabricante hallado; confrontar revisión con C5199867.pdf; NO usar especificación Infineon para UMW|
|Q2|https://www.jscj-elec.com/gallery/file/MMBT3904%20SOT-23V2.pdf|SOT23; cotejar revisión y fabricante; no deducir numeración de TO92|

- [ ] L1/L2: obtener datasheet XR y plano mecánico, DCR, pérdidas y saturación. El catálogo publica 330 uH/3.2 A/6.5 A, montaje Wave; no se encontró SMD aprobado.
- [ ] C1/C2: obtener ficha oficial MZR para MPN exacto; confirmar vigencia y rizado a 10 kHz.
- [ ] C4/C5: obtener ficha oficial BXJ; comprobar ESR/rizado y montaje Wave versus reflow.
- [ ] RS1: ficha oficial TA-I exacta, potencia/derating/TCR y geometría Kelvin.
- [ ] D2: ficha oficial ShunYe US1G, recuperación/Vf/fugas a las corrientes del bootstrap.
- [ ] U2: confirmar revisión/sufijo 78M05 UMW y consumo térmico; PDF familiar local disponible.

