"""Reproducible PWM and transistor-circuit validation; no experimental data.

Run with --matlab-results artifacts/<run> --output artifacts/<new-run>.
The ngspice executable is supplied explicitly or discovered on PATH.
"""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess

import numpy as np
from scipy.linalg import expm
from scipy.integrate import cumulative_trapezoid
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
TS = 1e-4
CASES = {'open_up': (6, 6, .6), 'open_down': (6, 6, .4),
         'ref_up': (7, 6, None), 'ref_down': (5, 6, None),
         'load_up': (6, 7.2, None), 'load_down': (6, 4.8, None)}


def transition(x, duration, voltage, resistance, L=660e-6, C=20e-6):
    # Augmented exact solution: i_L, v_C, integral(v_C dt), constant 1.
    a = np.array([[0, -1/L, 0, voltage/L],
                  [1/C, -1/(resistance*C), 0, 0],
                  [0, 1, 0, 0], [0, 0, 0, 0]])
    return (expm(a*duration) @ np.r_[x, 0., 1.])[:3]


def switched(case, kp, ki, L=660e-6, C=20e-6, startup=False):
    ref_final, r_final, dp_final = CASES[case]
    x = np.array([0., 0.]) if startup else np.array([1., 6.])
    integ, duty, measured = 0., .5, x[1]
    rows = []
    for k in range(300):
        t = k*TS
        ref = ref_final if k >= 100 else 6.
        resistance = r_final if k >= 100 else 6.
        if dp_final is not None:
            duty = 1-(dp_final if k >= 100 else .5)
            new_duty = duty
        else:
            error = ref-measured
            raw = .5+kp*error+integ
            new_duty = np.clip(raw, .05, .95)
            if not ((raw >= .95 and error > 0) or (raw <= .05 and error < 0)):
                integ += TS*ki*error
        # Driver inversion: off for dprime*T, then on for duty*T.
        off = transition(x, (1-duty)*TS, 0., resistance, L, C)
        on = transition(off[:2], duty*TS, 12., resistance, L, C)
        mean_v = (off[2]+on[2])/TS
        samples = np.vstack([transition(x, q*(1-duty)*TS, 0., resistance, L, C)[:2]
                             for q in np.linspace(0, 1, 9)] +
                            [transition(off[:2], q*duty*TS, 12., resistance, L, C)[:2]
                             for q in np.linspace(0, 1, 9)])
        rows.append([t+TS/2, mean_v, ref, 1-duty, samples[:, 0].min(),
                     samples[:, 0].max(), np.ptp(samples[:, 1])])
        x = on[:2]
        measured = mean_v  # Completed cycle average; next command delayed one cycle.
        duty = new_duty
    return np.array(rows)


def metrics(t, v, target, initial=6.):
    mask = t >= .01
    tail = t >= .025
    err = v[mask]-target
    band = .02*abs(target-initial) if target != initial else .12
    outside = np.flatnonzero(np.abs(err) > band)
    tt = t[mask]
    settle = float(tt[outside[-1]+1]-.01) if len(outside) and outside[-1]+1 < len(tt) else (None if len(outside) else 0.)
    direction = np.sign(target-initial)
    return {'mean_final_V': float(np.mean(v[tail])),
            'tail_error_V': float(abs(np.mean(v[tail])-target)),
            'peak_deviation_V': float(np.max(np.abs(err))),
            'overshoot_percent': float(max(0., np.max(direction*err))*100/abs(target-initial)) if direction else None,
            'settling_s': settle, 'settling_band_V': band}


def cycle_average(raw):
    t = raw[:, 0]
    edges = np.arange(301)*TS
    integral = cumulative_trapezoid(raw[:, 1], t, initial=0)
    means = np.diff(np.interp(edges, t, integral))/TS
    return edges[:-1]+TS/2, means


