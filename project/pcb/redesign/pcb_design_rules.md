# Reglas PCB Buck SMD para revisión — 2026-10-26

Reglas preliminares implementadas en [buck.kicad_pro](buck.kicad_pro), [buck.kicad_dru](buck.kicad_dru) y stackup en [buck.kicad_pcb](buck.kicad_pcb), KiCad 10.0.4, rama `Kicad-PCB`. La fase de migración terminó antes de esta fase: véase [design_changes.md](design_changes.md) y [estado de migración](validation/nucleo_update/migration_status.json). Los bloqueos de [open_issues.md](open_issues.md) siguen abiertos.

El PCB nuevo es un soporte de configuración **vacío**: 40 redes, cero footprints colocados, pistas, vías y zonas, sin contorno. No se copió el PCB original ni se inició layout. No está listo para rutear mientras falten decisiones eléctricas y mecánicas. Antes del layout habrá que actualizar desde el esquemático, comprobar las huellas pendientes y definir la mecánica aprobada.

## Stackup y fabricación

Objetivo: JLCPCB, FR-4, dos capas, 1.6 mm total nominal y cobre terminado 1 oz por cara (35 µm nominales). F.Cu: potencia, driver y señales locales; B.Cu: GND preferentemente continuo y auxiliares inevitables. PWM 10 kHz; ambiente 45 °C; incremento de pista objetivo 10 °C y comparación 20 °C. Los flancos del driver siguen siendo rápidos aunque PWM sea 10 kHz.

El modelo KiCad suma 35 µm F.Cu + 1.51 mm núcleo + 35 µm B.Cu + 10 µm por máscara = 1.60 mm. Núcleo, máscara, εr=4.5 y tanδ=0.02 son parámetros iniciales de modelado, pendientes del stackup suministrado; no equivalen a especificaciones garantizadas. Acabado superficial pendiente de selección; no se pidió control de impedancia.

