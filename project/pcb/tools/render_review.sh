#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/local_env.sh"
cd "$BUCK_REPO"
# Local extracted Arch binaries use build-directory lookup for 3D plugins.
[[ -e "$BUCK_TOOLS/plugins" ]] || ln -s lib/kicad/plugins "$BUCK_TOOLS/plugins"
[[ -e "$BUCK_TOOLS/pcbnew" ]] || ln -s bin "$BUCK_TOOLS/pcbnew"
/usr/bin/python project/pcb/tools/prepare_3d.py
out=project/pcb/release/report-assets
mkdir -p "$out"
KICAD_RUN_FROM_BUILD_DIR=1 kicad-cli pcb render "$BUCK_REPO/project/pcb/buck.kicad_pcb" --output "$out/pcb-3d.png" --width 1800 --height 1400 --rotate 315,0,35 --zoom 0.75 --background opaque --quality high --floor
KICAD_RUN_FROM_BUILD_DIR=1 kicad-cli pcb render "$BUCK_REPO/project/pcb/buck.kicad_pcb" --output "$out/pcb-top.png" --width 1600 --height 1600 --side top --zoom 0.9 --background opaque --quality high
kicad-cli pcb export svg project/pcb/buck.kicad_pcb --layers F.Fab,Edge.Cuts --mode-single --fit-page-to-board --exclude-drawing-sheet --output "$out/layout.svg"
rsvg-convert -f pdf "$out/layout.svg" -o "$out/layout.pdf"
"$BUCK_REPO/artifacts/buck-tools/venv/bin/python" project/pcb/tools/report_assets.py
