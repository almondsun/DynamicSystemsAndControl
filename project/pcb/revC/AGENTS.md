# Buck 12 V → 6 V — PCB Rev C (agent context)

Read this first. Scope for any agent working here: **only `project/pcb/revC/`**.
The rest of the repo (MATLAB/Simulink coursework, Buck Rev B, root `AGENTS.md`)
is unrelated to this task. Don't use it as a reference and don't modify it.

## 1. Purpose and hard constraints

- University lab board: *Sistemas Dinámicos y Control*, Universidad Nacional de
  Colombia (Manizales). Project: "Convertidor Buck con control de tensión de
  salida" (`docs/Descripcion Proyecto Buck.pdf`, in Spanish; **ignore its
  dates**, they are outdated).
- The board is for **Entrega 4** (closed-loop PID control of Vout = 6 V on real
  hardware). Entregas 2 and 3 are not done yet. The board is ordered early
  because of shipping time.
- **The board must work.** This goal is non-negotiable. It's a lab prototype,
  not a product: it's always fed from a 12 V bench supply, with a scope, DMM
  and other lab gear on hand. That's why the part count is minimal.
- **Schedule:** design frozen by the end of the week of 2026-11-02 (around
  2026-11-08). Order from JLCPCB with standard (cheap, slow) shipping. The
  board must arrive **before 2026-12-10**.
- **Assembly:** JLCPCB PCBA with as many in-stock parts as possible. When the
  board arrives, the owner only hand-solders headers, terminal blocks, test
  points and a few THT parts. The owner already bought the inductors and holds
  them in the JLC "My Parts Lib".
- Follow the JLCPCB 2-layer PCB and PCBA design rules.
- Microcontroller: **NUCLEO-L432KC** (Nucleo-32, Arduino-Nano-like footprint),
  owned by the student. It plugs in through female headers so it can be
  removed and reused. It generates the PWM and reads the ADCs. Powered from
  its own USB.

## 2. Operating point and specs (from the course PDF and Figure 1)

| Item | Value |
|---|---|
| Vin | 12 V bench supply |
| Vout | 6 V nominal; reference steps 6→7 V and 6→5 V (Entrega 3/4) |
| Load | 6 Ω nominal (1 A). Disturbance tests: R +20 % (7.2 Ω) and R −20 % (4.8 Ω) |
| L | 660 µH (reference) → here 2 × 330 µH in series |
| C | 20 µF (reference) → here 2 × 10 µF ceramic |
| fsw | 10 kHz in the professor's reference simulation (Figure 1, "PWM 10k") — **not yet confirmed for this board** |
| Reference parts | IRFZ14, 1N5822, 1N4148 bootstrap, 1 µF boot cap, 1.2 k pull-up, 2N2222 inverter, 2N3904/2N2907 totem pole |
| Control input | Reference driver is *inverting* → plant input d' = 1 − d. **This board's driver is non-inverting** (extra stage Q2), so PWM high = MOSFET on and the input is **d** (see §4). |

Load network on this board (very neat):
- J2 base load 7.2 Ω (2 × 3.6 Ω 10 W in series, off-board) → +20 % case.
- J3 36 Ω via Q6 → 7.2 ‖ 36 = **6.0 Ω** (nominal).
- J4 24 Ω via Q7 → 7.2 ‖ 36 ‖ 24 = **4.8 Ω** (−20 % case).
- Max steady output current ≈ 6 V / 4.8 Ω = 1.25 A (≈ 1.46 A at 7 V on 4.8 Ω,
  although that combination is not a required test).

## 3. Folder map

```
revC/
├── AGENTS.md                  ← this file
├── BOM/BOM_RevC.csv           ← master BOM (Spanish). LCSC #, Basic/Extended, Local = hand-solder
├── tools/place_revC.py        ← one-shot placement generator (record of placement rationale; see §9)
├── docs/Descripcion Proyecto Buck.pdf   ← assignment (Spanish, dates outdated)
└── pcb_revC/                  ← KiCad 10.0 project (kicad-cli 10.0.8 is installed)
    ├── pcb_revC.kicad_pro     ← design rules + netclasses
    ├── pcb_revC.kicad_sch     ← single-sheet schematic: POWER / DRIVER / LOAD / SENSE / NUCLEO
    ├── pcb_revC.kicad_pcb     ← layout (see §7 status)
    ├── buckRevC.kicad_sym     ← custom symbol AOD4184A (G=1, D=2, S=3)
    ├── buckRevC.pretty/L_Bourns_SRR1280.kicad_mod ← inductor footprint (pads 2.9×5.4 mm, 9.7 mm pitch)
    ├── buckRevC.pretty/IND-SMD_..-150M.kicad_mod, lib/ ← EasyEDA import leftovers (unused, lib/ is git-ignored)
    └── .history/              ← KiCad local-history git repo (auto snapshots; don't touch)
```

