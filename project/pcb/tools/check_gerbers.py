#!/usr/bin/env python3
"""Read manufacturing exports independently of KiCad and render both sides."""
import json
from pathlib import Path
from gerbonara import LayerStack
ROOT=Path(__file__).resolve().parents[1]
stack=LayerStack.open(ROOT/'release/fabrication-review')
for side in ['top','bottom']:
    assert (side,'copper') in stack.graphic_layers
    assert (side,'mask') in stack.graphic_layers
    (ROOT/'release'/f'gerber-{side}.svg').write_text(str(stack.to_pretty_svg(side=side)))
bounds=stack.board_bounds(); (x0,y0),(x1,y1)=bounds
assert abs(x1-x0-99)<.1 and abs(y1-y0-99)<.1,bounds
holes=len(stack.drill_pth.objects)
assert holes==158,holes
assert not stack.drill_npth.objects
result={'reader':'gerbonara 1.6.3','bounds_mm':bounds,'plated_holes':holes,'nonplated_holes':0,'copper_layers':2,'status':'PASS: exports readable; dimensions/layers/drill counts agree'}
(ROOT/'release/gerber-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
