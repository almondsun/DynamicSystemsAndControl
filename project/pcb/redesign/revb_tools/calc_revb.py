"""Rev B design calculations: ADC path, clamp, supervisor timing and bootstrap.

Datasheet limits are quoted inline with their source. Results are written as
JSON for the review documents; nothing here is a measurement.

    python3 -I calc_revb.py ../validation/revb/calculations.json
"""
import json
import math
import sys
from pathlib import Path

# --- ADC divider and protection (values as placed in the Rev B schematic) ---
R14, R15 = 15e3, 2.2e3          # 1 % thick film, existing
R20 = 1e3                       # series resistor, clamp node -> TMUX1511 S1
R23 = 2.2e3                     # LM4040 bias from +5V
R21 = 100e3                     # MCU-side discharge to GND
RON_TYP, RON_MAX = 2.0, 4.5     # TMUX1511 SCDS390B 5.5: typ at 3.3 V, max over VDD/temperature
C17 = 1e-9
TOL = 0.01
VREF_NOM = 3.3
LM4040 = {"vr": 2.5, "tol_25c": 2.5e-3, "tol_full": 19e-3, "irmin_max": 65e-6,
          "ir_abs_max": 20e-3, "if_abs_max": 10e-3, "zr_max": 0.8, "reg_1_15ma_max": 8e-3}
BAT54WS = {"vf_0p1ma_max": 0.24, "vf_1ma_max": 0.32, "vf_10ma_max": 0.40, "ir_25v_max": 2e-6}
TMUX_SIG_MIN = -0.5             # SCDS390B 5.1 abs max on S/D pins
TPS3808_VIT, TPS3808_ACC = 3.07, 0.015
SENSE_R, SENSE_INTERNAL = 10e3, 4e6

# --- Bootstrap (IR2110 VCC = VIN; course steps at 12 V nominal) ---
VIN = 12.0
VF_D2_MAX = 1.0                 # Vishay UF4004 VF max at IF = 1.0 A, 25 C
QG_MAX = 63e-9                  # Infineon IRFZ44NPbF Qg max (VGS = 10 V)
QLS = 5e-9                      # IR2110 level-shift charge, budget as in Rev A study
IQBS_MAX, ILK_MAX = 230e-6, 50e-6
R2_MIN = 10e3 * 0.99
C6_NOM = 2.2e-6
VBS_MIN_REC = 10.0              # IR2110 recommended VBS minimum
VBSUV_MAX = 9.7                 # IR2110 VBS UVLO+ maximum
TS = 100e-6


def divider():
    rth = R14 * R15 / (R14 + R15)
    k = R15 / (R14 + R15)
    load = R21 / (rth + R20 + RON_TYP + R21)
    kp = k * load

    def corner(sign):
        r14 = R14 * (1 - sign * TOL)
        r15 = R15 * (1 + sign * TOL)
        r21 = R21 * (1 + sign * TOL)
        r20 = R20 * (1 - sign * TOL)
        ron = RON_TYP if sign > 0 else RON_MAX
        rth_c = r14 * r15 / (r14 + r15)
        return r15 / (r14 + r15) * r21 / (rth_c + r20 + ron + r21)

    r_source = rth + R20 + RON_MAX
    tau = r_source * C17
    return {
        "k_unloaded": k, "rth_ohm": rth, "k_loaded_nominal": kp,
        "k_loaded_min": corner(-1), "k_loaded_max": corner(1),
        "volts_per_count_nominal": VREF_NOM / 4095 / kp,
        "gain_change_vs_revA_percent": (kp / k - 1) * 100,
        "source_resistance_max_ohm": r_source,
        "c17_tau_us": tau * 1e6, "c17_fc_khz": 1 / (2 * math.pi * tau) / 1e3,
        "phase_at_10khz_deg": -math.degrees(math.atan(2 * math.pi * 10e3 * tau)),
        "vadc_at": {f"{v:g}V": round(v * kp, 4) for v in (5, 6, 7, 8.3)},
    }