The KiCad install is at `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`. Write
any generated outputs (netlist, ERC/DRC reports, gerbers for checks) to a
scratch folder, never into the project folder unless asked.

## 4. Circuit summary (netlist as of 2026-11-03)

**POWER:** J1 (12 V IN) → VIN. Input caps C1–C3 10 µF/50 V 1206 + C4 100 nF
(the hot-loop cap; place it right at Q1's drain) + C5 100 µF electrolytic (DNP,
optional). The high-side N-MOSFET **Q1 AOD4184A** (TO-252) has D = VIN and
S = SW. Freewheel diode **D1 SS34** (K = SW, A = GND). L1 330 µH → VMID →
L2 330 µH → VOUT. Output caps C6, C7 10 µF/50 V (C8 is a DNP spare). J2 is the
base load.

**DRIVER** (discrete bootstrap, derived from the reference circuit):
- PWM (Nucleo D9/PA8) → R1 1 k → Q2 MMBT3904 (R2 100 k base pull-down) →
  DRV_IN (R3 10 k pull-up to VIN) → Q3 MMBT3904 base → DRV_B.
- DRV_B: R4 1.2 k (0805) pull-up to BOOT; drives the totem-pole bases
  Q4 MMBT2222A (NPN, C = BOOT) and Q5 S8550 (PNP, C = SW).
- Emitters (DRV_E) → R5 10 Ω → GATE. R6 10 k between GATE and SW.
- Bootstrap: D2 1N4148W from VIN → BOOT; C9 1 µF between BOOT and SW.
- Two inversions mean **PWM high ⇒ Q1 on**. If PWM floats or the Nucleo is
  unplugged, R2 keeps Q2 off, Q3 on and the gate low, so **Q1 stays off by
  default**. This is safer than the reference circuit, where a floating input
  turns the MOSFET fully on.

**LOAD:** Q6/Q7 AO3400A low-side switches for J3 (36 Ω) and J4 (24 Ω). Gates
are driven from LSW_A (D2/PA12) and LSW_B (D3/PB0) through 100 Ω, with 100 k
pull-downs (off by default).

**SENSE:** VIN → R9 30 k / R10 10 k → VIN_SENSE (A2/PA3). VOUT → R7 30 k /
R8 10 k → VOUT_SENSE (A1/PA1). Gain ×0.25, with 4.7 nF RC filters
(fc ≈ 4.5 kHz, 7.5 kΩ source impedance).

**NUCLEO:** J5 = CN3, J6 = CN4 (1×15 female sockets, 2.54 mm). Pins used:
CN3-4 GND, CN3-5 LSW_A, CN3-6 LSW_B, CN3-12 PWM, CN4-2 GND, CN4-10 VIN_SENSE,
CN4-11 VOUT_SENSE. All other pins are no-connect (Nucleo VIN/5V/3V3 are **not**
tied to the board).
Pin-function mapping (D9 = PA8 = TIM1_CH1, A1 = PA1, A2 = PA3, D2 = PA12,
D3 = PB0) is from memory of ST UM1956. **Still to be confirmed against the
datasheet and the physical board. The header row spacing is still to be
measured** (Arduino Nano/Nucleo-32 is expected to be 15.24 mm / 600 mil).

**Test points:** TP1 VIN, TP2 SW, TP3 GATE, TP4 VOUT, TP5 PWM, TP6–TP8 GND.
**Mounting:** H1–H4 M3 (3.2 mm NPTH). Their use is undecided because of board
space.

## 5. Assembly / sourcing split

- **JLC PCBA (SMD):** all resistors, ceramic caps, Q1–Q7, D1, D2, L1/L2.
  Extended parts (each adds a JLC feeder fee): Q1 C99124, L1/L2 C2041412
  (already bought, in My Parts Lib). Everything else is Basic per the BOM.
- **Hand-solder (local):** J1–J4 terminal blocks (KF301, check 5.0 vs 5.08 mm
  pitch), J5/J6 sockets, test points, optional C5, optional M3 standoffs.
- The LCSC numbers in the BOM have **not yet been verified** against the JLC
  catalogue (stock, Basic/Extended status, package, pinout). Check especially
  C105432 (S8550 SOT-23), C8512 (MMBT2222A), C2041412 (inductor value/current).

## 6. Design rules currently in `pcb_revC.kicad_pro`

- Min clearance 0.2 mm, min track 0.2 mm, copper-to-edge 0.3 mm, vias
  0.6/0.3 mm. All within JLC 2-layer standard capability.
