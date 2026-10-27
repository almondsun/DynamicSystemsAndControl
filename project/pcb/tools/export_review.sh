#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/local_env.sh"
cd "$BUCK_REPO"
out=artifacts/buck-pcb-validation
release=project/pcb/release
mkdir -p "$release/fabrication-review" "$out"
kicad-cli sch erc project/pcb/buck.kicad_sch --exit-code-violations --output "$out/erc-final.rpt"
kicad-cli sch export netlist project/pcb/buck.kicad_sch --format kicadxml --output "$out/schematic.xml"
kicad-cli pcb drc project/pcb/buck.kicad_pcb --schematic-parity --exit-code-violations --output "$out/drc-final.rpt"
/usr/bin/python project/pcb/tools/verify.py "$out/schematic.xml" "$out/design-checks.json"
kicad-cli sch export pdf project/pcb/buck.kicad_sch --output "$release/schematic.pdf"
kicad-cli pcb export pdf project/pcb/buck.kicad_pcb --layers F.Fab,Edge.Cuts --mode-single --black-and-white --sketch-pads-on-fab-layers --include-border-title --output "$release/assembly.pdf"
kicad-cli pcb export gerbers project/pcb/buck.kicad_pcb --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts --output "$release/fabrication-review/"
kicad-cli pcb export drill project/pcb/buck.kicad_pcb --output "$release/fabrication-review/" --excellon-separate-th --generate-map --generate-report --report-path "$out/drill-report.txt"
for side in front back; do
    if [[ "$side" == front ]]; then layers=F.Cu,F.Silkscreen,Edge.Cuts; else layers=B.Cu,Edge.Cuts; fi
    kicad-cli pcb export svg project/pcb/buck.kicad_pcb --layers "$layers" --mode-single --fit-page-to-board --exclude-drawing-sheet --output "$release/board-$side.svg"
    rsvg-convert -w 1400 "$release/board-$side.svg" -o "$release/board-$side.png"
done
cp "$out/erc-final.rpt" "$out/drc-final.rpt" "$out/design-checks.json" "$release/"