La [capacidad vigente de JLCPCB](https://jlcpcb.com/capabilities/pcb-capabilities), consultada el 26-10-2026, publica FR-4, opción exterior 1 oz, espesor ≥1 mm ±10%, tolerancia de ancho ±20%, taladro +0.13/−0.08 mm, posición ±0.075 mm y metalizado de barril promedio 18 µm. Esto no garantiza un mínimo de cobre terminado ni de barril. El intervalo de placa nominal 1.6 mm es 1.44–1.76 mm. Deben confirmarse los mínimos contratados antes de cerrar térmica.

En esa misma tabla: pista/espacio para dos capas y 1 oz 0.10/0.10 mm; separación de agujeros de vía 0.20 mm; margen cobre a borde fresado 0.20 mm; diferencia diámetro vía/taladro mínima 0.10 mm, recomendada 0.15 mm. Las reglas del proyecto usan más margen. Los anillos de pads THT tienen requisitos distintos: recomendación radial 0.25 mm (mínimo 0.18 mm para dos capas 1 oz); revisar los conectores individualmente. No confundir este requisito con el de vías.

Se conserva la opción de dos capas: la topología y frecuencia permiten estudiarla si se minimiza el lazo caliente y se mantiene retorno continuo. Los dos inductores de hasta 23.5×27×20 mm y sus tierras no están resueltos, por lo que no se afirma que el área disponible alcance. Cuatro capas facilitarían retornos y distribución, pero no resuelven bootstrap/ADC ni encapsulados. Añadirían capas y procesos; la comparación de precio requiere cotizar igual tamaño, cantidad, acabado y ensamblaje. Sin esa cotización no se inventa un diferencial monetario ni se cambia a cuatro capas.

## Clases y redes reales

Anchos objetivo de ruteo; los límites globales y las reglas personalizadas se distinguen abajo. Las once redes `unconnected-(...)` corresponden a pines NC o salidas sin uso; permanecen en Default. [CSV completo](netclass_assignments.csv).

| Clase | Redes | Ancho mm | Clearance mm | Vía/taladro mm |
|---|---|---:|---:|---:|
| Default | 11 redes unconnected | 0.25 | 0.20 | 0.60/0.30 |
| POWER_INPUT | VIN | 3.00 | 0.25 | 0.80/0.40 |
| POWER_SWITCH | SW | 2.00 | 0.25 | 0.80/0.40 |
| POWER_INDUCTOR | LMID, IP | 2.00 | 0.25 | 0.80/0.40 |
| POWER_OUTPUT | VOUT | 2.00 | 0.25 | 0.80/0.40 |
| POWER_GND | GND | 0.25 | 0.20 | 0.80/0.40 |
| GATE_DRIVER | BOOT, HO, GATE | 0.50 | 0.25 | 0.60/0.30 |
| SUPPLY_5V | +5V | 0.50 | 0.25 | 0.80/0.40 |
| SUPPLY_3V3 | NUC_3V3 | 0.35 | 0.25 | 0.80/0.40 |
| ANALOG_SENSE | VSENSE, ISENSE, VREF, OVSENSE | 0.25 | 0.25 | 0.60/0.30 |
| DIGITAL_CONTROL | MCU_PWM, DPRIME, HIN, RUN, RESET, FAULT, FB, NFAULT, NFAULT_MCU, NRESET, NTRIP, SD, UART_TX, UART_RX | 0.25 | 0.20 | 0.60/0.30 |

POWER_GND=0.25 mm es solo el valor por defecto para retornos de señal: **no dimensiona el retorno de potencia**. Priorizar plano y corredores de cobre cortos, sin estrechamientos; un corredor comparable al camino de 1.47 A necesita evaluación equivalente a 2 mm. No se crearon redes AGND separadas ni un ancho mínimo uniforme para toda GND. IP y VOUT contienen derivaciones Kelvin hacia INA180: las ramas de medida deben ser independientes de la caída del camino de potencia, sin imponerles la anchura del tronco.

La entrada usa 3 mm frente a los 1.5 mm iniciales; SW, LMID, IP y VOUT usan 2 mm frente a 1.5 mm. Justificación y límites en [trace_via_calculations.md](trace_via_calculations.md). Los escapes cortos a pads pequeños requieren revisión de resistencia, calentamiento y longitud, sin alterar el land del fabricante para acomodar una pista.

## Restricciones implementadas

Mínimos globales: clearance 0.20 mm; pista 0.20 mm; diámetro de vía 0.60 mm; taladro 0.30 mm; anillo radial de vía 0.15 mm; agujero a cobre 0.25 mm; agujero a agujero 0.25 mm; cobre a borde 0.50 mm. Son elecciones de diseño compatibles con fabricación estándar, no mínimos declarados del fabricante. Preferir 0.25 mm o más entre redes y mayor margen de borde en potencia/conectores cuando haya espacio. Los pares de taladros de conectores requieren además comprobación específica de fabricación y de sus pads.

Ocho reglas personalizadas: prohibir microvías y vías ciegas/enterradas; impedir agujeros abiertos a menos de 0.20 mm del cobre de pads SMD, incluso misma red; courtyard a courtyard 0.25 mm; SW a ANALOG_SENSE 0.50 mm; avisar por vía en SW; avisar por vía en GATE_DRIVER; avisar ancho VIN menor de 3 mm fuera de courtyard; avisar SW/LMID menor de 2 mm fuera de courtyard. Los dos últimos son avisos deliberados para revisar escapes. No existe prueba automática de capacidad térmica del cobre. IP/VOUT y GND requieren revisión manual de sus troncos y derivaciones.

La separación SW–analógico no verifica acoplamiento entre caras: no colocar sensado debajo del área SW ni cortar su retorno. GATE, HO y BOOT deben ser cortas y próximas a sus retornos; mantener la conmutación en F.Cu siempre que sea viable. B.Cu continuo no significa extender cobre SW ni convertir el nodo conmutado en una antena.

Los anchos de netclass son objetivos del router; KiCad no los convierte por sí solo en mínimos DRC. Las restricciones explícitas se implementaron donde procede; consultar el [manual KiCad 10](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html). Los chequeos heredados de ERC y exclusiones DRC se conservaron. Se activaron avisos de courtyard ausente y tipo de footprint, y error de agujero a agujero. Persisten chequeos ignorados heredados que figuran en cada JSON; no se atribuye a este trabajo una auditoría integral de ellos.

## Mecánica y aprobación antes de layout

Revisar L1/L2 Murata: land real, altura 20 mm, volumen, acoplamiento y herramientas de montaje. U5 carece de courtyard acreditado; la advertencia ahora es visible y no se dibujó uno inventado. Revisar disipación y acceso del regulador, volumen y vida de electrolíticos, accesibilidad y pin 1 de J3/J1/J2, orientación de arnés y polaridades. C1/C2/C4/C5: pad positivo y marca de cuerpo; D1: cátodo pad 1/anodo pad 2 en la conectividad actual; confirmar siempre land y marcas del MPN elegido. Q1 y D2 todavía no tienen sustitución inequívoca. Una huella existente no aprueba un componente.

## Validaciones ejecutadas y límites

Exportación de netlist: código 0, 40 redes, sin diferencias de endpoints respecto al inicio de esta fase. ERC: 0 errores, 2 avisos de etiquetas UART de conector, código 5. Comprobación hash: 273 archivos originales protegidos sin cambios; cinco esquemáticos del rediseño y firmware preservados en esta fase. Rama sin cambio; no commits ni push.

La prueba DRC aislada generó 16 infracciones intencionales y 2 conexiones incompletas, código 5. Se verificó que detecta cinco reglas personalizadas (SW–analógico, vía en SMD, vía SW, vía gate y ancho VIN), geometría mínima de vías y courtyard ausente. Las ocho reglas se analizaron sin errores de sintaxis; las otras tres no tienen prueba negativa individual. La placa vacía produce únicamente `invalid_outline`, código 5; esto es esperado, **no un DRC aprobado** y tampoco una verificación de paridad PCB/esquemático.

El stackup sobrevivió a carga/guardado nativo aislado. El SDK guardó inicialmente ajustes por defecto al crear la placa; se restauraron y comprobaron las once clases antes del DRC final. La CLI emitió avisos de registro HKCU sin permiso y caché Fontconfig no escribible; no se ocultaron. Los informes de netlist/ERC/DRC sí se generaron y analizaron.

Saturn 8.48 instalado, pero sin ventana controlable: no se obtuvieron resultados de Saturn. La térmica, el barril mínimo, el montaje, el arnés, las protecciones y las huellas pendientes requieren revisión. Evidencia: [rules_status.json](validation/pcb_rules/rules_status.json) y [cálculos](validation/pcb_rules/calculations.json). No hay Gerbers, CPL ni ruteo nuevo.