- Track widths are preset to 0.25, 0.5 and 1.5 mm.
- Netclasses: Default 0.25 mm; Power 1.5 mm (via 0.8/0.4); Drive (no
  overrides).
- Netclass patterns are entered as a single comma-separated string
  (`"VIN, SW, VOUT, VMID, LOAD_A, LOAD_B"` and `"GATE, BOOT, DRV_E, DRV_B"`).
  KiCad matches patterns one entry per row, so these probably match no nets.
  **To fix/verify** (see §8).

## 7. Status

| Date | State |
|---|---|
| 2026-11-02 | Schematic finished (commit `5ad943b`). kicad-cli ERC: 0 errors / 0 warnings (4 check types ignored in project settings). |
| 2026-11-03 | `pcb_revC.kicad_pcb` is **empty**: no footprints, no Edge.Cuts. The owner confirmed that no layout exists yet; only the schematic is done. Agent review started; this file was created. |
| 2026-11-03 | The owner ran "Update PCB from Schematic". The agent then: fixed the netclass patterns (one per row; verified Power/Drive resolve on pads); set H1–H4 to `on_board no` in the schematic (no M3 holes) and removed their footprints; generated the **first placement draft** with `tools/place_revC.py` (KiCad pcbnew API). Board 78.5 × 57 mm, 2 layers. DRC: 0 errors, 0 courtyard overlaps, schematic parity OK; 82 unconnected (no routing yet); silk warnings left for the final cleanup. Backups of the pre-placement files are in the agent's scratchpad only. |

### 7.1 Placement draft (2026-11-03): layout rationale

Board outline: (100,100)–(178.5,157) mm. Power flows left → right along the
top; the driver sits under Q1; the NUCLEO is along the bottom.

- **Input / hot loop:** J1 is at the left edge (wire entry faces out; pin 1 VIN
  top). C1–C3 + C4 are vertical, GND pads up, VIN pads down next to the Q1 tab.
  Q1 is at rot 180 (tab = VIN faces the caps, leads face L1). D1 lies across
  the top of Q1: K beside Q1's source, A beside C4's GND. Loop: C4 → tab → S →
  D1 K → D1 A → C4 GND, about 13 × 4 mm. **Route it on the top layer with wide
  copper.**
