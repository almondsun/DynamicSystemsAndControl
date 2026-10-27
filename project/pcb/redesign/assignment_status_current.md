# Estado de asignación vigente tras la actualización NUCLEO

2026-10-26. Este resumen sustituye los recuentos históricos de [assignment_report.md](assignment_report.md), que se conserva como evidencia de la primera fase. MPN y huellas de la netlist vigente; ver [design_changes.md](design_changes.md) para decisiones aceptadas y conectividad autorizada.

De **57 referencias**, **41 tienen candidato SMD asignado**, incluidas huellas provisionales. **4 requieren intervención para una sustitución SMD segura: L1, L2, Q1 y D2**. **12 conectores/puntos de prueba siguen THT**, incluido J3 actualizado a interfaz NUCLEO con selección mecánica provisional. No se cuenta la NUCLEO externa como componente ensamblado.

Las 57 referencias requieren revisión del conjunto. Las 41 asignaciones no son aprobaciones eléctricas; todos los pasivos mantienen pendiente su aprobación integral según auditoría. Las clases y reglas PCB tampoco alteran ese estado.

| Referencia | MPN | Símbolo | Footprint | Cambio realizado | Validación | Pendiente |
|---|---|---|---|---|---|---|
| C1 | Panasonic 25SVPF100M | Buck:C1 | Buck_SMD:PCAP_SVP_E7_PAN | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| C2 | Panasonic 25SVPF100M | Buck:C2 | Buck_SMD:PCAP_SVP_E7_PAN | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| C3 | Yageo CC0603KRX7R9BB104 | Buck:C3 | Capacitor_SMD:C_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| C4 | Panasonic 50SVF10M | Buck:C4 | Buck_SMD:CAP_SVF_C6_PAN | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| C5 | Panasonic 50SVF10M | Buck:C5 | Buck_SMD:CAP_SVF_C6_PAN | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| D1 | SS34 | Buck:D1 | Diode_SMD:D_SMA | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| J1 | TB002-500-02BE | Buck:J1 | TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal | THT conservado | CAD comprobado; sin aprobación integral | Montaje/MPN/mecánica pendientes |
| J2 | TB002-500-02BE | Buck:J2 | TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal | THT conservado | CAD comprobado; sin aprobación integral | Montaje/MPN/mecánica pendientes |
| L1 | Murata 60B334C | Buck:L1 | Buck:Inductor_25mm_P10mm_VERIFY | Sin sustitución SMD segura | CAD comprobado; sin aprobación integral | MPN/land y validación pendientes |
| L2 | Murata 60B334C | Buck:L2 | Buck:Inductor_25mm_P10mm_VERIFY | Sin sustitución SMD segura | CAD comprobado; sin aprobación integral | MPN/land y validación pendientes |
| Q1 | IRFZ44NS | Buck:Q1 | Package_TO_SOT_THT:TO-220-3_Vertical | Sin sustitución SMD segura | CAD comprobado; sin aprobación integral | MPN/land y validación pendientes |
| RS1 | TA-I RLP25FEER050 | Buck:RS1 | Resistor_SMD:R_2512_6332Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| C6 | CL31B225KBHNNNE | Buck:C6 | Capacitor_SMD:C_1206_3216Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| C7 | Yageo CC0603KRX7R9BB104 | Buck:C7 | Capacitor_SMD:C_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| C8 | Yageo CC0603KRX7R9BB104 | Buck:C8 | Capacitor_SMD:C_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| C9 | Samsung CL21B334KBFNNNE | Buck:C9 | Capacitor_SMD:C_0805_2012Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| C10 | Yageo CC0603KRX7R9BB104 | Buck:C10 | Capacitor_SMD:C_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| C11 | Samsung CL21A106KAYNNNE | Buck_Redesign:CL21A106KAYNNNE | Capacitor_SMD:C_0805_2012Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| C12 | Yageo CC0603KRX7R9BB104 | Buck:C12 | Capacitor_SMD:C_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| D2 | US1G | Buck:D2 | Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal | Sin sustitución SMD segura | CAD comprobado; sin aprobación integral | MPN/land y validación pendientes |
| R1 | UNI-ROYAL 0805W8F100JT5E | Buck:R1 | Resistor_SMD:R_0805_2012Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| R2 | UNI-ROYAL 0603WAF1002T5E | Buck:R2 | Resistor_SMD:R_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| R3 | UNI-ROYAL 0603WAF1002T5E | Buck:R3 | Resistor_SMD:R_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| R4 | UNI-ROYAL 0603WAF1001T5E | Buck:R4 | Resistor_SMD:R_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| U1 | IR2110STRPBF | Buck:U1 | Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| U2 | 78M05 | Buck:U2 | Package_TO_SOT_SMD:TO-252-2 | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| U3 | SN74HCT14DR | Buck:U3 | Buck_SMD:D14 | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| C13 | Yageo CC0603KRX7R9BB104 | Buck:C13 | Capacitor_SMD:C_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| C14 | Yageo CC0603KRX7R9BB104 | Buck:C14 | Capacitor_SMD:C_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| C15 | Yageo CC0603KRX7R9BB104 | Buck:C15 | Capacitor_SMD:C_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| C16 | CC0603KRX7R9BB224 | Buck:C16 | Capacitor_SMD:C_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| Q2 | MMBT3904 | Buck_Redesign:MMBT3904_C20526 | Package_TO_SOT_SMD:SOT-23 | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| R5 | UNI-ROYAL 0603WAF1002T5E | Buck:R5 | Resistor_SMD:R_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| R6 | UNI-ROYAL 0603WAF1002T5E | Buck:R6 | Resistor_SMD:R_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| R7 | UNI-ROYAL 0603WAF4701T5E | Buck:R7 | Resistor_SMD:R_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| R8 | UNI-ROYAL 0603WAF1502T5E | Buck:R8 | Resistor_SMD:R_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| R9 | UNI-ROYAL 0603WAF1002T5E | Buck:R9 | Resistor_SMD:R_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| R10 | CRCW060330K9FKEA | Buck:R10 | Resistor_SMD:R_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| R11 | UNI-ROYAL 0603WAF1002T5E | Buck:R11 | Resistor_SMD:R_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| R12 | UNI-ROYAL 0603WAF1002T5E | Buck:R12 | Resistor_SMD:R_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| R13 | UNI-ROYAL 0603WAF1002T5E | Buck:R13 | Resistor_SMD:R_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| U4 | SN74HCT00DR | Buck:U4 | Buck_SMD:D14 | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| U5 | LM393BIDR | Buck:U5 | Buck_SMD:D0008A-MFG | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| U6 | INA180A1IDBVR | Buck:U6 | Buck_SMD:DBV0005A_N | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| C17 | Fenghua 0603CG102J500NT | Buck:C17 | Capacitor_SMD:C_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| J3 | TBD keyed IDC header 2x5 2.54mm | Buck_Redesign:J3_NUCLEO_L432KC | Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical | Interfaz NUCLEO y huella IDC provisional | CAD comprobado; sin aprobación integral | Montaje/MPN/mecánica pendientes |
| R14 | 0603WAF1502T5E | Buck:R14 | Resistor_SMD:R_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| R15 | 0603WAF2201T5E | Buck:R15 | Resistor_SMD:R_0603_1608Metric | Candidato SMD asignado | CAD comprobado; sin aprobación integral | Validación eléctrica/mecánica; ver matriz e informes |
| TP1 | No definido | Buck:TP1 | TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm | THT conservado | CAD comprobado; sin aprobación integral | Montaje/MPN/mecánica pendientes |
| TP2 | No definido | Buck:TP2 | TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm | THT conservado | CAD comprobado; sin aprobación integral | Montaje/MPN/mecánica pendientes |
| TP3 | No definido | Buck:TP3 | TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm | THT conservado | CAD comprobado; sin aprobación integral | Montaje/MPN/mecánica pendientes |
| TP4 | No definido | Buck:TP4 | TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm | THT conservado | CAD comprobado; sin aprobación integral | Montaje/MPN/mecánica pendientes |
| TP5 | No definido | Buck:TP5 | TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm | THT conservado | CAD comprobado; sin aprobación integral | Montaje/MPN/mecánica pendientes |
| TP6 | No definido | Buck:TP6 | TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm | THT conservado | CAD comprobado; sin aprobación integral | Montaje/MPN/mecánica pendientes |
| TP7 | No definido | Buck:TP7 | TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm | THT conservado | CAD comprobado; sin aprobación integral | Montaje/MPN/mecánica pendientes |
| TP8 | No definido | Buck:TP8 | TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm | THT conservado | CAD comprobado; sin aprobación integral | Montaje/MPN/mecánica pendientes |
| TP9 | No definido | Buck:TP9 | TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm | THT conservado | CAD comprobado; sin aprobación integral | Montaje/MPN/mecánica pendientes |
