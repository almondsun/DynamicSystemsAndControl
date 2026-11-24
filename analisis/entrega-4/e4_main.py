"""Entrega 4: numbers and report figures from the Rev C bench data.

Reads the captures in firmware/bringup/captures/ (AD3 + firmware), the Entrega 4 metrics
(metrics_entrega4.csv, from firmware/bringup/tools/analyze_e4.py) and the Entrega 3
simulations (entrega3/results/e3_sims.mat). Writes entrega4/results/e4_results.json and the
vector figures in entrega4/figures/report/ used by report/entrega_4.tex.

Also re-evaluates the exact sampled-data loop of entrega3/matlab/e3_loop.m ('disc') with the
plant identified on the board, to check that the Entrega 3 PI needs no retuning.

usage: python -I e4_main.py        (paths are relative to this file)
"""
import csv
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
from scipy.linalg import expm
from scipy.optimize import curve_fit

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
REVC = HERE.parents[1]
CAP = REVC / "firmware" / "bringup" / "captures"
OUT_FIG = REVC / "entrega4" / "figures" / "report"
OUT_RES = REVC / "entrega4" / "results"
sys.path.insert(0, str(REVC / "firmware" / "bringup" / "tools"))
import analyze_e4 as a4  # noqa: E402  (metrics port of e3_metrics.m, loaders)

KP, KI = 0.030477, 91.43
FSW_MEAS = 19840.0
TEAL, ORANGE, GRAY, RAW, INK, GRID = "#0097B2", "#F19820", "#7D8B95", "#B9C5CC", "#111111", "#DDDDDD"
REP_COLORS = ["#0097B2", "#3FB8CF", "#006F83"]
COL_IN, WIDE_IN = (237 / 72, 211 / 72), (486 / 72, 242 / 72)

plt.rcParams.update({"font.family": "sans-serif",
                     "font.sans-serif": ["Helvetica", "Arial", "Liberation Sans", "DejaVu Sans"],
                     "font.size": 8, "axes.edgecolor": INK, "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.5, "lines.linewidth": 1.1, "legend.frameon": False,
                     "legend.fontsize": 7, "pdf.fonttype": 42})


# ---------- exact sampled-data loop (port of e3_plant.m + e3_zoh.m + e3_loop.m 'disc') ----------

def loop_disc(w, p, ts):
    a = np.array([[-p["rL"] / p["L"], -1 / p["L"], 0.0],
                  [1 / p["C"], -1 / (p["R"] * p["C"]), 0.0],
                  [0.0, 1 / p["tau"], -1 / p["tau"]]])
    b = np.array([[(p["Vin"] + p["Vf"]) / p["L"]], [0.0], [0.0]])
    m = np.zeros((4, 4)); m[:3, :3] = a; m[:3, 3:] = b
    e = expm(m * ts)
    ad, bd = e[:3, :3], e[:3, 3:]
    cm = np.array([[0.0, 0.0, 1.0]])
    z = np.exp(1j * w * ts)
    g = np.array([(cm @ np.linalg.solve(zi * np.eye(3) - ad, bd))[0, 0] for zi in z])
    c = KP + KI * ts * z / (z - 1)
    return c * g / z


def margins(p, ts):
    w = np.logspace(1, np.log10(np.pi / ts * 0.999), 40000)
    lw = loop_disc(w, p, ts)
    mag, ph = np.abs(lw), np.unwrap(np.angle(lw))
    i_c = int(np.argmax(mag < 1.0))
    wc = np.interp(1.0, [mag[i_c], mag[i_c - 1]], [w[i_c], w[i_c - 1]])
    pm = 180 + np.degrees(np.interp(wc, w, ph))
    i_180 = np.flatnonzero(np.degrees(ph) < -180)
    gm = -20 * np.log10(np.interp(w[i_180[0]], w, mag)) if i_180.size else np.inf
    return {"wc": float(wc), "PM_deg": float(pm), "GM_dB": float(gm)}


def plant_2nd(p):
    lc = p["L"] * p["C"]
    a1, a0 = (p["L"] / p["R"] + p["rL"] * p["C"]) / lc, (1 + p["rL"] / p["R"]) / lc
    return {"wn": float(np.sqrt(a0)), "zeta": float(a1 / (2 * np.sqrt(a0))),
            "K0": float((p["Vin"] + p["Vf"]) / (1 + p["rL"] / p["R"]))}


