# Primera cotización JLCPCB

**Alcance: PCB + 41 SMD de cara superior. Pendiente de revisión; no es una liberación de fabricación.** Quedan fuera siete THT cuya selección/montaje no está resuelta. No se hicieron pedidos ni pagos.

1. Subir `gerbers.zip` en la página de cotización de PCB. El ZIP contiene únicamente nueve Gerbers, dos Excellon y el job Gerber.
2. Confirmar FR-4, **2 capas, 105,55 × 81,05 mm, 1,6 mm**, cobre de 35 µm (1 oz) por cara según el stackup CAD. Confirmar dimensiones detectadas y contorno único. Acabado, color, cantidad y condiciones comerciales deben elegirse para la cotización: el CAD no fija un acabado final aprobado. Registrar esas selecciones junto al precio; no confundirlas con requisitos eléctricos validados.
3. Abrir la previsualización Gerber. Revisar ambas caras, máscaras, pasta, contorno y taladros, especialmente J1/J2/J3, Q1 y L1/L2. La validación automática de coordenadas no reemplaza esta revisión CAM. B.Paste y B.SilkS están vacías; no hay ensamblaje inferior.
4. Activar ensamblaje **solo superior**. Comprobar si la modalidad disponible admite las 24 selecciones comerciales y sus posibles costes de componentes extendidos o utillaje. No asumir que todos son compatibles con la modalidad económica.
5. Subir `bom_jlcpcb.csv`: deben reconocerse **24 líneas agrupadas / 41 designators**. Confirmar cada MPN, código LCSC y encapsulado contra `assembly_inventory.md`. No aceptar sustituciones automáticas. Stock PCBA, precio y disponibilidad están **NO VERIFICADOS** hasta esta pantalla.
6. Subir `cpl_jlcpcb.csv`: **41 colocaciones**, unidades mm, capa `top`. Se conserva el origen absoluto de KiCad (X positivo, Y negativo); no aplicar espejado o desplazamientos independientes. Si el portal no alinea automáticamente, revisar el mismo origen en Gerber y CPL antes de continuar.
7. Revisar **todas** las colocaciones en el visualizador de ensamblaje. Prioridad: pin 1 de U1–U6; cátodo de D1; terminales de Q2; polaridad de C1/C2/C4/C5 y geometría de RS1. Las rotaciones CPL son las reales de KiCad normalizadas a 0–360°, sin correcciones de máquina adivinadas. No aprobar mientras el visualizador muestre un giro o pinout incorrecto.
8. Confirmar C6 **CL31B225KBHNNNE / C50254**, R10 **30,9 kΩ**, C16 **220 nF** y divisor R14/R15 **15 kΩ / 2,2 kΩ**. Resolver la calificación de los lands personalizados antes de ordenar.
9. Comprobar exclusiones explícitas: **J1/J2/J3, L1/L2, Q1 y D2** pendientes THT; **TP1–TP9** son pads sin pieza añadida; NUCLEO-L432KC y carga son externas. La cotización SMT no incluye estos siete THT ni permite afirmar que la placa ensamblada estará completa. Obtener selección comercial compatible y cotización separada de compra/montaje manual o servicio THT, sin sustituir huellas actuales.
10. Revisar las cinco advertencias DRC y dos ERC del informe. Resolver o aceptar técnicamente antes de fabricar; no desactivar reglas para ocultarlas. Los campos CAD de aprobación eléctrica siguen pendientes.
11. Obtener el precio y registrar abajo. **Detenerse antes de confirmar el pedido o autorizar pagos.**

| Dato | Resultado a completar en el portal |
|---|---|
| Fecha / moneda / número de cotización | Pendiente |
| Cantidad de PCB / cantidad ensamblada | Pendiente |
| Acabado / máscara / serigrafía | Pendiente |
| Servicio de ensamblaje elegido | Pendiente |
| PCB / componentes / colocación / utillaje | Pendiente |
| Envío / impuestos / total | Pendiente |
| Coste separado de los siete THT y externos | Pendiente |
| Stock y rotaciones comprobados por | Pendiente |

Referencia de formato: [guía oficial JLCPCB para BOM y centroid de KiCad](https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad). Este paquete usa exportación nativa y conversión CSV local, sin modificar el diseño.
