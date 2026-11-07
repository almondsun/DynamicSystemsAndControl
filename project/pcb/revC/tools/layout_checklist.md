# Buck Rev C routing review checklist (reviewer, S0)

Board: `route_work/pcb_revC/pcb_revC.kicad_pcb` (2 layers, 1 oz = 35 um, 1.6 mm FR-4, 78.5 x 60 mm).
Currents for sizing: 1.0-1.29 A rms steady, 1.4 A peak, 1.9 A fault (PID saturated, AGENTS #20).
Checker: `review/check_layout.py <board> --stage Sx`. Each row ID below is printed by the checker,
except the `MAN-R*` rows, which are manual checks on the renders.

## Stage semantics

| Kind | S0 (baseline) | S1-S3 | S4 | S5 |
|---|---|---|---|---|
| always: quality of copper that exists | WARN | FAIL | FAIL | FAIL |
| complete: unconnected, GND pours, stitching, teardrops, taps not yet routed | WARN | WARN | FAIL | FAIL |
| final: silkscreen, labels | WARN | WARN | WARN | FAIL |
| advice: rule of thumb or my own judgement | WARN | WARN | WARN | WARN |

Assumed router stages (generic, so the checker does not depend on them): S1 power copper, S2 drive,
S3 signals, S4 GND pours + stitching + teardrops + 0 unconnected, S5 silkscreen + final export.

## Sources (read 2026-11-05; local copies in `review/sources/`, text in `review/sources_txt/`)

| Key | Document |
|---|---|
| AN1149 | TI AN-1149 *Layout Guidelines for Switching Power Supplies*, SNVA021C (rev. Apr 2013), https://www.ti.com/lit/pdf/snva021 |
| SLYT614 | C. Glaser, *Five steps to a great PCB layout for a step-down converter*, TI Analog Applications Journal 1Q 2015, SLYT614, https://www.ti.com/lit/pdf/slyt614 |
| ROHM | ROHM *PCB Layout Techniques of Buck Converter*, 60AN066E Rev.004 (Jan 2024), https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf |
| BA | D. Brooks, J. Adam, *Trace Currents and Temperatures Revisited* (UltraCAD, Apr 2015), Eq. 3-2 / Table 3-1 (fit to IPC-2152 external data), https://mathscinotes.com/wp-content/uploads/2016/06/pcbtempr.pdf |
| SMPS | smps.us PCB trace calculator, curve fit to IPC-2152 Fig. 5-2, https://www.smps.us/pcb-calculator.html |
| JLC | JLCPCB PCB manufacturing capabilities, https://jlcpcb.com/capabilities/pcb-capabilities (fetched 2026-11-05) |
| KICAD | KiCad 10.0 PCB Editor manual (based on 10.0.8), https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html: *Working with zones*, *Teardrops*, *Board Setup > Constraints*, *Custom design rules* |
| SPEC | Owner-approved routing spec (in the reviewer brief) |
| AG | `project/pcb/revC/AGENTS.md` (sec. 4, 7.1; issues #2, #16, #19, #20) |

IPC-2152 width for 1 oz external copper at a 10 C rise (computed from the fits above):

| Current | BA Eq. 3-2 | SMPS Fig. 5-2 fit | IPC-2221 ext. (old, for comparison) | AN1149 15 mil/A | ROHM 1 mm/A |
|---|---|---|---|---|---|
| 1.29 A | 0.43 mm | 0.45 mm | 0.43 mm | 0.49 mm | 1.29 mm |
| 1.5 A | **0.56 mm** | **0.60 mm** | 0.53 mm | 0.57 mm | 1.5 mm |
| 1.9 A | 0.85 mm | 0.92 mm | 0.73 mm | 0.72 mm | 1.9 mm |
| 2.0 A | **0.93 mm** | **1.01 mm** | 0.78 mm | 0.76 mm | 2.0 mm |

Both IPC-2152 fits model a trace with no nearby plane, so they are conservative here (B.Cu GND plane).
By BA, a 1.5 mm trace rises about 2.4 C at 1.29 A and about 5.2 C at 1.9 A. The checker uses
**1.0 mm as the hard IPC floor** (2 A at 10 C) and the project's **1.5 mm** as the spec value.

## Checklist

| ID | Rule (adapted to this board) | Source | Measurable pass criterion | Check | Kind |
|---|---|---|---|---|---|
| DRC-1 | DRC clean apart from unconnected and silk items | JLC; SPEC | kicad-cli DRC (`--severity-all --schematic-parity`, run on a snapshot): 0 errors other than unconnected and silk | auto | always |
| DRC-2 | Fully routed at the end | SPEC | 0 `unconnected_items` | auto | complete |
| DRC-3 | Board matches the schematic | SPEC | parity ran, 0 parity issues | auto | always |
| DRC-4 | No dangling copper; no copper warnings | KICAD (via_dangling, isolated_copper, starved_thermal) | 0 track/via dangling (always); 0 other copper warnings (complete) | auto | always / complete |
| DRC-5 | Custom rules enforce the Power and Drive widths | SPEC; KICAD *Custom design rules* (file starts `(version 1)`, the last matching rule wins, `track_width` checks only track and arc segments) | `<board>.kicad_dru` exists, starts with `(version 1)`, has a Power `track_width (min >= 1.5mm)` rule and a Drive `(min >= 0.5mm)` rule, and DRC reports no rule-syntax errors. **Probe:** a throw-away copy gets a 1.0 mm VMID stub and a 0.3 mm GATE stub, and DRC must flag both as `track_width`. Tested: kicad-cli 10.0.8 silently ignores a broken rule file (exit 0, no message) | auto | always |
| RUL-1 | Project rules and netclasses | SPEC; AG sec. 6 | min clearance 0.2; copper-to-edge >= 0.3; Default 0.25/0.2; Power 1.5 mm, clearance 0.3, via 0.8/0.4; Drive 0.5; vias 0.6/0.3; text 1.0/0.18; min spokes >= 2; VIN, SW, VMID, VOUT, LOAD_A, LOAD_B resolve to Power and GATE, BOOT, DRV_E, DRV_B to Drive. Advisory: hole clearance >= 0.28 (JLC PTH-to-track) | auto | always |
| RUL-2 | JLC 2-layer, 1 oz capability on the real geometry | JLC: PTH annular ring >= 0.18 (rec. 0.25); via drill >= 0.15 and via dia >= drill + 0.1; via hole to track 0.2; PTH to track 0.28 (rec. 0.35); routed edge >= 0.2 | every PTH ring >= 0.18 (WARN < 0.25); every via within limits; hole edge to other-net copper >= 0.28 mm for PTH and >= 0.2 mm for vias (WARN < 0.35) | auto | always |
| PWR-1 | Hot loop minimal (placement) | SLYT614 step 1; ROHM sec. 1, 3; AN1149 sec. 5 | area of the pad-centre polygon C4.1>Q1.2>Q1.3>D1.1>D1.2>C4.2 equals the baseline (32.5 mm^2) within 0.5 mm^2, so no part was moved | auto | always |
| PWR-2 | Hot loop and bulk-cap links on F.Cu only, with a solid GND return | SLYT614 step 3 ("no vias should be used to route these components"); ROHM sec. 3 (input cap and diode on the IC's layer, no vias), sec. 8 | each pair C4.1-Q1.2, Q1.3-D1.1, D1.2-C4.2, C1..C3.1-Q1.2, C1..C3.2-D1.2 is joined by F.Cu copper alone. FAIL if a pair is joined only through B.Cu/vias; WARN (complete) if still open | auto | always / complete |
| PWR-3 | Power nets on F.Cu only | SPEC; SLYT614 step 3; ROHM sec. 3 | 0 VIN/SW/VMID/VOUT/LOAD tracks or zones on B.Cu; 0 power vias | auto | always |
| PWR-4 | Power tracks >= 1.5 mm; narrow copper only as legal taps | SPEC; BA/SMPS (floor 1.0 mm at 2 A); AN1149 sec. 5 (>= 15 mil/A) | every power segment >= 1.5 mm, except "taps": a narrow group that ends on a listed low-current pad (VIN: R3.1, R9.1, TP1 at >= 0.25 and D2.2 at >= 0.5; VOUT: R7.1, TP4 >= 0.25; SW: Q5.3, R6.2, C9.2, TP2 >= 0.5) and attaches to the wide copper at one point. Any narrow group in series between power pads FAILs | auto | always |
| PWR-5 | Zone and track necks wide enough | SPEC (SW >= 2 mm; Power 1.5 mm); BA/SMPS; KICAD (zone *Minimum width*; `connection_width` constraint) | erosion test: the net's F.Cu copper is shrunk by w/2, and every joined cluster of terminal pads must stay joined. A terminal counts as reached when the eroded copper comes within w/2 of its pad edge (plus the relief gap for thermal pads), so 0603/1206 pads narrower than w are not counted as necks. w = 1.5 mm for VIN, VMID, VOUT, LOAD_A, LOAD_B and the hot-loop GND (C1..C4.2, D1.2); w = 2.0 mm for SW (Q1.3, D1.1, L1.2). The output also says whether a failed neck still meets 1.0 mm | auto | always |
| PWR-6 | SW node copper small | SLYT614 step 2 (SW copper is a parasitic-capacitor plate, so keep it small); ROHM sec. 5 ("do not expand copper area more than needed") | non-pad SW copper on F.Cu <= 80 mm^2 (my judgement; the minimal Q1.3-D1.1-L1.2 zone plus the driver branch is about 20-40 mm^2) | auto | advice |
| PWR-7 | Nothing routed through the hot loop | SLYT614 step 1 ("route ... so that nothing else can be routed in its path") | 0 other-net F.Cu tracks/vias inside the hot-loop polygon | auto | always |
| PWR-8 | B.Cu is an unbroken GND plane under the power stage | SPEC; AN1149 sec. 5 (ground plane on both sides); SLYT614 step 5 | 0 non-GND B.Cu tracks in the hot-loop box (FAIL), none elsewhere under the stage (WARN); B.Cu GND fill covers >= 90 % of the hot-loop box (complete); >= 85 % of the stage box and >= 75 % of the board (WARN) | auto | always / complete |
| PWR-9 | Input and output cap grounds apart | ROHM sec. 3, 6 (CIN and CO grounds 1-2 cm apart) | min distance C1..C4.2 to C6..C8.2 >= 10 mm (placement, currently 42 mm) | auto | advice |
| DRV-1 | Drive nets >= 0.5 mm | SPEC | all GATE, BOOT, DRV_E, DRV_B segments >= 0.5 mm | auto | always |
| DRV-2 | Drive nets on F.Cu; one jump on DRV_B | SPEC; AG sec. 7.1 | vias: DRV_B <= 2 (one jump), GATE/BOOT/DRV_E = 0 | auto | always |
| DRV-3 | Gate loop small | SPEC; SLYT614 step 4 (short, direct) | pad-centre gate-loop area reported (17.5 mm^2 at placement); routed GATE and DRV_E each <= 10 mm (judgement) | auto | advice |
| SIG-1 | Signals >= 0.25 mm | SPEC (JLC min is 0.10) | every non-power, non-drive segment >= 0.25 mm; GND tracks < 0.5 mm flagged; no copper on `unconnected-*` nets | auto | always |
| SIG-2 | Sensitive traces away from SW copper | AN1149 sec. 2 (feedback far from inductor and noisy traces); ROHM sec. 7(d); SLYT614 step 2 | edge gap from VOUT_SENSE, VIN_SENSE, the R7/R9 taps and TRIG to SW copper (pads, tracks, fill) on the same layer >= 1.0 mm FAIL / >= 3.0 mm WARN; PWM, LSW_A, LSW_B >= 0.5 mm FAIL / >= 2.0 mm WARN; 0 crossings over or under SW copper on the other layer. **The distances are my judgement; the sources give no number** | auto | always |
| SIG-3 | No signal under L1/L2/D1 | ROHM sec. 7(d) ("do not wire directly below the inductor and diode"), sec. 5 (Fig. 6-c) | 0 sense segments under the 12.5 x 12.5 mm L1/L2 bodies or the D1 body (FAIL); other non-power signals there WARN | auto | always |
| SIG-4 | Kelvin VOUT tap from C6/C7; VIN tap from the input caps | SPEC; ROHM sec. 7(b) ("connected after output capacitor or at both ends of output capacitor"); SLYT614 step 3 ("short and direct to the output capacitor"); AG sec. 7.1 | the R7.1 tap attaches to VOUT copper within 2.5 mm of C6.1 or C7.1 (C8.1 WARN), and runs <= 2 mm inside VOUT zone fill. The R9.1 tap attaches within 2.5 mm of C1..C5 pad 1 | auto | always / complete |
| SIG-5 | ADC filter caps at the ADC pins; short ADC nets | AN1149 sec. 3, 4 (filter parts close to the IC); SLYT614 step 4 | C10.1-J6.11 and C11.1-J6.10 <= 6 mm (placement: 3.3 mm); VOUT_SENSE and VIN_SENSE routed <= 15 mm (judgement) | auto | advice |
| SIG-6 | Short bottom jumps | SPEC | each connected B.Cu run of a non-GND net <= 10 mm | auto | advice |
| SIG-7 | PWM and LSW routes as specified | SPEC; AG #19 | PWM: 0 vias, length <= 1.5 x straight line (J5.12-R1.1 + TP5); LSW_B runs between the socket rows | auto | advice |
| GEO-1 | Segments at multiples of 45 deg | ROHM sec. 11 (bend at 45 deg or round); SPEC | every straight segment within 1 deg of k x 45 deg (FAIL), within 0.05 deg (WARN, typically a pad-centre offset); 0 zero-length segments; arcs allowed | auto | always |
| GEO-2 | No 90 deg or acute junctions | ROHM sec. 11; SPEC | 2-segment joint angle > 90 deg; >= 3-way junction: no angle < 90 deg (FAIL), a 90 deg T is a WARN (my judgement: no source bans a T). Joints inside same-net pads, vias or fill are skipped | auto | always |
| GEO-3 | No dangling stubs or one-layer vias | SPEC; KICAD (track_dangling, via_dangling) | 0 track ends touching nothing of their net; every via connected on both layers; 0 duplicate or overlapping same-net segments (WARN) | auto | always |
| VIA-1 | Via sizes | SPEC; JLC | Power vias 0.8/0.4; others 0.6/0.3 or 0.8/0.4; through vias only; within the JLC limits | auto | always |
| VIA-2 | Power layer changes | SPEC (>= 2 vias); AN1149 sec. 5 (1 via per 200 mA); SLYT614 step 5 (1 via per A); ROHM sec. 10-3 (0.4 mm hole = 0.6 A) | none expected (PWR-3). If present, each cluster has >= 2 vias, and I recommend >= 4 x 0.4 mm drill for 1.9 A (ROHM) | auto | always |
| VIA-3 | GND stitching around the power stage | SPEC (about every 5 mm, next to the power GND pads); AN1149 sec. 5; SLYT614 step 5 ("vias ... at the input- and output-capacitor's ground terminal") | a GND via within 3 mm of each of C1..C4.2, D1.2, C6.2, C7.2; worst distance from any F.Cu GND-fill point in the power-stage box to the nearest GND via <= 5 mm | auto | complete |
| ZON-1 | Zone inventory | KICAD *Working with zones* | lists net, layer, priority, pad connection, relief gap and spoke width, min width, island mode, fill area and outline count | auto | info |
| ZON-2 | GND pours lowest priority | SPEC; KICAD ("lower-priority zones keep clearance to the filled areas of higher-priority zones"; KiCad 10 priority = Zone Manager order) | a board-size GND pour on F.Cu and on B.Cu, each at the lowest priority on its layer; every overlapping power zone has a higher priority | auto | complete |
| ZON-3 | 0 islands and 0 floating copper | SPEC; KICAD *Remove islands* ("islands are never removed from zones that are electrically unconnected") | per-net connectivity graph (overlap per layer, vias and PTH pads join the layers): every fill outline, track and via has a path to a pad | auto | always |
| ZON-4 | Fills up to date | KICAD ("make sure zone fills are up-to-date before generating outputs") | an in-memory refill of a second copy changes no zone-layer area by more than max(0.5 mm^2, 1 %) | auto | complete |
| ZON-5 | Zone fill >= 0.5 mm from the edge | SPEC (JLC routed edge >= 0.2) | 0 fill area within 0.5 mm of Edge.Cuts | auto | always |
| ZON-6 | Pad connections | SPEC; AG #2 (solid or wide-spoke power pads); KICAD (pad connection modes, `min_resolved_spokes`) | SMD power pads (C1-C4, C6-C8, Q1, D1, L1, L2) inside a same-net zone are >= 98 % covered (solid). THT pads in a zone have >= 2 spokes per layer; power THT pads (J1-J4, C5) have total spoke width >= 1.0 mm (FAIL) / >= 1.5 mm (WARN); a solid THT connection WARNs (hand soldering) | auto | always |
| TDR-1 | Teardrops | SPEC; KICAD *Teardrops* (default: no teardrop on a pad inside a zone; none if track > 90 % of pad) | every via, and every pad with a track narrower than 90 % of its smaller dimension that is not inside a same-net zone, overlaps a teardrop zone of its net | auto | complete |
| SLK-1 | Silk text size | SPEC (1.0 / 0.18 mm); JLC (min text height 1.0 mm; min line width 0.15 mm; preferred width-to-height ratio 1:6) | every visible silk text height >= 1.0 mm and stroke >= 0.18 mm | auto | final |
| SLK-2 | 0 silk overlaps, 0 silk on pads, 0 edge clips | SPEC; JLC (pad to silkscreen 0.15 mm) | DRC: 0 silk_overlap, silk_over_copper, silk_edge_clearance, text_height, text_thickness, mirror warnings | auto | final |
| SLK-3 | References visible, not under a body | SPEC | each non-TP reference visible on F/B.Silkscreen and not overlapping any F.Fab body box (or the 12.5 mm inductor bodies); under the NUCLEO outline WARNs; TP references on silk WARN (spec moves them to F.Fab) | auto | final |
| SLK-4 | Required labels | SPEC; AG #20 (polarity labels at J1-J4) | F.Silkscreen: each TP's net name within 3 mm; J1 "+12V" and "GND", J2 "VOUT" and "GND", J3 "VOUT" and "36R", J4 "VOUT" and "24R" within 8 mm; "CN3"/"CN4"; a title (BUCK / REV C); a text with "15V" and "1.5A" | auto | final |
| SLK-5 | Bottom labels for the hand-soldered parts | SPEC | each of J1-J6, C5 and TP1-TP10 has a **mirrored** B.Silkscreen text within 4 mm | auto | final |
| SLK-6 | Each label sits next to its pin | SPEC; AG sec. 7.1 (pin 2 above pin 1) | single-word labels: the nearest pad of the connector has the matching net (+12V to VIN, 36R to LOAD_A, ...); combined "A/B" labels are listed for manual check | auto + manual | final |
| SLK-7 | Silk line width | JLC (min line width 0.15 mm; the row describes characters) | advisory: count of silk graphic lines < 0.15 mm (KiCad library outlines are 0.12 mm) | auto | advice |
| MAN-1 | No footprint moved | SPEC | `cmp.py`-equivalent diff against `unrouted_baseline.kicad_pcb`: 0 changes in position, rotation, layer or footprint ID | auto | FAIL at any stage |
| MAN-2 | JLC SMD spacing | AG #19 (JLC "Minimum Spacing Requirements for SMD Components") | `jlc_spacing.py` reports 0 violations | auto | FAIL at any stage |
| MAN-3 | Fabrication outputs | JLC; SPEC | `kicad-cli pcb export gerbers` and `export drill` exit 0 and produce the F/B Cu, Mask and Silkscreen layers, Edge_Cuts and a .drl | auto | FAIL at any stage |
| MAN-4 | Outline unchanged | SPEC; AG sec. 7 | Edge.Cuts bounding box and area equal the baseline (100,100)-(178.5,160), 4710 mm^2 | auto | FAIL at any stage |
| MAN-R1 | Switching loops curl the same way | AN1149 sec. 5 ("arrange the components so that the switching current loops curl in the same direction") | on render_top: the Q1-on loop (C4>Q1>L1>Cout>GND>C4) and the Q1-off loop (D1>L1>Cout>GND>D1) circulate in the same sense | manual-render | advice |
| MAN-R2 | Gate-loop return path | SLYT614 step 4; AG sec. 7.1 (SW branch from L1.2 to Q5.C/R6/C9) | the SW branch to Q5.3, C9.2 and R6.2 leaves the SW copper next to Q1.3 (source), so gate-discharge current does not share the D1 path | manual-render | advice |
| MAN-R3 | Copper looks sane | ROHM Fig. 6-b (no unnecessary wide copper on SW); KICAD | top and bottom renders: no slivers, no necks pinched by vias, the B.Cu plane is not slotted between the power stage and J5/J6 GND | manual-render | advice |
| MAN-R4 | Quiet-ground returns | SLYT614 step 5; ROHM sec. 8 | R8.2, R10.2, C10.2, C11.2 and the NUCLEO GND pins (J5.4, J6.2) return through plane areas the hot-loop current does not cross. Judgement; see the conflicts below | manual-render | advice |

## Where the spec and the sources disagree (reported to the owner, not enforced as FAIL)

1. **Vias per power layer change.** The spec says >= 2 vias. AN1149 sec. 5 says 1 via per 200 mA
   (>= 7 at 1.29 A). SLYT614 says 1 via per A (2). ROHM sec. 10-3 gives 0.6 A for a 0.4 mm hole
   (>= 3 at 1.29 A, >= 4 at 1.9 A). Only SLYT614 supports ">= 2". This is moot if power stays on F.Cu (PWR-3).
2. **GND plane under the inductors.** The spec wants B.Cu unbroken under the power stage.
   ROHM sec. 5 / Fig. 6-c advises no ground layer directly under the inductor (eddy currents lower L
   and Q), unless the inductor is closed-magnetic. AN1149 sec. 5 favours planes on both sides. The
   SRR1280 is a shielded part, so I judge the plane acceptable.
3. **Single GND vs split power/quiet ground.** SLYT614 step 5 and ROHM sec. 8 recommend separate
   power and signal grounds joined at one point. ROHM says never to tie the noisy input/diode ground
   into the signal-ground layer. The spec's stitched F+B pours follow AN1149 sec. 5 instead. On a
   2-layer board I accept the stitched plane, with MAN-R4 as the safeguard.
4. **Custom rule "Power >= 1.5 mm" vs the spec's own 0.25 mm VOUT Kelvin tap.** VOUT is in Power, and
   so are the VIN branches to R3/R9/D2 and the SW branch to Q5/R6/C9/TP2. A netclass-wide
   `track_width (min 1.5mm)` either flags these as DRC errors or forces 1.5 mm tracks onto 0603 pads.
   The .kicad_dru needs an exemption for the taps. Also, KICAD's `track_width` checks only
   track/arc segments, so it does not see zone necks; PWR-5 and `connection_width` cover those.
5. **Editing .kicad_dru by script.** KICAD says the file "should not be edited with an external text
   editor; always use the Custom Rules page". A scripted file is acceptable only if DRC runs clean of
   rule errors (DRC-5). The owner should press "Check rule syntax" once in Board Setup.
6. **Width rule of thumb for the fault case.** ROHM's ">= 1 mm per A" gives 1.9 mm at 1.9 A, but the
   spec has 1.5 mm. IPC-2152 (BA) puts a 1.5 mm trace at about +5 C at 1.9 A, so 1.5 mm is adequate.
7. **Teardrops "on pads and vias".** KICAD's defaults skip pads inside zones and tracks wider than
   90 % of the pad, so zone-connected power pads get none. TDR-1 follows KiCad's eligibility rules.
8. **JLC hole clearance.** The project's min_hole_clearance is 0.25 mm, below JLC's PTH-to-track
   0.28 mm (rec. 0.35 mm). It is not binding with the current annular rings, but set it to 0.3 mm.
