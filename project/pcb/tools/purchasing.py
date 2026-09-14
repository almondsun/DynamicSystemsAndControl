#!/usr/bin/env python3
"""Build a transparent purchasing allowance from the actual board BOM."""
import csv,json
from design import ROOT,PARTS
shop='https://www.didacticaselectronicas.com/shop/'
observed={
 'U1':(10890.88,shop+'ir2110-driver-mosfet-ir2110-500v-2a-6383'),
 'D1':(404.60,shop+'1n5822-tp-diodo-schottky-40v-3a-do-201ad-4261'),
 'L1':(3871.07,shop+'bob-v-65125-330uh-bobina-toroidal-vertical-de-330uh-5a-24437'),
 'L2':(3871.07,shop+'bob-v-65125-330uh-bobina-toroidal-vertical-de-330uh-5a-24437')}
estimates={'Q1':1800,'RS1':2500,'U2':1500,'U3':1800,'U4':1800,'U5':1200,'U6':6500,'Q2':300,'D2':400,'J1':1500,'J2':1500,'J3':700,'C6':800}
rows=[]
for p in PARTS:
    ref=p['ref'];spare=1 if ref in {'Q1','D1','U1','U6','RS1','C4','C5'} else 0
    price,source=observed.get(ref,(estimates.get(ref,100 if ref.startswith('R') else 50 if ref.startswith('TP') else 1000 if ref in {'C1','C2','C4','C5','C11'} else 250),'pending supplier quote'))
    status='observed 2026-09-14; reconfirm' if ref in observed else 'planning allowance; NOT a quote'
    if ref.startswith('L'):status+='; dimensions/Isat unqualified'
    if ref in {'C4','C5'}:status+='; exact MPN/ripple rating unqualified'
    rows.append(dict(group='PCB',references=ref,item=p['value'],installed=1,spares=spare,buy_qty=1+spare,unit_COP=price,total_COP=round(price*(1+spare),2),price_status=status,source=source,qualification=p['note']))
extras=[
 ('controller','MCU','STM32F103C8T6 USB-C D-STM32F103C8T6-C',1,1,10890.88,shop+'d-stm32f103c8t6-c-tarjeta-de-desarrollo-stm32f103c8t6-usb-tipo-c-39492','observed; verify clone, flash, crystal and ADC'),
 ('controller','SWD','Waveshare WS-10053 ST-LINK V2 mini',1,0,39259.29,shop+'ws-10053-programador-y-compilador-stm-st-link-v2-mini-10292','observed; verify connector/power pin'),
 ('controller','UART','USB-UART 3.3V logic, TX/RX/GND',1,0,9000,'pending supplier quote','allowance; verify logic levels, not only power jumper'),
 ('controller','CABLE','Polarized J3 harness and SWD/UART jumpers',1,0,4000,'pending supplier quote','allowance'),
 ('load','RL1 RL2','12 ohm 10 W ceramic',2,0,963.90,shop+'r-12r-10w-resistencia-ceramica-12r-10w-35841','observed price; insufficient observed stock'),
 ('load','RL3','1.2 ohm 5 W ceramic',1,0,1500,'pending supplier quote','allowance'),
 ('load','RL4 RL5','12 ohm 5 W ceramic',2,0,1200,'pending supplier quote','allowance'),
 ('load','S1 S2','Switch >=3A at 24V DC',2,0,3500,'pending supplier quote','allowance; verify DC rating'),
 ('load','WIRING','Insulated load-bank wiring and supports',1,0,4000,'pending supplier quote','allowance'),
 ('PCB','F1','External fast fuse 2A 5x20 mm',1,2,500,'pending supplier quote','allowance; mandatory external input fuse'),
 ('PCB','FH1','Inline insulated 5x20 fuseholder with leads',1,0,3000,'pending supplier quote','allowance'),
 ('PCB','MISC','DIP sockets, insulating board support and coil fasteners',1,0,6000,'pending supplier quote','allowance')]
for group,ref,item,n,spare,price,url,status in extras:
    rows.append(dict(group=group,references=ref,item=item,installed=n,spares=spare,buy_qty=n+spare,unit_COP=price,total_COP=round(price*(n+spare),2),price_status=status,source=url,qualification='Verify received component before assembly'))
with (ROOT/'purchasing.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
subtotal={g:round(sum(r['total_COP'] for r in rows if r['group']==g),2) for g in ['PCB','controller','load']}
planned=round(sum(subtotal.values())+80000+25000,2)
summary={'currency':'COP','date':'2026-09-14','status':'Mixed observed item prices and unquoted allowances; delivered total unknown','component_subtotals':subtotal,'pcb_and_international_shipping_allowance':80000,'domestic_shipping_allowance':25000,'estimated_before_contingency':planned,'remaining_from_350000_target':round(350000-planned,2),'target_per_student':87500,'students':4}
(ROOT/'budget.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
