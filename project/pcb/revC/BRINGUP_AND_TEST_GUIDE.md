# Buck Rev C: bring-up and Entrega 4 test guide

This guide covers what to do from the day the board arrives until the four
Entrega 4 tests are done. Follow the sections in order. Section 4 (first
power-up) is the one that protects the board; don't skip its steps.

Expected values below come from the design checks in `AGENTS.md` (§8 #11, #12,
#17, #20, #21): ngspice simulations with datasheet parameters and the inductor
DCR at its 0.6 Ω maximum. Real readings will be close but not identical.

---

## Safety rules (read once, apply always)

| Rule | Why |
|---|---|
| Set the bench supply to **12.0 V** with a **current limit**: 100 mA for the first checks, then **1.5 A** for normal work. Never above 15 V. | The required tests draw at most 0.85 A. The limit keeps any short or wiring mistake survivable. Above ~20 V the gate exceeds its rating. |
| Check **J1 polarity** before every power-up ("+12V" / "GND" are printed on both sides). | A reversed supply drives current through D1 and Q1's body diode. The current limit saves the board; without a limit it burns. |
| **Scope ground clip only on a GND test point** (TP6, TP7, TP8). Never on SW (TP2), GATE (TP3) or BOOT (TP9). | The scope ground and the PC's USB (through the NUCLEO) are both tied to mains earth. A ground clip on SW shorts the switching node. |
| Plug or unplug the NUCLEO **only with the 12 V off**. Its **USB end points to J2–J4** (the "USB ->" arrow on the board). | Plugged in rotated 180°, the NUCLEO's power pins land on the PWM and ground pins. |
| Firmware: **duty ≤ 0.85**, soft start, PWM off at boot (section 5). | At 100 % duty the bootstrap drains in ~10 ms and Q1 overheats (~4 W). That is the same symptom as Entrega 2, from a different cause. |
| Hot parts: the inductors reach **~60 °C** at the nominal load and **~80 °C** in the −20 % test, and the load resistors much more. | Don't touch them while running. Keep the −20 % test short. |
| Hold the board flat when tightening the J2–J4 screws. | Bending the board near C6–C8 can crack the ceramic capacitors. |

---

## 0. Before the board arrives

### 0.1 Parts to buy (hand-soldered, not assembled by JLC)

| Ref | Part | Qty | Notes |
|---|---|---|---|
| J1–J4 | 2-pin screw terminal, **5.0 mm pitch** (KF301-5.0-2P) | 4 | The footprint is 5.00 mm. A 5.08 mm part won't fit well. |
| J5, J6 | 1×15 female header, 2.54 mm, standard height (8.5 mm) | 2 | For the NUCLEO-L432KC. |
| TP1–TP10 | Single male header pins, 2.54 mm (break from a strip) | 10 | Optional. The 1.0 mm holes also take probe hooks or wire loops. |
| C5 | 100 µF electrolytic, 25 V or 35 V, radial 6.3 mm diameter, 2.5 mm lead spacing, 105 °C **low-ESR** (ripple ≥ 0.3 A) | 1 | Polarity: **+ = square pad**, marked on both sides. |
| Base load (J2) | 2 × 3.6 Ω, 10 W, in series = 7.2 Ω | 2 | Dissipates 5 W at 6 V, so it runs hot. |
| Load A (J3) | 36 Ω, ≥ 5 W | 1 | 1 W at 6 V. |
| Load B (J4) | 24 Ω, ≥ 5 W (10 W gives margin) | 1 | 1.5 W at 6 V. |
| Wire | ≥ 0.5 mm² (AWG 20) for J1–J4 | — | Keep the J1 leads short. |

### 0.2 Prepare the firmware now

Write and compile it before the board arrives (section 5). Start from your
Entrega 2 firmware, which already ramps the duty, clamps it and has a watchdog.
Then apply these changes:
- Move the step marker from D2/PA12 to **TRIG = A3/PA4**. On this board PA12
  drives the 36 Ω load switch.
- The driver is non-inverting, so the plant input is **d** (not d').
- Add the duty clamp, PWM-off-at-boot and the ADC/load-switch functions from
  section 5.

---

## 1. Incoming inspection (unpowered, NUCLEO out)

### 1.1 Visual
- Every part placed. **C8 is intentionally empty** (DNP spare). C5, J1–J6 and
  the TP pins are yours to solder.
- Orientation against the silkscreen:
  - Q1 (TO-252): the tab is on the side toward C1–C4.
  - D1 (SS34): its cathode band on the outline's cathode bar.
  - D2 (1N4148W): its cathode band on the outline's cathode bar.
  - Q2–Q7 (SOT-23): pin 1 matches the outline.
- No solder bridges on the SOT-23 transistors or the 0603 resistors.

### 1.2 DMM checks
Use the TP pads. "GND" means TP6, TP7 or TP8.

| From → to | Expected | If not |
|---|---|---|
| TP6 ↔ TP7 ↔ TP8 ↔ J1 pin 2 ↔ J2 pin 2 | ~0 Ω | Broken ground: don't power up. |
| TP1 (VIN) → GND | Rises to several kΩ (the caps charge) | **< 100 Ω means a short. Stop.** |
| TP4 (VOUT) → GND, no loads connected | ≥ 10 kΩ. R7 + R8 is 40 kΩ, but paths through Q1's body diode can read lower. | **< 100 Ω means a short**; check C6/C7. |
| TP3 (GATE) → TP2 (SW) | ≈ 10 kΩ or somewhat less (R6, with transistor junctions in parallel) | Near 0 Ω means a short at Q1/R5/R6. |
| **TP2 (SW) → TP4 (VOUT)**, low-Ω range | **≈ 0.9–1.2 Ω** (DCR of L1 + L2; subtract the lead resistance) | Write it down: this is R_L in your model. |
| Diode test: red on GND, black on TP2 | ≈ 0.2–0.35 V (D1 forward) | OL means D1 is missing or reversed. |
| Diode test: red on TP1, black on TP9 | ≈ 0.4–0.6 V (D2 forward) | Check D2's orientation. |

### 1.3 L and C for the model (LCR meter, 1 kHz, unpowered, no loads, NUCLEO out)
- **L:** TP2 → TP4 should read ≈ 660 µH. Each inductor is 330 µH ±10 %. The
  in-circuit reading is valid here because every parallel path is a small
  capacitance.
- **C:** TP4 → TP8 should read ≈ 20 µF (C6 + C7 at 0 V bias). At 6 V the
  ceramics lose capacitance, so the real operating value is lower, roughly
  14 µF. Get the true value from the step response in §6.

---

## 2. Hand soldering

1. **TP pins** (optional), then **C5**. Square pad = "+". Check the "+" on the
   bottom silkscreen while you solder.
2. **J1–J4**, with the wire entry facing out of the board. Support the board.
3. **J5/J6 sockets**, last:
   1. Plug both sockets onto the NUCLEO.
   2. Insert them into the board, with the USB toward J2–J4.
   3. Tack one pin at each end of each socket.
   4. Unplug the NUCLEO and solder the rest.
4. Repeat the "TP1 → GND" and ground-continuity checks from §1.2.

---

## 3. Load wiring

Each terminal block has its pin labels printed beside it, on both sides.

| Block | Connect | Pins |
|---|---|---|
| J2 | Base load 7.2 Ω (2 × 3.6 Ω in series) | VOUT ↔ GND |
| J3 | 36 Ω | VOUT ↔ 36R |
| J4 | 24 Ω | VOUT ↔ 24R |

| LSW_A (PA12) | LSW_B (PB0) | Load | Use |
|---|---|---|---|
| 0 | 0 | 7.2 Ω | +20 % disturbance |
| 1 | 0 | 6.0 Ω | **nominal** |
| 1 | 1 | 4.8 Ω | −20 % disturbance |

Mount the resistors in free air, away from the board and the wires.

---

## 4. First power-up (staged; stop at the first unexpected reading)

**How to measure:**
- Use DC coupling, with the scope ground on TP7 (next to SW) or TP8 (next to VOUT).
- **Vgs = TP3 − TP2.** Use the scope's math function (CH_A − CH_B), or an
  Analog Discovery 2 in differential mode (1+ on TP3, 1− on TP2). GATE reaches
  ~23 V relative to GND, inside the AD2's ±25 V range.
- **Bootstrap voltage = TP9 − TP2.**

### Step A: board alone (NUCLEO unplugged), 12.0 V, limit 100 mA

| Reading | Expected |
|---|---|
| Supply current | **≈ 11 mA** |
| TP4 (VOUT) | 0 V |
| TP3 (GATE), TP2 (SW) | ≈ 0 V (Q1 off by design) |
| TP9 (BOOT) relative to GND | ≈ 11.3 V |

If the supply goes into current limit, turn it off and go back to §1.2.

### Step B: NUCLEO plugged in (12 V off while you plug it)

Plug in USB, start the firmware with the PWM **off**, then turn on the 12 V.
The current should still be ≈ 11 mA, and TP5 (PWM) should read 0 V.

### Step C: open loop, low duty (limit 300 mA, LSW_A on = 6 Ω)

Command 20 kHz at d = 0.10, using the ramp.

| Reading | Expected |
|---|---|
| TP5 (PWM) | 0 / 3.3 V square wave, 20 kHz, 10 % |
| **Vgs (TP3 − TP2)** | **≈ 11 V during the on-time**, ≈ 0 V off |
| TP2 (SW) | Square wave from −0.4 V to 12 V. Some ringing on the edges is normal. |
| Bootstrap (TP9 − TP2) | ≈ 11.5 V |
| TP4 (VOUT) | ≈ 0.7 V |

### Step D: nominal open-loop point (limit 1.5 A)

Ramp d to 0.60 (6 Ω).

| Reading | Expected (simulated) |
|---|---|
| VOUT | **≈ 5.9 V** |
| Ripple at TP4 (AC coupling, short ground spring on TP8) | ≈ 0.1 V p-p at 20 kHz |
| Supply current | ≈ 0.60 A (efficiency ≈ 80 %) |
| Vgs on / bootstrap | ≈ 11.4 V / ≥ 11.5 V |
| PWM edge → Vgs edge delay | ≈ 0.1 µs turn-on, ≈ 0.3 µs turn-off |

### Step E: open-loop duty table (checks the plant before closing the loop)

| Load | d | VOUT (simulated) | Iin |
|---|---|---|---|
| 6 Ω | 0.51 | 4.98 V | 0.44 A |
| 6 Ω | 0.60 | 5.89 V | 0.60 A |
| 6 Ω | 0.70 | 6.91 V | 0.82 A |
| 7.2 Ω | 0.58 | 5.86 V | 0.48 A |
| 4.8 Ω | 0.65 | 6.13 V | 0.85 A |

The simulation uses the inductors' maximum DCR, so the real VOUT may be
slightly higher.

---

## 5. Firmware checklist (Entrega 4)

| Signal | NUCLEO pin | MCU pin | Function |
|---|---|---|---|
| PWM | D9 (CN3-12) | PA8 | TIM1_CH1, active-high: **high = Q1 on** |
| LSW_A | D2 (CN3-5) | PA12 | GPIO out: 1 = 36 Ω connected |
| LSW_B | D3 (CN3-6) | PB0 | GPIO out: 1 = 24 Ω connected |
| VOUT_SENSE | A1 (CN4-11) | PA1 | ADC (ADC1_IN6; CubeMX shows the channel) |
| VIN_SENSE | A2 (CN4-10) | PA3 | ADC (ADC1_IN8) |
| TRIG | A3 (CN4-9) | PA4 | GPIO marker for the scope, or DAC1_OUT1 (L432KC) to plot d(t) or the reference |
| GND | CN3-4, CN4-2 | — | — |
| UART | ST-LINK virtual COM port | PA2 / PA15 | Commands and data logging (don't use A7/PA2 for anything else) |

### PWM
- 20 kHz recommended (10 kHz also works, with 4× the output ripple and an
  audible whine). Confirm the frequency with your professors.
- At an 80 MHz timer clock, set ARR = 3999 for 20 kHz; d = CCR / 4000.

### Duty limits
- Clamp to **0 ≤ d ≤ 0.85** inside the function that writes CCR.
- Add **anti-windup** to the integrator. The tests need d ≤ 0.70 in steady
  state.

### Start-up and safe state
- At boot: PWM output off (CCR = 0), LSW_A = LSW_B = 0.
- **Soft start:** ramp the reference (or the duty) over ≥ 50 ms. Your Entrega 2
  ramp of 1 %/20 ms is fine.
- **Watchdog (IWDG):** a reset turns the PWM pin into an input, R2 then holds
  Q2 off, so **Q1 is off by hardware**.
- **Debugger:** don't halt at a breakpoint with the 12 V on while the PWM is
  high. If you need to halt, set TIM1 to freeze on halt with the output idle
  level low.

### ADC
- 12-bit, VREF = 3.3 V. **VOUT = code × 3.3 / 4095 × 4** (divider 30 k / 10 k).
  1 LSB ≈ 3.2 mV at VOUT.
- Calibrate the gain once against the DMM: the resistors are 1 %.
- Trigger the ADC from TIM1 at a fixed point of the PWM period (for example
  the middle of the on-time), so the ripple doesn't alias.
- There is an RC filter on each ADC pin: 7.5 kΩ / 4.7 nF, so τ = 35 µs and
  fc ≈ 4.5 kHz. Include it in the loop model.

### Steps and logging
- For every test step, set **TRIG high at the same instant** you change the
  reference or LSW, and lower it again when you return.
- Log VOUT (ADC), d and the reference over UART, so you can plot them next to
  the scope capture.

---

## 6. Plant model to use in the controller (update of Entrega 1–3)

Averaged buck with the input **d**, including the inductor resistance R_L and
the diode drop V_F:

```
Vout(s)          Vin + V_F
------- = -------------------------------------------------
 d(s)     L·C·s² + (L/R + R_L·C)·s + (1 + R_L/R)

DC point:  Vout = (d·(Vin + V_F) − V_F) / (1 + R_L/R)
Sensor:    H(s) = 0.25 / (1 + 35e-6·s)     (plus about 1–1.5 control periods of delay)
```

| Parameter | Value |
|---|---|
| L | Measured, ≈ 660 µH |
| R_L | Measured TP2–TP4, ≈ 1.0–1.2 Ω |
| V_F | ≈ 0.35–0.45 V |
| R | 7.2 / 6 / 4.8 Ω |
| Vin | Measured |
| C | Effective value from the step response |

Example values at R = 6 Ω, L = 660 µH, R_L = 1.2 Ω, Vin = 12 V:

| C | ωn | ζ | Gain dVout/dd |
|---|---|---|---|
| 20 µF | 9.5 krad/s (1.5 kHz) | 0.53 | ≈ 10.3 V per unit d |
| 14 µF | 11.4 krad/s | 0.60 | ≈ 10.3 V per unit d |

**Validate it before tuning:**
1. Run in open loop at 6 Ω.
2. Step d from 0.60 to 0.70, with the scope triggered on TRIG.
3. Fit ωn and ζ, and compare the gain. This is the same method as your
   Entrega 2 report.
4. Use the fitted C from then on.

---

## 7. Entrega 4 tests

### 7.1 Setup (identical for every test)

| Item | Setting |
|---|---|
| Supply | 12.0 V (measure it), limit 1.5 A |
| Loads | J2 7.2 Ω, J3 36 Ω, J4 24 Ω. Start at **nominal 6 Ω** (LSW_A = 1, LSW_B = 0). |
| Scope / AD2 | CH1 = TP4 (VOUT), DC coupled. CH2 = TP10 (TRIG). Ground on TP8. Trigger: CH2 rising edge, single shot. Window ≈ 10 ms with ≈ 2 ms before the trigger. |
| Before each test | Closed loop at Vref = 6 V, steady for ≥ 1 s |
| Repetitions | 3 captures per test; export them to CSV |

### 7.2 The four required tests

| # | Test | Action at t = 0 | Duty (expected) | Measure |
|---|---|---|---|---|
| 1 | Reference 6 → 7 V | Vref = 7 V | 0.60 → ~0.70 | Rise time, overshoot Mp, settling time (2 %), steady-state error |
| 2 | Reference 6 → 5 V | Vref = 5 V | 0.60 → ~0.51 | Same |
| 3 | Load +20 % (6 → 7.2 Ω) | LSW_A = 0 | 0.60 → ~0.58 | Max deviation ΔV, recovery time (back within ±2 %), steady-state error |
| 4 | Load −20 % (6 → 4.8 Ω) | LSW_B = 1 | 0.60 → ~0.65 | Same. **Keep this test short** (the inductors run at their current rating). |

**Processing (as in your Entrega 2 report):**
- Average VOUT over one switching period (50 µs at 20 kHz) to remove the ripple.
- Compute the metrics.
- Plot measurement and Entrega 3 simulation together, and report the errors.

**Pass criteria:**
- The specifications you set in Entrega 3 (Mp, ts).
- Steady-state error ≈ 0 (integral action), within ±2 ADC LSB (≈ ±6 mV).
- The duty never sits on the 0.85 clamp in steady state.
- No sustained oscillation.

---

## 8. Troubleshooting

| Symptom | Likely cause | Check |
|---|---|---|
| Supply in current limit at power-up | Short, reversed J1, or a scope ground on SW | §1.2 checks, J1 polarity, probe grounds |
| VOUT higher than expected and Q1 hot | Q1 not fully on: bootstrap drained (duty stuck at or near 100 %) | Vgs ≈ 11 V? TP9 − TP2 ≈ 11.5 V? Is the duty clamp working? |
| No output, PWM present at TP5 | Driver: Q2/Q3/Q4/Q5, R1–R6 | Vgs on TP3 − TP2; DRV stage soldering |
| No PWM at TP5 | Firmware or pin, or the NUCLEO rotated or off its sockets | Pin PA8/TIM1_CH1; NUCLEO orientation |
| ADC reads wrong | Gain or reference | Compare with the DMM; recalibrate the ×4 factor |
| Load step does nothing | LSW pin, Q6/Q7, or the resistor on the wrong J3/J4 pins | TP-to-pin wiring: VOUT ↔ 36R/24R |
| Large spikes on the SW or VOUT trace | Long scope ground lead | Use a spring tip: TP2 + TP7 pair, TP4 + TP8 pair |
| Audible whine | 10 kHz PWM | Normal; use 20 kHz |
| Inductors too hot to touch | −20 % load held for a long time | Normal for minutes at 4.8 Ω (~80 °C); keep that test short |

---

## 9. Quick reference: test points

| TP | Signal | Typical value (running at 6 V / 6 Ω) |
|---|---|---|
| TP1 | VIN | 12 V |
| TP2 | SW | −0.4 V ↔ 12 V square wave |
| TP3 | GATE | SW + 11 V when on (≈ 23 V relative to GND) |
| TP4 | VOUT | 6 V, ≈ 0.1 V p-p ripple |
| TP5 | PWM | 0 / 3.3 V |
| TP6, TP7, TP8 | GND | Scope ground here only |
| TP9 | BOOT | SW + ≈ 11.5 V |
| TP10 | TRIG | Firmware marker (PA4) |