E3_PLANT = {"Vin": 12.0, "Vf": 0.4, "L": 660e-6, "rL": 1.2, "C": 20e-6, "R": 6.0, "tau": 7.5e3 * 4.7e-9}
ID_PLANT = {**E3_PLANT, "Vin": 11.85, "Vf": 0.26, "rL": 0.94, "C": 15e-6}


# ---------- open-loop duty step identification ----------

def step2(t, t0, y0, dy, wn, z):
    tau = np.clip(t - t0, 0, None); wd = wn * np.sqrt(1 - z ** 2)
    return y0 + dy * (1 - np.exp(-z * wn * tau) * (np.cos(wd * tau) + z / np.sqrt(1 - z ** 2) * np.sin(wd * tau)))


def identify_step(path, sign):
    t_us, v = np.loadtxt(path, delimiter=",", skiprows=1, unpack=True)
    t, fs = t_us * 1e-6, 1e6 / np.median(np.diff(t_us))
    win = int(round(fs / FSW_MEAS))
    va = np.convolve(v, np.ones(win) / win, mode="valid"); ta = t[: len(va)] + (win - 1) / 2 / fs
    y0g, y1g = va[:500].mean(), va[-2000:].mean()
    t_guess = ta[np.argmax(sign * (va - (y0g + y1g) / 2) > 0)] - 0.15e-3
    sel = (ta > t_guess - 2e-3) & (ta < t_guess + 6e-3)
    p, _ = curve_fit(step2, ta[sel], va[sel], p0=[t_guess, y0g, y1g - y0g, 11e3, 0.5],
                     bounds=([0, 0, -3, 2e3, 0.05], [0.02, 10, 3, 5e4, 0.99]))
    rms = float(np.sqrt(np.mean((step2(ta[sel], *p) - va[sel]) ** 2)))
    return {"t": t - p[0], "v": v, "ta": ta - p[0], "va": va, "fit": p, "rms": rms}


# ---------- figures ----------

def save(fig, name):
    fig.savefig(OUT_FIG / f"{name}.pdf"); plt.close(fig)


def fig_vgs():
    t1, vgs = np.loadtxt(CAP / "stepC_vgs_d010.csv", delimiter=",", skiprows=1, unpack=True)
    t2, vb = np.loadtxt(CAP / "stepD_d060.csv", delimiter=",", skiprows=1, usecols=(0, 1), unpack=True)
    fig, ax = plt.subplots(2, 1, figsize=COL_IN, sharex=True)
    k1 = int(np.argmax(vgs > 5))
    ax[0].plot(t1 - t1[k1], vgs, color=TEAL)
    ax[0].set_ylabel("$v_{GS}$ (V)"); ax[0].set_ylim(-1, 12.5)
    ax[0].set_title("$d=0.10$, $6\\,\\Omega$: compuerta de $Q_1$", fontsize=8)
    ax[1].plot(t2 - t2[0], vb, color=ORANGE)
    ax[1].set_ylabel("$v_{BOOT}-v_{SW}$ (V)"); ax[1].set_ylim(11.3, 12.0)
    ax[1].set_title("$d=0.60$, $6\\,\\Omega$: bootstrap", fontsize=8)
    ax[1].set_xlim(-5, 130); ax[1].set_xlabel("t ($\\mu$s)")
    fig.tight_layout(pad=0.3); save(fig, "fig_vgs")
    return {"vgs_on": float(np.median(vgs[vgs > 8])), "vgs_off": float(np.median(vgs[vgs < 2])),
            "boot_med_d060": float(np.median(vb)), "boot_min_d060": float(vb.min())}