def clamp(kp_max):
    """U10 biased by R23 from +5V sets REF_2V5; D4 clamps the divider tap to REF + VF, D3 to -VF.
    Neither diode nor U10 sits on the tap in normal operation (LM4040-N conducts 5-35 uA below
    breakdown, SNOS633N Fig. 5-4, so it must not load the measurement node)."""
    rth = R14 * R15 / (R14 + R15)
    ref_max = LM4040["vr"] + LM4040["tol_full"] + LM4040["reg_1_15ma_max"]
    bias = {"min_ma": (4.75 - 2.519) / (R23 * 1.01) * 1e3, "max_ma": (5.25 - 2.481) / (R23 * 0.99) * 1e3}
    rows = []
    for vout in (7, 8.3, 13.2, 20, 24, 30, 48):
        vth = vout * R15 / (R14 + R15)
        onset = ref_max + BAT54WS["vf_0p1ma_max"] * 0  # clamp starts conducting near REF
        i = max(0.0, (vth - LM4040["vr"] - 0.2) / rth)
        vf = 0.0 if i == 0 else (BAT54WS["vf_1ma_max"] if i <= 1e-3 else BAT54WS["vf_10ma_max"])
        tap = min(vth, ref_max + vf) if i else vth
        rows.append({"vout": vout, "tap_unclamped_v": round(vth, 4), "clamp_current_ma_est": round(i * 1e3, 3),
                     "tap_v_max": round(tap, 4), "adc_pin_v_max": round(tap * R21 / (R21 + R20), 4)})
    tap_abs = ref_max + BAT54WS["vf_10ma_max"]
    neg = []
    for vout in (-1, -5, -12, -24):
        vth = vout * R15 / (R14 + R15)
        i = max(0.0, (-vth - 0.24) / rth)
        vf = BAT54WS["vf_1ma_max"] if i <= 1e-3 else BAT54WS["vf_10ma_max"]
        pin = -vf if i > 0 else vth
        neg.append({"vout": vout, "diode_current_ma": round(i * 1e3, 4), "tmux_pin_v_min": round(pin, 4),
                    "within_tmux_abs_max": pin >= TMUX_SIG_MIN})
    return {
        "topology": "U10 reference (R23 2.2k from +5V, C22) + D4 tap->REF_2V5 + D3 GND->tap",
        "lm4040_bias_ma": bias, "ref_2v5_max_v": ref_max, "tap_abs_max_v_clamp_10ma": tap_abs,
        "adc_pin_abs_max_v": tap_abs * R21 / (R21 + R20),
        "vdda_min_when_switch_on": TPS3808_VIT * (1 - TPS3808_ACC),
        "headroom_v": TPS3808_VIT * (1 - TPS3808_ACC) - tap_abs * R21 / (R21 + R20),
        "vout_measurement_ceiling_nominal": (LM4040["vr"] + 0.2) / kp_max,
        "positive": rows, "negative": neg,
        "diode_leak_error_mv_at_vout_per_1uA": 1e-6 * rth * (R14 + R15) / R15 * 1e3,
        "note": "BAT54WS IR 2 uA max at 25 V/25 C (DS30098); typical 0.045 uA at 25 C and ~1.8 uA at 75 C "
                "near 0.9-1.6 V reverse (Fig. 2): D3 and D4 leak in opposite directions on the tap.",
    }


def supervisor():
    shift = SENSE_R / SENSE_INTERNAL
    return {"vit_nominal": TPS3808_VIT, "vit_min": TPS3808_VIT * (1 - TPS3808_ACC),
            "vit_max": TPS3808_VIT * (1 + TPS3808_ACC), "series_r_shift_percent": shift * 100,
            "sense_backfeed_limit_ma_if_internal_diode": (3.465 - 0.6) / SENSE_R * 1e3,
            "release_delay_ms_ct_to_vdd_via_r24": [180, 300, 420], "sense_to_reset_us_typ": 20,
            "release_threshold_max_v": TPS3808_VIT * (1 + TPS3808_ACC) * 1.025 + 0.008,
            "sense_filter_tau_us": SENSE_R * 1e-9 * 1e6}


def bootstrap():
    rows = []
    for vout in (5.0, 6.0, 7.0):
        d = vout / VIN
        ton = d * TS
        q = QG_MAX + QLS + (IQBS_MAX + ILK_MAX + (VIN - VF_D2_MAX) / R2_MIN) * ton
        for beta in (1.0, 0.5):
            ceff = C6_NOM * 0.9 * 0.85 * beta
            dv = q / ceff
            vbs = VIN - VF_D2_MAX - dv
            rows.append({"vout": vout, "duty": round(d, 4), "ton_us": round(ton * 1e6, 2),
                         "q_nc": round(q * 1e9, 1), "beta_dc_bias": beta, "ceff_uf": round(ceff * 1e6, 4),
                         "droop_v": round(dv, 4), "vbs_min_v": round(vbs, 3),
                         "meets_10v": vbs >= VBS_MIN_REC, "above_uvlo_max": vbs >= VBSUV_MAX,
                         "recharge_avg_ma": round(q / ((1 - d) * TS) * 1e3, 3)})
    vin_min = VBS_MIN_REC + VF_D2_MAX + max(r["droop_v"] for r in rows)
    return {"vin": VIN, "vs_off_assumed_v": 0.0, "rows": rows,
            "vin_min_for_10v_worst_row": round(vin_min, 3),
            "note": "VS taken as 0 V during OFF (D1 conduction would add ~0.3 V margin); "
                    "no claim for 10.8 V input or pre-charged output."}


def main() -> None:
    out = Path(sys.argv[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    adc = divider()
    data = {"adc": adc, "clamp": clamp(adc["k_loaded_max"]), "supervisor": supervisor(),
            "bootstrap": bootstrap()}
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(data, indent=1))


if __name__ == "__main__":
    main()
