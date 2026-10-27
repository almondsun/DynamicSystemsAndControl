# Pendientes de reglas y layout

Esta lista complementa, sin sustituir, [open_issues.md](open_issues.md). Reglas configuradas, **layout no liberado**.

| Pendiente | Criterio antes de ruteo o fabricación |
|---|---|
| Saturn 8.48 sin interfaz controlable | Completar IPC-2152 para montaje y planos reales, Δ10/20 °C, mínimo de cobre contratado; revisar anchos |
| Stackup y metalizado | Confirmar cobre terminado mínimo, barril mínimo, tolerancias de vía/anillo y stackup del pedido; 30/15 µm son sensibilidades |
| Fallas y térmica de componentes | Acotar corriente/tiempo/SOA, saturación y recuperación del diodo; revisar U2, Q1, D1 y shunt |
| Mecánica vacía | Definir contorno, fijaciones, conector y arnés; validar alturas, courtyards y lands antes de colocar |
| L1/L2, Q1/D2 y RS1 | Resolver MPN/lands pendientes de migración; no propagar placeholders a ensamblaje |
| Bootstrap/ADC/backfeed | Cerrar cálculos y protección de alimentación/estado apagado según informes; no energizar con solo las reglas |
| Plano GND y Kelvin | Revisar retornos reales y corredores, sin plano partido bajo control; mantener SW alejado del sensado en ambas caras |
| Validación DRC futura | Después de colocar/rutear, ejecutar DRC y paridad; actualmente solo se comprobó soporte vacío y prueba aislada |
| NUCLEO/firmware | Inspeccionar SB17/SB18 y arnés físico; compilar no prueba estados seguros, PI ni temporización real |

No se generaron rutas de producción, Gerbers ni CPL. No se modificó el firmware original ni los archivos originales del PCB. La próxima decisión es revisión humana del esquemático, encapsulados y riesgos; esta entrega no la sustituye.