def fig_ident():
    res, fig = {}, plt.figure(figsize=WIDE_IN)
    axes = fig.subplots(1, 2)
    e3 = plant_2nd(E3_PLANT)
    for ax, (name, sign, title) in zip(axes, [("dynamics_step_up_060_070", 1, "$d$: $0.60\\to0.70$"),
                                              ("dynamics_step_down_070_060", -1, "$d$: $0.70\\to0.60$")]):
        r = identify_step(CAP / f"{name}.csv", sign)
        t0, y0, dy, wn, z = r["fit"]
        model = step2(r["ta"] + t0, t0, y0, sign * 0.1 * e3["K0"], e3["wn"], e3["zeta"])
        ax.plot(r["t"] * 1e3, r["v"], color=RAW, lw=0.5, label="medido (AD3, 1 MS/s)")
        ax.plot(r["ta"] * 1e3, r["va"], color=TEAL, label="medido, media por periodo")
        ax.plot(r["ta"] * 1e3, step2(r["ta"] + t0, *r["fit"]), "--", color=ORANGE,
                label=f"ajuste: $\\omega_n$={wn:.0f} rad/s, $\\zeta$={z:.2f}")
        ax.plot(r["ta"] * 1e3, model, ":", color=GRAY, lw=1.2, label="modelo entrega 3 ($C=20\\,\\mu$F)")
        ax.set_xlim(-0.5, 3); ax.set_title(title, fontsize=8); ax.set_xlabel("t desde el escalón (ms)")
        ax.legend(loc="lower right" if sign > 0 else "upper right")
        res[name] = {"wn": float(wn), "zeta": float(z), "dV": float(dy), "y0": float(y0), "rms_mV": r["rms"] * 1e3,
                     "C_eff_uF": float((1 + ID_PLANT["rL"] / 6) / (660e-6 * wn ** 2) * 1e6)}
    axes[0].set_ylabel("$v_o$ (V)")
    fig.tight_layout(pad=0.3); save(fig, "fig_ident")
    return res


