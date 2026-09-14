#!/usr/bin/env python3
"""Capture a real UART experiment. Requires pyserial; never synthesizes lab data."""
import argparse,csv,io,time
from pathlib import Path
def decode(lines):
    start=lines.index('tick_100us,vo_mV,vref_mV,dprime_10000,mode')
    end=lines.index('END',start)
    rows=list(csv.DictReader(io.StringIO('\n'.join(lines[start:end]))))
    if len(rows)!=512:raise ValueError(f'Expected 512 records, received {len(rows)}')
    values=[{k:int(v) for k,v in r.items()} for r in rows]
    ticks=[r['tick_100us'] for r in values]
    if any(b-a!=1 for a,b in zip(ticks,ticks[1:])):raise ValueError('Dropped/nonmonotonic samples')
    if any(r['mode'] not in (2,3) or r['vo_mV']==65535 for r in values):raise ValueError('Capture contains startup, off or fault state')
    return values
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port',required=True);p.add_argument('--case',choices=['open_up','open_down','ref_up','ref_down'],required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--load-ohm',type=float,required=True)
    a=p.parse_args()
    if a.output.exists():p.error('Output already exists; preserve original measurements')
    if not 0<a.load_ohm<100:p.error('Supply the measured load in ohms')
    import serial
    initial,event={'open_up':('a','b'),'open_down':('a','c'),'ref_up':('6','7'),'ref_down':('6','5')}[a.case]
    with serial.Serial(a.port,115200,timeout=1,write_timeout=1) as s:
        def cmd(c):
            s.write(c.encode());s.flush()
            for _ in range(10):
                line=s.readline().decode('ascii').strip()
                if line=='OK':return
                if line=='REJECT':raise RuntimeError(f'Firmware rejected {c}')
            raise TimeoutError(f'No acknowledgement for {c}')
        try:
            s.reset_input_buffer();cmd('s');cmd('r');cmd(initial);time.sleep(1.1)
            s.write(b'i');state=s.readline().decode('ascii').strip().split(',')
            wanted='2' if a.case.startswith('open') else '3'
            if len(state)!=7 or state[:3]!=['STATE',wanted,'0']:raise RuntimeError(f'Not ready: {state}')
            cmd('v');time.sleep(.010);cmd(event);time.sleep(.060)
            s.write(b'd');s.flush();lines=[]
            deadline=time.monotonic()+8
            while time.monotonic()<deadline:
                line=s.readline().decode('ascii').strip();lines.append(line)
                if line=='END':break
            rows=decode(lines)
            a.output.parent.mkdir(parents=True,exist_ok=True)
            raw=a.output.with_suffix('.uart.txt')
            with raw.open('x') as f:f.write('\n'.join(lines)+'\n')
            first=rows[0]['tick_100us']
            with a.output.open('x',newline='') as f:
                w=csv.writer(f);w.writerow(['time_s','voltage_V','dprime','load_ohm','reference_V'])
                for r in rows:w.writerow([(r['tick_100us']-first)*.0001,r['vo_mV']*.001,r['dprime_10000']*.0001,a.load_ohm,r['vref_mV']*.001])
            print(a.output)
        finally:
            s.write(b's');s.flush()
if __name__=='__main__':main()
