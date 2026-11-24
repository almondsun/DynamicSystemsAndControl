"""Entrega 4 metrics and figures: bench captures vs the Entrega 3 switched simulation.

Metric definitions are a port of analisis/entrega-3/matlab/e3_metrics.m (per-period average of vo):
  reference steps: tr 10-90 %, Mp (% of the change), ts (band +-2 % of the change), ess
  load steps:      dVmax (peak deviation), trec (back inside +-2 % of Vref), ts20 (+-20 mV), ess
AD3 traces are averaged over one PWM period and gain-corrected so the pre-event mean is the
DMM-calibrated 6.000 V (the loop ADC was calibrated against the DMM before the tests).

usage: python -I analyze_e4.py <captures_dir> <e3_sims.mat> <out_dir>
"""
import csv
import sys
from pathlib import Path

import matplotlib
import numpy as np
import scipy.io as sio

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

VREF0 = 6.0
FSW_HZ = 19840.0  # measured PWM frequency (MSI clock)
# label -> (sim key, ref0, ref1, title)
TESTS = {"ref_up_6_7": ("up", 6.0, 7.0, "Referencia 6 -> 7 V"),
         "ref_down_6_5": ("down", 6.0, 5.0, "Referencia 6 -> 5 V"),
         "load_plus20": ("Rp", 6.0, 6.0, "Carga +20 % (6 -> 7.2 ohm)"),
         "load_minus20": ("Rm", 6.0, 6.0, "Carga -20 % (6 -> 4.8 ohm)")}
FIELDS = ["test", "rep", "source", "v0", "vf", "ess", "tr_ms", "Mp_pct", "ts_ms",
          "dVmax", "trec_ms", "ts20_ms", "dmin", "dmax"]


def last_time_outside(t, mask):
    idx = np.flatnonzero(mask)
    return float(t[idx[-1]]) if idx.size else 0.0


def crossing(ta, sa, level):
    i = int(np.argmax(sa >= level))
    if i == 0:
        return float(ta[0])
    return float(ta[i - 1] + (level - sa[i - 1]) * (ta[i] - ta[i - 1]) / (sa[i] - sa[i - 1]))


def metrics(t, v, ref0, ref1, d=None, t_d=None):
    v0 = v[(t > -2e-3) & (t < 0)].mean()
    vf = v[t > t[-1] - 2e-3].mean()
    after = t > 0
    m = {"v0": v0, "vf": vf, "ess": vf - ref1}
    if d is not None:
        m["dmin"], m["dmax"] = d[t_d > 0].min(), d[t_d > 0].max()
    if ref1 != ref0:
        dv = ref1 - ref0
        ta, sa = t[after], (v[after] - v0) / dv
        m["tr_ms"] = 1e3 * (crossing(ta, sa, 0.9) - crossing(ta, sa, 0.1))
        m["Mp_pct"] = max(0.0, 100 * (sa.max() - (vf - v0) / dv))
        m["ts_ms"] = 1e3 * last_time_outside(t, after & (np.abs(v - vf) > 0.02 * abs(dv)))
    else:
        dev = v[after] - ref1
        m["dVmax"] = dev[np.argmax(np.abs(dev))]
        m["trec_ms"] = 1e3 * last_time_outside(t, after & (np.abs(v - ref1) > 0.02 * ref1))
        m["ts20_ms"] = 1e3 * last_time_outside(t, after & (np.abs(v - ref1) > 0.02))
    return m


def load_ad3(path):
    t_us, _trig, v = np.loadtxt(path, delimiter=",", skiprows=1, unpack=True)
    t = t_us * 1e-6
    fs = 1.0 / np.median(np.diff(t))
    win = int(round(fs / FSW_HZ))
    va = np.convolve(v, np.ones(win) / win, mode="same")
    va = va[win:-win]
    t = t[win:-win]
    gain = VREF0 / va[(t > -2e-3) & (t < 0)].mean()
    return t, va * gain, gain


def load_fw(path):
    a = np.loadtxt(path, delimiter=",", skiprows=1)
    return a[:, 1] * 1e-6, a[:, 2], a[:, 3], a[:, 4]  # t, vref, vout_adc, d


def load_sim(mat_path):
    sims = sio.loadmat(mat_path, squeeze_me=True, struct_as_record=False)["sims"]
    out = {}
    for key in ("up", "down", "Rp", "Rm"):
        sc, sw = getattr(sims, key).sc, getattr(sims, key).sw
        out[key] = (sw.tp + sw.Ts / 2 - sc.t_ev, sw.vavg, sw.d)
    return out


def fmt(x):
    return "" if x is None else f"{x:.4g}"


def main():
    cap_dir, mat_path, out_dir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    sim = load_sim(mat_path)
    rows = []
    fig, axes = plt.subplots(4, 2, figsize=(12, 13), gridspec_kw={"width_ratios": [2, 1]})
    for (label, (key, r0, r1, title)), ax in zip(TESTS.items(), axes):
        ts_, vs_, ds_ = sim[key]
        rows.append({"test": label, "rep": "-", "source": "sim_e3", **metrics(ts_, vs_, r0, r1, ds_, ts_)})
        for rep in sorted(cap_dir.glob(f"{label}_r*_ad3.csv")):
            n = rep.stem.split("_r")[-1].split("_")[0]
            t, v, gain = load_ad3(rep)
            tf, vref, vadc, d = load_fw(cap_dir / f"{label}_r{n}_fw.csv")
            rows.append({"test": label, "rep": n, "source": "ad3", **metrics(t, v, r0, r1, d, tf)})
            rows.append({"test": label, "rep": n, "source": "fw_adc", **metrics(tf, vadc, r0, r1, d, tf)})
            ax[0].plot(t * 1e3, v, lw=1, label=f"medido AD3 #{n}")
            ax[1].plot(tf * 1e3, d, lw=0.8, label=f"d firmware #{n}")
        ax[0].plot(ts_ * 1e3, vs_, "k--", lw=1.3, label="simulacion E3 (conmutado)")
        ax[1].plot(ts_ * 1e3, ds_, "k--", lw=1.1, label="d simulado")
        ax[0].set_title(title); ax[0].set_xlim(-3, 15); ax[1].set_xlim(-3, 15)
        ax[0].set_ylabel("VOUT promedio por periodo [V]"); ax[1].set_ylabel("d")
        for a_ in ax:
            a_.grid(alpha=0.3); a_.legend(fontsize=7)
    for a_ in axes[-1]:
        a_.set_xlabel("t desde el evento [ms]")
    fig.suptitle("Entrega 4: PI en lazo cerrado sobre la placa Rev C vs simulacion Entrega 3")
    fig.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "entrega4_tests.png", dpi=140)

    with open(out_dir / "metrics_entrega4.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: (fmt(r.get(k)) if k not in ("test", "rep", "source") else r[k]) for k in FIELDS})
    for r in rows:
        print(",".join(str(r[k]) if k in ("test", "rep", "source") else fmt(r.get(k)) for k in FIELDS))


if __name__ == "__main__":
    main()
