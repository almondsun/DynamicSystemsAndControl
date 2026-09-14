"""Compare a measured capture to the averaged Buck model using measured R/L/C.

Example: python analyze_experiment.py capture.csv measured.json --output NEW_DIR
The output folder must not exist. Raw laboratory captures are never modified.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.linalg import expm


def predict(data, params):
    required = {'time_s', 'voltage_V', 'dprime', 'load_ohm', 'reference_V'}
    if not required.issubset(data.dtype.names or ()):
        raise ValueError('Missing required capture columns.')
    data = np.atleast_1d(data)
    if len(data) < 10:
        raise ValueError('At least ten samples are required.')
    for field in required:
        if not np.isfinite(data[field]).all():
            raise ValueError(f'Non-finite values in {field}.')
    t = data['time_s']
    if not (np.diff(t)>0).all():
        raise ValueError('Time must be strictly increasing.')
    if not ((data['dprime']>=0) & (data['dprime']<=1)).all():
        raise ValueError('dprime must be between zero and one.')
    if not (data['load_ohm']>0).all():
        raise ValueError('Load resistance must be positive.')
    for field in ['Vin', 'L_H', 'C_F', 'R_ohm']:
        if not np.isfinite(params[field]) or params[field] <= 0:
            raise ValueError(f'{field} must be finite and positive.')
    if not t[0] < params['step_time_s'] < t[-1]:
        raise ValueError('Capture must include samples before and after the step.')
    i0 = params.get('initial_current_A', data['voltage_V'][0]/data['load_ohm'][0])
    if not np.isfinite(i0):
        raise ValueError('Initial current must be finite.')
    x = np.array([i0, data['voltage_V'][0], 1.])
    pred = np.empty(len(data))
    pred[0] = x[1]
    L, C = params['L_H'], params['C_F']
    # ZOH measured duty/load over each sample interval; exact state transition.
    for k, dt in enumerate(np.diff(t)):
        R = data['load_ohm'][k]
        a = np.array([[0, -1/L, params['Vin']*(1-data['dprime'][k])/L],
                      [1/C, -1/(R*C), 0], [0, 0, 0]])
        x = expm(a*dt)@x
        pred[k+1] = x[1]
    return pred


def analyze(capture, params):
    pred = predict(capture, params)
    t, measured = capture['time_s'], capture['voltage_V']
    after = t >= params['step_time_s']
    before = (t < params['step_time_s']) & (t >= params['step_time_s']-.002)
    if not np.any(before):
        raise ValueError('Need pre-step data within 2 ms of the event.')
    error = measured[after]-pred[after]
    inc = (measured[after]-measured[before].mean())-(pred[after]-pred[before].mean())
    result = {'rmse_absolute_V': float(np.sqrt(np.mean(error**2))),
              'mae_V': float(np.mean(abs(error))),
              'max_absolute_error_V': float(np.max(abs(error))),
              'rmse_incremental_V': float(np.sqrt(np.mean(inc**2))),
              'initial_current_assumed_equilibrium': 'initial_current_A' not in params,
              'model': 'Ideal averaged CCM; measured duty/load held between samples; no ESR or DCR',
              'ripple_handling': 'Metrics use supplied samples without smoothing; raw ripple contributes to error.'}
    return pred, result


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('parameters', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    capture = np.genfromtxt(args.capture, delimiter=',', names=True)
    params = json.loads(args.parameters.read_text())
    pred, result = analyze(capture, params)
    args.output.mkdir(parents=True, exist_ok=False)
    result.update(capture=str(args.capture.resolve()), parameters=params)
    (args.output/'comparison.json').write_text(json.dumps(result, indent=2, allow_nan=False))
    np.savetxt(args.output/'comparison.csv', np.column_stack([capture['time_s'], capture['voltage_V'],pred]),
               delimiter=',', header='time_s,measured_voltage_V,model_voltage_V', comments='')
    fig, ax = plt.subplots(figsize=(7,4))
    ax.plot(capture['time_s']*1000, capture['voltage_V'], label='Medicion suministrada')
    ax.plot(capture['time_s']*1000, pred, label='Modelo con parametros medidos')
    ax.set(xlabel='Tiempo (ms)', ylabel='Tension (V)')
    ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(args.output/'comparison.png', dpi=180)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
