"""Entrega 4 test suite (BRINGUP_AND_TEST_GUIDE.md section 7.2) on the Buck Rev C.

Precondition: PI active at vref 6 V, nominal load (A=1, B=0), 12 V supply on.
For each test and repetition: hold 1.5 s at the nominal point, run the event with
cl_event.py (AD3 + firmware captures), then return to the nominal point.

usage: python -I run_suite.py <out_dir> [--reps 3] [--port /dev/ttyACM0]
"""
import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

import serial

AD3_FS_HZ = "250000"   # 65.5 ms window
AD3_PRE_S = "0.005"
SETTLE_S = 1.5
# (label, event command, return command)
TESTS = [("ref_up_6_7", "v 7", "v 6"),
         ("ref_down_6_5", "v 5", "v 6"),
         ("load_plus20", "a 0", "a 1"),
         ("load_minus20", "b 1", "b 0")]


def console(port: serial.Serial, text: str, wait_s: float = 0.5) -> str:
    port.reset_input_buffer()
    port.write(text.encode() + b"\r")
    time.sleep(wait_s)
    return port.read(16384).decode(errors="replace")


def nominal_ok(port: serial.Serial) -> bool:
    s = console(port, "s")
    vref = re.search(r"vref ([\d.]+) V \(actual ([\d.]+)\)", s)
    return ("Modo PI" in s and "A=1 B=0" in s and vref is not None
            and vref.group(1) == "6.000" and vref.group(2) == "6.000")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--port", default="/dev/ttyACM0")
    a = ap.parse_args()
    event_script = Path(__file__).with_name("cl_event.py")

    for label, event, ret in TESTS:
        for rep in range(1, a.reps + 1):
            with serial.Serial(a.port, 115200, timeout=0.05) as port:
                if not nominal_ok(port):
                    print(f"ABORT antes de {label} #{rep}: no esta en PI 6 V / 6 ohm"); return 1
            time.sleep(SETTLE_S)
            name = f"{label}_r{rep}"
            print(f"=== {name}: '{event}' ===", flush=True)
            res = subprocess.run([sys.executable, "-I", str(event_script), event, name, AD3_FS_HZ, AD3_PRE_S,
                                  str(a.out_dir), "--port", a.port], capture_output=True, text=True)
            summary = [l for l in res.stdout.splitlines() if l.startswith(("firmware:", "AD3:", "ABORT"))]
            print("\n".join(summary) or res.stdout[-500:], res.stderr[-500:], flush=True)
            with serial.Serial(a.port, 115200, timeout=0.05) as port:
                reply = console(port, ret)
                if res.returncode != 0 or "DISPARO" in reply:
                    console(port, "x")
                    print(f"ABORT en {name}: PWM apagado por seguridad. {reply.strip()}"); return 1
            time.sleep(SETTLE_S)
    with serial.Serial(a.port, 115200, timeout=0.05) as port:
        print(console(port, "s").strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
