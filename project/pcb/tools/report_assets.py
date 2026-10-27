#!/usr/bin/env python3
"""Create vector connectivity and wiring views from the reviewed design."""
from pathlib import Path
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from design import PARTS

OUT=Path(__file__).resolve().parents[1]/'release/report-assets'
OUT.mkdir(exist_ok=True)
parts={p['ref']:p for p in PARTS}
for ref, pins in {'Q1':{'1':'GATE','2':'VIN','3':'SW'},'L1':{'1':'SW','2':'LMID'},
                 'L2':{'1':'LMID','2':'IP'},'RS1':{'1':'IP','2':'VOUT'},
                 'D1':{'1':'SW','2':'GND'},'C4':{'1':'VOUT','2':'GND'},
                 'C5':{'1':'VOUT','2':'GND'}}.items():
    assert parts[ref]['pins']==pins, f'Update diagram connectivity: {ref}'
plt.rcParams.update({'font.size':11,'pdf.fonttype':42})
def canvas(w,h):
    fig,ax=plt.subplots(figsize=(w,h)); ax.set(xlim=(0,w),ylim=(0,h)); ax.axis('off');return fig,ax
def box(ax,x,y,w,h,text):
    ax.add_patch(Rectangle((x,y),w,h,facecolor='#eef3f6',edgecolor='#25485b',lw=1))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center')
def line(ax,coords): ax.plot(*zip(*coords),color='#25485b',lw=1.2)
def save(fig,name):
    fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight',pad_inches=.08)
    fig.savefig(OUT/(name+'.png'),dpi=180,bbox_inches='tight',pad_inches=.08)
    plt.close(fig)
fig,ax=canvas(12,7)
ax.text(6,6.7,'PLACA IR2110 · CONECTIVIDAD DE POTENCIA',ha='center',weight='bold')
for x,w,label in [(0.1,1.2,'J1\n12 V'),(2,1.4,'Q1\nIRFZ44N'),(4.3,1.5,'L1\n330 μH'),(6.4,1.5,'L2\n330 μH'),(8.6,1.4,'RS1\n0.05 Ω'),(10.7,1.2,'J2\nVOUT')]:
    box(ax,x,5,w,.8,label)
for a,b,net in [(1.3,2,'VIN'),(3.4,4.3,'SW'),(5.8,6.4,'LMID'),(7.9,8.6,'IP'),(10,10.7,'VOUT')]:
    line(ax,[(a,5.4),(b,5.4)]);ax.text((a+b)/2,5.85,net,ha='center',fontsize=9)
box(ax,3.4,3.1,1.5,1,'D1 1N5822\nK: SW\nA: GND')
line(ax,[(3.8,5.4),(3.8,4.1)]);line(ax,[(4.1,3.1),(4.1,2.7),(11.4,2.7)])
box(ax,9.9,3.1,2,1,'C4 ∥ C5\n10 + 10 μF')
line(ax,[(10.4,5.4),(10.4,4.1)]);line(ax,[(10.9,3.1),(10.9,2.7)])
ax.text(11.6,2.7,'GND',ha='center',va='top')
box(ax,.1,1.2,2.2,1.2,"PWM d′ → HCT14\nHIN = 1 − d′\nIR2110: HO → R1")
line(ax,[(2.3,1.8),(2.7,1.8),(2.7,5)])
ax.text(2.85,4.6,'GATE',fontsize=9)
box(ax,4.1,1.1,3.4,1.1,'INA180: IN+ = IP\nIN− = VOUT; OUT = ISENSE')
box(ax,8.3,1.1,3.5,1.1,'VOUT → 3 kΩ → VSENSE\nVSENSE → 1 kΩ ∥ 1 nF → GND')
ax.text(6,.45,'Bootstrap: VIN → UF4004 → BOOT; 1 μF entre BOOT y SW.\nVista funcional: desacoplos, enclavamiento y todos los pines en el esquema completo.',ha='center',fontsize=10)
save(fig,'power-summary')

fig,ax=canvas(10,6.2)
box(ax,3.5,2,3,2.5,'PCB BUCK\nJ1: VIN / GND\nJ2: VOUT / GND\nJ3: control y sensor')
box(ax,.1,4.5,2.5,1.2,'Fuente 12 V limitada\nFusible externo 2 A')
box(ax,7.4,4.5,2.5,1.2,'Carga externa\n6 / 7.2 / 4.8 Ω')
box(ax,.1,.2,2.5,1.3,'STM32 Blue Pill\nexterno\n5 V desde PCB')
box(ax,7.4,.2,2.5,1.3,'ST-Link + USB-UART\nexternos\nlógica 3.3 V')
line(ax,[(2.6,5.1),(3.9,5.1),(3.9,4.5)])
line(ax,[(6.1,4.5),(6.1,5.1),(7.4,5.1)])
line(ax,[(1.35,1.5),(1.35,2.8),(3.5,2.8)])
line(ax,[(2.6,.8),(7.4,.8)])
ax.text(5,.98,'SWD: PA13/14 · UART: PA9/10',ha='center',fontsize=9)
ax.text(5,5.95,'CONEXIONES PREVISTAS · MONTAJE PENDIENTE',ha='center',weight='bold')
ax.text(6.8,2.65,'J3 → MCU\n3: PA8 PWM\n4: PB0 RUN\n5: PB1 RESET\n6: PB10 fallo\n7: PA0 ADC\n9: 3.3 V',fontsize=9,va='center')
ax.text(5,1.72,'J3: 1 = 5 V; 2, 8 y 10 = GND',ha='center',fontsize=9)
save(fig,'wiring')