def run_spice(executable, folder, case, kp, ki, maxstep='500n'):
    folder.mkdir()
    ref, resistance, dp = CASES[case]
    template = (ROOT/'circuit/buck.cir.in').read_text()
    values = {'REFERENCE': f'(time<10m ? 6 : {ref})',
              'LOAD': f'(time<10m ? 6 : {resistance})',
              'DPRIME': f'(time<10m ? 0.5 : {dp})' if dp is not None else '1-min(0.95,max(0.05,V(raw)))',
              'KP': str(kp), 'KI': str(ki) if dp is None else '0', 'MAXSTEP': maxstep}
    for key, value in values.items():
        template = template.replace('@'+key+'@', value)
    assert '@' not in template
    (folder/'buck.cir').write_text(template)
    env = dict(os.environ)
    # Optional unpacked Debian runtime, scoped only to this child process.
    lib = executable.parent.parent/'lib/x86_64-linux-gnu'
    if lib.is_dir():
        env['LD_LIBRARY_PATH'] = str(lib)
    # -n skips machine startup files; this circuit uses only built-in devices.
    result = subprocess.run([str(executable), '-n', '-b', 'buck.cir'], cwd=folder,
                            env=env, text=True, capture_output=True, timeout=180)
    (folder/'ngspice.log').write_text(result.stdout+'\n'+result.stderr)
    if result.returncode or 'Error:' in result.stdout+result.stderr:
        raise RuntimeError(f'ngspice failed: {folder}/ngspice.log\n{result.stderr}')
    raw = np.loadtxt(folder/'waveform.txt', skiprows=1)
    assert raw[-1, 0] >= .03-1e-9 and np.isfinite(raw).all()
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matlab-results', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--ngspice', type=Path, default=shutil.which('ngspice'))
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    m = json.loads((args.matlab_results/'results.json').read_text())
    nominal = {'Vin':12., 'L':660e-6, 'C':20e-6, 'R':6., 'fs':1e4,
               'V0':6., 'dp0':.5}
    for name, value in nominal.items():
        if not np.isclose(m['parameters'][name],value,rtol=1e-12,atol=1e-15):
            raise ValueError(f'{name} differs from the fixed project circuit; update all models together.')
    kp, ki = m['parameters']['Kp'], m['parameters']['Ki']
    result = {'matlab_source': str(args.matlab_results.resolve()), 'parameters': m['parameters'],
              'switched': {}, 'circuit': {}, 'checks': []}
    plt.rcParams.update({'font.size': 9, 'axes.grid': True, 'grid.alpha': .25})
    for case, (ref, resistance, dp) in CASES.items():
        a = switched(case, kp, ki)
        np.savetxt(out/(case+'_pwm.csv'), a, delimiter=',',
                   header='time_s,voltage_cycle_mean_V,reference_V,dprime,min_current_A,max_current_A,ripple_pp_V', comments='')
        target = 12*(1-dp) if dp is not None else ref
        result['switched'][case] = metrics(a[:, 0], a[:, 1], target)
        result['switched'][case].update(min_current_A=float(a[100:, 4].min()),
                                       ripple_pp_V=float(a[-20:, 6].mean()))
        assert a[100:, 4].min() > 0, f'CCM invalid: {case}'
        assert result['switched'][case]['tail_error_V'] < .02
        if dp is None:
            assert result['switched'][case]['settling_s'] is not None
            assert result['switched'][case]['settling_s'] < .01
            if ref != 6:
                assert result['switched'][case]['overshoot_percent'] < 10
            else:
                assert result['switched'][case]['peak_deviation_V'] < .8
        fig, ax = plt.subplots(figsize=(6.6, 3.3))
        ax.plot(a[:, 0]*1e3, a[:, 1], label='PWM ideal, promedio por periodo')
        matlab_file = {'open_up': 'open_1', 'open_down': 'open_-1'}.get(case, case)
        b = np.genfromtxt(args.matlab_results/(matlab_file+'.csv'), delimiter=',', names=True)
        ax.plot(b['time_s']*1e3, b['voltage_V'], '--', label='MATLAB, modelo promediado')
        if args.ngspice:
            raw = run_spice(args.ngspice.resolve(), out/case, case, kp, ki)
            t, v = cycle_average(raw)
            cm = metrics(t, v, target)
            cm['ripple_pp_V'] = float(np.ptp(raw[raw[:, 0]>.0299, 1]))
            cm['vgs_min_V'] = float(raw[raw[:, 0]>.01, 4].min())
            cm['vgs_max_V'] = float(raw[raw[:, 0]>.01, 4].max())
            cm['min_current_A'] = float(raw[raw[:, 0]>.01, 2].min())
            cm['max_current_A'] = float(raw[raw[:, 0]>.01, 2].max())
            assert cm['min_current_A'] > 0, f'Circuit leaves CCM: {case}'
            if dp is not None:
                cm['actual_step_metrics'] = metrics(t, v, float(v[-50:].mean()), float(v[90:100].mean()))
                cm['overshoot_percent'] = None  # Ideal final value is not reached with losses.
                mv = np.interp(t, b['time_s'], b['voltage_V'])
                mask = (t>=.01) & (t<=.02)
                error = v[mask]-mv[mask]
                cm['rmse_absolute_V'] = float(np.sqrt(np.mean(error**2)))
                cm['max_absolute_error_V'] = float(abs(error).max())
                # Separate static losses from the incremental step dynamics.
                inc_error = (v[mask]-np.mean(v[90:100]))-(mv[mask]-6)
                cm['rmse_incremental_V'] = float(np.sqrt(np.mean(inc_error**2)))
                cm['rmse_step_percent'] = cm['rmse_absolute_V']/1.2*100
            else:
                assert cm['tail_error_V'] < .02, f'Circuit regulation failed: {case}: {cm}'
                assert cm['settling_s'] is not None and cm['settling_s'] < .01
                if ref != 6:
                    assert cm['overshoot_percent'] < 10
                else:
                    assert cm['peak_deviation_V'] < .8
            result['circuit'][case] = cm
            ax.plot(raw[:, 0]*1e3, raw[:, 1], color='C2', alpha=.18, lw=.4)
            ax.plot(t*1e3, v, color='C2', label='ngspice, promedio por periodo')
        ax.axhline(target, color='.5', ls=':', lw=.8)
        titles = {'open_up': 'Lazo abierto: d′ de 0.5 a 0.6',
                  'open_down': 'Lazo abierto: d′ de 0.5 a 0.4',
                  'ref_up': 'Referencia de 6 a 7 V', 'ref_down': 'Referencia de 6 a 5 V',
                  'load_up': 'Resistencia de 6 a 7.2 Ω', 'load_down': 'Resistencia de 6 a 4.8 Ω'}
        visible = []
        for line in ax.lines:
            xx, yy = map(np.asarray, line.get_data())
            visible.extend(yy[(xx >= 8) & (xx <= 22)])
        low, high = min(visible), max(visible)
        padding = max(.08, .1*(high-low))
        ax.set(xlabel='Tiempo (ms)', ylabel='Tensión de salida (V)', xlim=(8, 22),
               ylim=(low-padding,high+padding),title=titles[case])
        ax.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(out/(case+'.png'), dpi=180)
        plt.close(fig)
        print(case, result['switched'][case], result['circuit'].get(case), flush=True)
    if args.ngspice:
        raw_fine = run_spice(args.ngspice.resolve(), out/'convergence', 'open_up', kp, ki, '250n')
        raw_base = np.loadtxt(out/'open_up/waveform.txt', skiprows=1)
        t, fine = cycle_average(raw_fine)
        _, base = cycle_average(raw_base)
        result['convergence_max_cycle_mean_V'] = float(np.max(abs(fine[t>=.01]-base[t>=.01])))
        assert result['convergence_max_cycle_mean_V'] < .005
        result['checks'].append('ngspice: six scenarios and half-step convergence <5 mV')
    result['checks'].append('PWM: six scenarios, CCM, mean final error <20 mV, closed-loop settling <10 ms, reference overshoot <10%')
    (out/'results.json').write_text(json.dumps(result, indent=2, allow_nan=False))
    print('PASS', out, flush=True)


if __name__ == '__main__':
    main()
