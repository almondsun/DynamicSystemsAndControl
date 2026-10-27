#!/usr/bin/env python3
"""Single source of connectivity, exact package pin numbers and placement.

This is an original educational design. Inductor geometry is a procurement
assumption, explicitly blocking fabrication until checked against actual parts.
"""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PARTS = []
def part(ref, value, footprint, xy, pins, section, note='', rotation=0):
    PARTS.append(dict(ref=ref, value=value, footprint=footprint, xy=xy,
                      pins={str(k):v for k,v in pins.items()}, section=section,
                      note=note, rotation=rotation))
R='Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal'
C='Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm'
E='Capacitor_THT:CP_Radial_D6.3mm_P2.50mm'
D='Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal'
T='TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal'
def r(ref,value,x,y,a,b,section=3): part(ref,value,R,(x,y),{1:a,2:b},section)
def c(ref,value,x,y,a,b,section=1): part(ref,value,C,(x,y),{1:a,2:b},section)
part('J1','12V FUSED INPUT',T,(17,18),{1:'VIN',2:'GND'},1,'External 2A fast fuse; current-limited laboratory supply')
part('Q1','IRFZ44N TO-220', 'Package_TO_SOT_THT:TO-220-3_Vertical',(40,19),{1:'GATE',2:'VIN',3:'SW'},1,'Gate/drain/source; metal tab VIN')
part('D1','1N5822 40V 3A','Diode_THT:D_DO-201AD_P15.24mm_Horizontal',(49,28),{1:'SW',2:'GND'},1,'Pin 1 cathode band, pin 2 anode',180)
for ref,x,n1,n2 in [('L1',70,'SW','LMID'),('L2',96,'LMID','IP')]:
    part(ref,'330uH >=3A Isat VERIFY','Buck:Inductor_25mm_P10mm_VERIFY',(x,23),{1:n1,2:n2},1,'Check actual dimensions, DCR and saturation before ordering PCB')
part('RS1','0.050R 1% 1W','Resistor_SMD:R_2512_6332Metric',(92,41),{1:'IP',2:'VOUT'},1,'Kelvin sense at pads; CRCW2512 0R050 or verified equivalent')
part('J2','LOAD + / -',T,(101,51),{1:'VOUT',2:'GND'},1)
for ref,x,y in [('C1',20,28),('C2',29,20)]:
    part(ref,'100uF 25V', 'Capacitor_THT:CP_Radial_D8.0mm_P3.50mm',(x,y),{1:'VIN',2:'GND'},1,'Input bulk; positive pin 1')
c('C3','100nF 50V',20,36,'VIN','GND')
for ref,x in [('C4',96),('C5',104)]:
    part(ref,'10uF 35V low ESR',E,(x,62),{1:'VOUT',2:'GND'},1,'Exact 20uF total target; verify ripple rating and measured capacitance')
part('U1','IR2110PBF DIP14','Package_DIP:DIP-14_W7.62mm',(48,48),
     {1:None,2:'GND',3:'VIN',4:None,5:'SW',6:'BOOT',7:'HO',8:None,9:'+5V',10:'HIN',11:'SD',12:'GND',13:'GND',14:None},2,rotation=180)
part('D2','UF4004',D,(25,43),{1:'BOOT',2:'VIN'},2,'Bootstrap: cathode to BOOT')
c('C6','1uF 50V X7R',52,37,'BOOT','SW',2)
c('C7','100nF 50V',51,46,'VIN','GND',2)
c('C8','100nF 50V',31,34,'+5V','GND',2)
part('R1','10R',R,(53,30),{1:'HO',2:'GATE'},2,rotation=90)
r('R2','10k',39,23,'GATE','SW',2)
part('U2','L7805CV','Package_TO_SOT_THT:TO-220-3_Vertical',(17,48),{1:'VIN',2:'GND',3:'+5V'},2,'Input / ground / output; evaluate dissipation')
c('C9','330nF 50V',16,40,'VIN','GND',2)
c('C10','100nF 50V',15,60,'+5V','GND',2)
part('C11','10uF 25V',E,(25,57),{1:'+5V',2:'GND'},2)
part('U3','SN74HCT14N','Package_DIP:DIP-14_W7.62mm',(30,73),
     {1:'DPRIME',2:'HIN',3:'GND',4:None,5:'GND',6:None,7:'GND',8:None,9:'GND',10:None,11:'GND',12:None,13:'GND',14:'+5V'},2,'HCT TTL thresholds; do not substitute HC at 5V')