def fig_arranque():
    t, _trig, v = np.loadtxt(CAP / "closed_loop" / "softstart_6V_day2_ad3.csv", delimiter=",", skiprows=1,
                             unpack=True)
    fw = np.loadtxt(CAP / "closed_loop" / "softstart_6V_day2_fw.csv", delimiter=",", skiprows=1)
    fig, ax = plt.subplots(2, 1, figsize=COL_IN, sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    ax[0].plot(t * 1e-3, v, color=RAW, lw=0.4, label="$v_o$ medido (AD3)")
    ax[0].plot(fw[:, 1] * 1e-3, fw[:, 3], color=TEAL, label="$v_m$ del lazo (ADC)")
    ax[0].plot(fw[:, 1] * 1e-3, fw[:, 2], "--", color=ORANGE, label="$v_{ref}$ (rampa)")
    ax[0].set_ylabel("V"); ax[0].legend(loc="upper left")
    ax[1].plot(fw[:, 1] * 1e-3, fw[:, 4], color=TEAL); ax[1].set_ylabel("$d$")
    ax[1].set_xlabel("t desde el arranque (ms)"); ax[1].set_xlim(-5, 150)
    fig.tight_layout(pad=0.3); save(fig, "fig_arranque")
    ramp = (fw[:, 1] > 10e3) & (fw[:, 1] < 85e3)
    late = t > t[-1] - 20e3
    return {"lag_mV": float((fw[ramp, 2] - fw[ramp, 3]).mean() * 1e3), "vout_final_ad3": float(v[late].mean())}


def fig_tests(labels, name, xlim):
    sim = a4.load_sim(REVC / "entrega3" / "results" / "e3_sims.mat")
    fig = plt.figure(figsize=WIDE_IN)
    axes = fig.subplots(2, 2, sharex="col", gridspec_kw={"height_ratios": [2, 1]})
    for col, label in enumerate(labels):
        key, r0, r1, title = a4.TESTS[label]
        ts_, vs_, ds_ = sim[key]
        for k, rep in enumerate(sorted((CAP / "entrega4").glob(f"{label}_r*_ad3.csv"))):
            n = rep.stem.split("_r")[-1].split("_")[0]
            t, v, _g = a4.load_ad3(rep)
            tf, _vref, _vadc, d = a4.load_fw(CAP / "entrega4" / f"{label}_r{n}_fw.csv")
            axes[0, col].plot(t * 1e3, v, color=REP_COLORS[k], lw=1.0, label=f"medido #{n}")
            axes[1, col].plot(tf * 1e3, d, color=REP_COLORS[k], lw=0.9)
        axes[0, col].plot(ts_ * 1e3, vs_, "--", color=ORANGE, lw=1.1, label="simulado (entrega 3)")
        axes[1, col].plot(ts_ * 1e3, ds_, "--", color=ORANGE, lw=1.0)
        if r0 == r1:
            axes[0, col].axhspan(r1 * 0.98, r1 * 1.02, color=GRID, alpha=0.6, lw=0)
        axes[0, col].set_title(title.replace("ohm", "$\\Omega$").replace("->", "$\\to$"), fontsize=8)
        axes[1, col].set_xlabel("t desde el evento (ms)"); axes[1, col].set_xlim(*xlim)
    axes[0, 0].set_ylabel("$v_o$, media por periodo (V)"); axes[1, 0].set_ylabel("$d$")
    axes[0, 0].legend(loc="best")
    fig.tight_layout(pad=0.3); save(fig, name)


# ---------- summary of the Entrega 4 metrics ----------

def summarize_metrics():
    with open(CAP / "entrega4" / "metrics_entrega4.csv") as f:
        rows = list(csv.DictReader(f))
    out = {}
    for label in a4.TESTS:
        out[label] = {}
        for src in ("ad3", "fw_adc", "sim_e3"):
            sel = [r for r in rows if r["test"] == label and r["source"] == src]
            stats = {}
            for k in ("ess", "tr_ms", "Mp_pct", "ts_ms", "dVmax", "trec_ms", "ts20_ms", "dmin", "dmax"):
                vals = [float(r[k]) for r in sel if r[k] != ""]
                if vals:
                    stats[k] = {"mean": float(np.mean(vals)), "min": float(min(vals)), "max": float(max(vals))}
            out[label][src] = stats
    return out


ERROR_WINDOWS_MS = {"ref_up_6_7": 10.0, "ref_down_6_5": 10.0, "load_plus20": 6.0, "load_minus20": 6.0}


def trace_errors():
    """Measured (AD3, period average) minus the E3 switched simulation, on the simulation's
    period grid from the event to the end of the figure window. 'bias-free' removes the
    pre-event difference (-2..0 ms), i.e. the simulation's steady-state ADC bias."""
    sim = a4.load_sim(REVC / "entrega3" / "results" / "e3_sims.mat")
    out = {}
    for label, win_ms in ERROR_WINDOWS_MS.items():
        ts_, vs_, _ds = sim[a4.TESTS[label][0]]
        post, pre = (ts_ >= 0) & (ts_ <= win_ms * 1e-3), (ts_ > -2e-3) & (ts_ < 0)
        reps = []
        for rep in sorted((CAP / "entrega4").glob(f"{label}_r*_ad3.csv")):
            t, v, _g = a4.load_ad3(rep)
            err = np.interp(ts_, t, v) - vs_
            bias = err[pre].mean()
            reps.append({"rms_mV": 1e3 * float(np.sqrt(np.mean(err[post] ** 2))),
                         "max_mV": 1e3 * float(np.abs(err[post]).max()),
                         "rms_nobias_mV": 1e3 * float(np.sqrt(np.mean((err[post] - bias) ** 2))),
                         "bias_mV": 1e3 * float(bias)})
        out[label] = {k: {"mean": float(np.mean([r[k] for r in reps])),
                          "min": float(min(r[k] for r in reps)), "max": float(max(r[k] for r in reps))}
                      for k in reps[0]}
        out[label]["window_ms"] = win_ms
    return out


def main():
    OUT_FIG.mkdir(parents=True, exist_ok=True); OUT_RES.mkdir(parents=True, exist_ok=True)
    ts_nom, ts_meas = 50e-6, 1 / FSW_MEAS
    res = {"margins": {"e3_nominal": margins(E3_PLANT, ts_nom),
                       "identified": margins(ID_PLANT, ts_meas),
                       "identified_C14_L594": margins({**ID_PLANT, "C": 14e-6, "L": 594e-6}, ts_meas),
                       "identified_C17_L726": margins({**ID_PLANT, "C": 17e-6, "L": 726e-6}, ts_meas)},
           "plant": {"e3": plant_2nd(E3_PLANT), "identified": plant_2nd(ID_PLANT)},
           "ki_effective": KI * ts_nom * FSW_MEAS,
           "driver": fig_vgs(), "ident": fig_ident(), "softstart": fig_arranque(),
           "tests": summarize_metrics(), "trace_error": trace_errors()}
    fig_tests(["ref_up_6_7", "ref_down_6_5"], "fig_ref", (-1, 10))
    fig_tests(["load_plus20", "load_minus20"], "fig_carga", (-1, 6))
    (OUT_RES / "e4_results.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("margins", "plant", "ki_effective", "driver", "softstart")}, indent=1))
    print(json.dumps(res["ident"], indent=1))
    print(json.dumps(res["trace_error"], indent=1))


if __name__ == "__main__":
    main()
