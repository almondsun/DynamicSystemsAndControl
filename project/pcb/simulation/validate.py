#!/usr/bin/env python3
"""Run the isolated PCB estimate; never replace original course result files."""
import csv,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
OUT=REPO/'artifacts/buck-pcb-validation/simulation'
OUT.mkdir(parents=True,exist_ok=True)
exe=OUT/'simulate'
subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(HERE/'simulate.c'),str(REPO/'project/firmware/runtime.c'),str(REPO/'project/hardware/buck_control.c'),'-lm','-o',str(exe)],check=True)
results={}
for case in ['open_up','open_down','ref_up','ref_down','load_up','load_down']:
    path=OUT/(case+'.csv')
    run=subprocess.run([str(exe),case,'0.0000005',str(path)],check=True,text=True,capture_output=True)
    print(run.stdout,end='')
    rows=list(csv.DictReader(path.open()));data=[{k:float(v) for k,v in row.items()} for row in rows]
    tail=data[-50:]; final=sum(r['vo_V'] for r in tail)/len(tail)
    item={'final_vo_V':final,'source':'switched estimate; assumptions unmeasured','simulation_log':run.stdout.strip()}
    assert all(r['hardware_fault']==0 for r in data)
    if not case.startswith('open'):
        target=7 if case=='ref_up' else 5 if case=='ref_down' else 6
        err=abs(final-target);assert err<.020,(case,err)
        band=.020 if case.startswith('ref') else .12
        outside=[r['t_s'] for r in data if r['t_s']>=.01 and abs(r['vo_V']-target)>band]
        item.update(steady_error_V=err,settling_s_after_event=max(0,max(outside,default=.01)-.01+.0001))
    results[case]=item
subprocess.run([str(exe),'ref_up','0.00000025',str(OUT/'ref_up_half_dt.csv')],check=True)
def volts(p):return [float(r['vo_V']) for r in csv.DictReader(p.open())]
a,b=volts(OUT/'ref_up.csv'),volts(OUT/'ref_up_half_dt.csv')
delta=max(abs(x-y) for x,y in zip(a,b));assert delta<.02,delta
results['convergence_max_cycle_mean_difference_V']=delta
(OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n')
print('PASS: six scenarios, no simulated protection trips, PI final error <20mV, timestep convergence <20mV')