- **Inductors:** L1 at rot 180 (pad 2 = SW faces Q1's source, 3.5 mm), L2 at
  rot 0. VMID pads face each other (4.2 mm).
- **Output:** C6–C8 between L2 and the terminals. J2/J3/J4 are stacked on the
  right edge, wire entry facing out. Each block has pin 2 *above* pin 1
  (J2: GND/VOUT, J3: LOAD_A/VOUT, J4: LOAD_B/VOUT).
  Routing note: the VOUT pins alternate with the LOAD pins. Plan to run the
  VOUT bus along the *right* of the J pins (x ≈ 176, under the terminal
  bodies), or use short bottom-layer jumps for LOAD_A/LOAD_B.
- **Load switches:** Q6+R11+R13 sit beside J3; Q7+R12+R14 beside J4. LSW_A
  and LSW_B come from J5.5/J5.6 through the empty middle area.
- **Driver** (under Q1, y 115–127): R5 runs straight down from Q1's gate
  (3.5 mm). R6 sits between the gate and the SW trace. The SW trace comes down
  from L1 pad 2 (x ≈ 132.7, under the L1 body) to Q5.C, R6 and C9. Q4 (rot
  180) and Q5 (rot 0) have their emitters facing R5. BOOT is a short line at
  y ≈ 124: D2.K → R4.1 → C9.1, with a short hop up to Q4.C. R4.2 is 1.9 mm
  from Q4.B. DRV_E and DRV_B inherently cross between two SOT-23s, so **one via
  on DRV_B** is expected. The chain Q3 ← Q2 ← R1 runs towards the PWM pin
  J5.12.
- **Test points:** TP3 GATE is next to R5/Q1. TP2 SW + TP7 GND sit side by
  side under L1. TP4 VOUT + TP8 GND are by the output caps. TP1 VIN + TP6 GND
  are under J1/C5. TP5 PWM is by R1.
- **NUCLEO:** J5 = CN3 is the top row (pins y = 134), J6 = CN4 the bottom row
  (y = 149.24), 15.24 mm apart. Pin 15 is at the left board edge, because the
  USB end is assumed to be the pin-15/D12-D13 end (Arduino Nano convention,
  **not verified**). Both NUCLEO ends are kept free of tall parts (the
  terminal blocks end at y = 137, above the pin-1-end plug corridor). The
  approximate 50.3 × 18 mm outline is drawn on User.Drawings only.
- **Sense:** the R7–R10 / C10–C11 row sits just below J6.10/J6.11 (≈ 3.3 mm
  to the ADC pins) for accessibility (not under the NUCLEO). Take the VIN and
  VOUT taps from the input caps and from the output caps/J2.
- Board size isn't a cost driver (< 100 × 100 mm at JLC). The bottom-right
  area is intentionally free (plug corridor plus routing space).

## 8. Open issues / review log

Keep this list updated: change the status, don't delete entries.

| # | Area | Issue | Status |
|---|---|---|---|
| 1 | Layout | First placement draft done (§7.1). Next: owner review in KiCad, then routing. Silk cleanup at the end (ref text thickness 0.15 < 0.18 project rule, overlapping refs). | review |
| 2 | Rules | **Fixed 2026-11-03:** netclass patterns are now one per row (Power/Drive resolve). Original issue: patterns were comma-joined, so they matched nothing. Use one pattern per row (VIN, SW, VOUT, VMID, LOAD_A, LOAD_B → Power). GND: the owner will use a GND pour, placed last (Altium habit). Agreed, provided the hot-loop and output returns are short direct top-layer copper, power pads use solid or wide-spoke zone connections, and DRC shows no unconnected islands. | open |
| 3 | Power | fsw: the owner is leaning towards **20 kHz** (to be justified to the professors). At 10 kHz: ΔI_L ≈ 0.45 A p-p, peak ≈ 1.48 A at 1.25 A load (> Isat 1.4 A), ΔVout ≈ 0.28 V p-p (more with DC-biased ceramics), audible. At 20 kHz: ΔI ≈ 0.23 A, peak ≈ 1.36 A, ΔVout ≈ 0.07 V. Inductor heating at −20 % is mostly I²·DCR (Irms 1.1 A < 1.25 A), so fsw barely changes it. | leaning 20 kHz |
| 4 | Model | Driver is non-inverting, so the input is d (not d'). Inductor DCR ≈ 2 × 0.6 Ω means d ≈ 0.6 (not 0.5) for 6 V at 1 A. Ceramic output C derates with DC bias (an LCR meter at 0 V bias overstates it). All of this matters for Entregas 1–4. | note |
| 5 | Driver | Totem-pole off-state is referenced to GND through Q3, not SW (same as the reference design). Expected Vgs(off) ≈ 0–1 V. Acceptable, but check TP3/TP2 on the scope. Propagation delay of the Q2/Q3 saturated stages limits fsw and min/max duty. | verify |
| 6 | Test points | TestPoint_THTPad D1.5 mm / drill 0.7 mm can't accept 2.54 mm header pins (need ~1.0 mm drill). The owner plans to solder test-point headers. | open |
| 7 | Nucleo | Confirm the CN3/CN4 pinout (UM1956). Row spacing **assumed 15.24 mm** for now; the owner will measure it and J5/J6 will be adjusted. | open |
| 8 | BOM | Verify LCSC parts/stock and Basic/Extended status. The CSV lists C5/C8 at qty 0 (DNP), consistent with the schematic. | open |
| 9 | Mech | **Decided: no M3 holes.** H1–H4 are `on_board no` in the schematic, footprints removed, BOM row qty 0. | closed |
| 10 | Libs | Inductor 3D model path is relative to `lib/`, which is git-ignored, so the 3D view breaks on a fresh clone. Cosmetic only. | low |

## 9. Decisions log

- Two 330 µH SRR1280-331K in series (= 660 µH reference). Inductors already
  purchased. Don't change them.
- Microcontroller on removable female headers (reuse of the NUCLEO-L432KC).
- Switched-load network 7.2 / 6 / 4.8 Ω for the ±20 % disturbance tests.
- 2026-11-03: no mounting holes (board space).
- 2026-11-03: GND is handled as the last copper pour (owner's Altium habit), not
  in the Power netclass.
- 2026-11-03: placement is done by script (`tools/place_revC.py`); after that,
  edits are made manually in KiCad. **Don't re-run the script** once the owner
  has moved parts by hand.

## 10. How to re-check quickly

```sh
K="/c/Program Files/KiCad/10.0/bin/kicad-cli.exe"
"$K" sch erc --severity-all -o <scratch>/erc.rpt pcb_revC/pcb_revC.kicad_sch
"$K" sch export netlist --format kicadxml -o <scratch>/net.xml pcb_revC/pcb_revC.kicad_sch
"$K" pcb drc --severity-all --schematic-parity -o <scratch>/drc.rpt pcb_revC/pcb_revC.kicad_pcb
```
