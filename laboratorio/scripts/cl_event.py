"""Closed-loop event capture for the Buck Rev C bench (Entrega 4).

Sends one console command to the NUCLEO (e.g. "pi on", "v 7", "a 0") and records:
  - Analog Discovery 3: CH1 = TRIG (TP10, trigger on either edge), CH2 = VOUT (TP4)
  - the firmware capture (vref, VOUT from the loop ADC, d, one row per PWM period)
Writes <label>_ad3.csv (t_us, trig_V, vout_V) and <label>_fw.csv (n, t_us, vref_V, vout_adc_V, d).

usage: python -I cl_event.py "<command>" <label> <fs_hz> <pre_s> <out_dir> [--port /dev/ttyACM0]
Needs libdwf (Digilent WaveForms runtime), pyserial, numpy. Close WaveForms first.
"""
import argparse
import ctypes as C
import re
import sys
import time
from pathlib import Path

import numpy as np
import serial

N_SAMPLES = 16384          # AD3 analog-in buffer maximum
TRIG_LEVEL_V = 1.65
VIN_OK_V = (11.0, 13.0)
STATE_ARMED, STATE_DONE = 1, 2


def console(port: serial.Serial, text: str, wait_s: float = 0.4) -> str:
    port.reset_input_buffer()
    port.write(text.encode() + b"\r")
    time.sleep(wait_s)
    return port.read(16384).decode(errors="replace")


def read_until(port: serial.Serial, marker: str, limit_s: float) -> str:
    buf, t0 = "", time.time()
    while marker not in buf and time.time() - t0 < limit_s:
        buf += port.read(4096).decode(errors="replace")
    return buf


def vin_of(status: str) -> float:
    return float(re.search(r"VIN=([\d.]+)", status).group(1))


def wait_state(dwf, h, wanted: int, read_data: int, limit_s: float, what: str) -> None:
    st, t0 = C.c_byte(), time.time()
    while True:
        dwf.FDwfAnalogInStatus(h, C.c_int(read_data), C.byref(st))
        if st.value == wanted:
            return
        if time.time() - t0 > limit_s:
            raise RuntimeError(f"AD3: {what} (estado {st.value})")
        time.sleep(0.002)


def configure_ad3(dwf, h, fs: float, pre_s: float) -> None:
    dwf.FDwfAnalogInFrequencySet(h, C.c_double(fs))
    dwf.FDwfAnalogInBufferSizeSet(h, C.c_int(N_SAMPLES))
    dwf.FDwfAnalogInChannelEnableSet(h, C.c_int(-1), C.c_int(1))
    dwf.FDwfAnalogInChannelRangeSet(h, C.c_int(-1), C.c_double(50.0))
    dwf.FDwfAnalogInChannelOffsetSet(h, C.c_int(-1), C.c_double(0.0))
    dwf.FDwfAnalogInTriggerSourceSet(h, C.c_ubyte(2))          # analog-in detector
    dwf.FDwfAnalogInTriggerAutoTimeoutSet(h, C.c_double(0))    # normal mode
    dwf.FDwfAnalogInTriggerChannelSet(h, C.c_int(0))           # CH1 = TRIG
    dwf.FDwfAnalogInTriggerTypeSet(h, C.c_int(0))              # edge
    dwf.FDwfAnalogInTriggerLevelSet(h, C.c_double(TRIG_LEVEL_V))
    dwf.FDwfAnalogInTriggerHysteresisSet(h, C.c_double(0.3))
    dwf.FDwfAnalogInTriggerConditionSet(h, C.c_int(2))         # either edge
    dwf.FDwfAnalogInTriggerPositionSet(h, C.c_double(N_SAMPLES / 2 / fs - pre_s))


def capture_ad3(port: serial.Serial, command: str, fs: float, pre_s: float) -> list:
    dwf = C.cdll.LoadLibrary("libdwf.so")
    h = C.c_int()
    if not dwf.FDwfDeviceOpen(C.c_int(-1), C.byref(h)):
        raise RuntimeError("AD3 no abre (WaveForms abierto?)")
    try:
        configure_ad3(dwf, h, fs, pre_s)
        dwf.FDwfAnalogInConfigure(h, C.c_int(1), C.c_int(1))
        wait_state(dwf, h, STATE_ARMED, 0, 3.0, "no arma")
        port.reset_input_buffer()
        port.write(command.encode() + b"\r")
        wait_state(dwf, h, STATE_DONE, 1, 3.0, "sin trigger (TRIG en 1+?)")
        channels = []
        for ch in (0, 1):
            buf = (C.c_double * N_SAMPLES)()
            dwf.FDwfAnalogInStatusData(h, C.c_int(ch), buf, C.c_int(N_SAMPLES))
            channels.append(np.array(buf))
        return channels
    finally:
        dwf.FDwfDeviceCloseAll()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command"); ap.add_argument("label")
    ap.add_argument("fs", type=float); ap.add_argument("pre", type=float); ap.add_argument("out_dir", type=Path)
    ap.add_argument("--port", default="/dev/ttyACM0")
    a = ap.parse_args()

    port = serial.Serial(a.port, 115200, timeout=0.05)
    status = console(port, "s")
    print(status.strip())
    vin = vin_of(status)
    if not VIN_OK_V[0] < vin < VIN_OK_V[1]:
        print(f"ABORT: VIN={vin} V"); return 1

    trig, vout = capture_ad3(port, a.command, a.fs, a.pre)
    reply = read_until(port, "captura lista", 3.0)
    print("firmware:", " | ".join(l.strip() for l in reply.splitlines() if l.strip() not in ("", ">")))
    if "ERROR" in reply or "DISPARO" in reply:
        print("ABORT: comando rechazado o disparo"); return 1

    port.write(b"dump\r")
    dump = read_until(port, "# fin", 30.0)
    fw = np.array([[float(x) for x in line.split(",")] for line in dump.splitlines()
                   if re.match(r"^\d+,-?\d+,", line)])
    edge = int(np.argmax(np.abs(np.diff((trig > TRIG_LEVEL_V).astype(int))))) + 1
    t = (np.arange(N_SAMPLES) - edge) / a.fs
    a.out_dir.mkdir(parents=True, exist_ok=True)
    np.savetxt(a.out_dir / f"{a.label}_ad3.csv", np.c_[t * 1e6, trig, vout], delimiter=",",
               header="t_us,trig_V,vout_V", comments="", fmt="%.4f")
    np.savetxt(a.out_dir / f"{a.label}_fw.csv", fw, delimiter=",",
               header="n,t_us,vref_V,vout_adc_V,d", comments="", fmt="%.4f")
    time.sleep(0.3)
    print(console(port, "s").strip())
    print(f"AD3: evento a {edge / a.fs * 1e3:.1f} ms del inicio; filas firmware {len(fw)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