r('R3','10k',19,69,'DPRIME','+5V',2)
r('R4','1k',19,76,'MCU_PWM','DPRIME',2)
c('C12','100nF',31,68,'+5V','GND',2)
part('U4','SN74HCT00N','Package_DIP:DIP-14_W7.62mm',(53,73),
     {1:'RESET',2:'NTRIP',3:'NRESET',4:'RUN',5:'NFAULT',6:'SD',7:'GND',8:'FAULT',9:'NTRIP',10:'NFAULT',11:'NFAULT',12:'NRESET',13:'FAULT',14:'+5V'},3,'Set-dominant NAND latch; SD = NOT(RUN AND NFAULT)')
c('C13','100nF',55,68,'+5V','GND',3)
r('R5','10k',41,94,'RUN','GND')
r('R6','10k',52,94,'RESET','GND')
r('R7','4.7k',65,88,'NTRIP','+5V')
part('U5','LM393P','Package_DIP:DIP-8_W7.62mm',(78,73),
     {1:'NTRIP',2:'ISENSE',3:'VREF',4:'GND',5:'VREF',6:'OVSENSE',7:'NTRIP',8:'+5V'},3,'Two open-collector outputs wired together; overcurrent OR overvoltage')
c('C14','100nF',78,67,'+5V','GND',3)
r('R8','15k 1%',65,57,'+5V','VREF')
r('R9','10k 1%',65,62,'VREF','GND')
c('C15','100nF',65,68,'VREF','GND',3)
r('R10','31k 1%',88,87,'VOUT','OVSENSE')
r('R11','10k 1%',88,94,'OVSENSE','GND')
part('U6','INA180A1IDBVR','Package_TO_SOT_SMD:SOT-23-5',(86,48),
     {1:'ISENSE',2:'GND',3:'IP',4:'VOUT',5:'+5V'},3,'Pinout A ONLY; gain 20 V/V; sense RS1 pads directly')
c('C16','100nF',79,54,'+5V','GND',3)
part('Q2','2N3904','Package_TO_SOT_THT:TO-92_Inline_Wide',(69,94),{1:'GND',2:'FB',3:'NFAULT_MCU'},3,'E/B/C pin order must match purchased manufacturer')
r('R12','10k',66,81,'FAULT','FB')
r('R13','10k',78,98,'+3V3','NFAULT_MCU')
r('R14','3k 1%',59,103,'VOUT','VSENSE',4)
r('R15','1k 1%',72,103,'VSENSE','GND',4)
c('C17','1nF',85,103,'VSENSE','GND',4)
part('J3','STM32 CABLE 2x5','Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical',(20,94),
     {1:'+5V',2:'GND',3:'MCU_PWM',4:'RUN',5:'RESET',6:'NFAULT_MCU',7:'VSENSE',8:'GND',9:'+3V3',10:'GND'},4,'Key/polarize cable; external Blue Pill not integrated')
for n,(net,x,y) in enumerate([('VIN',13,30),('GND',13,36),('SW',57,34),('GATE',54,19),('VOUT',104,72),('ISENSE',92,72),('SD',63,91),('NTRIP',77,88),('MCU_PWM',13,87)],1):
    part(f'TP{n}',net,'TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm',(x,y),{1:net},4)

if __name__ == '__main__':
    import json
    print(json.dumps(PARTS,indent=2))
