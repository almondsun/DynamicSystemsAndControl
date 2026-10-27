"""Assemble the report from actual MATLAB exports and validation results.

Usage: python build_report.py /path/to/MATLAB/output
Requires reportlab. MATLAB does all simulation and plotting.
"""
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Preformatted,
    Table, TableStyle,
)

HERE = Path(__file__).resolve().parent
RUN = Path(sys.argv[1]).resolve()
RESULT = json.loads((RUN / "validation.json").read_text())
assert RESULT["passed"], "Refusing to publish failed simulation results"
SOURCE = (HERE / "run_dynamic_response_2.m").read_text()
FONT = Path('/usr/share/fonts/liberation')
pdfmetrics.registerFont(TTFont('Body', str(FONT / 'LiberationSans-Regular.ttf')))
pdfmetrics.registerFont(TTFont('BodyBold', str(FONT / 'LiberationSans-Bold.ttf')))
pdfmetrics.registerFont(TTFont('Code', str(FONT / 'LiberationMono-Regular.ttf')))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle('Main', fontName='Body', fontSize=9.2, leading=13,
                          spaceAfter=8, textColor=colors.HexColor('#243447')))
styles.add(ParagraphStyle('SmallText', parent=styles['Main'], fontSize=8, leading=11))
styles.add(ParagraphStyle('Heading', fontName='BodyBold', fontSize=17, leading=22,
                          spaceAfter=10, textColor=colors.HexColor('#114b70')))
styles.add(ParagraphStyle('Sub', fontName='BodyBold', fontSize=10, leading=14,
                          spaceBefore=5, spaceAfter=6))
styles.add(ParagraphStyle('Cover', parent=styles['Heading'], fontSize=29,
                          leading=35, spaceAfter=18))
styles.add(ParagraphStyle('CodeBlock', fontName='Code', fontSize=8.3, leading=11,
                          backColor=colors.HexColor('#f0f4f8'), borderPadding=7,
                          spaceBefore=4, spaceAfter=9))
story = []


def para(text, style='Main'):
    story.append(Paragraph(text, styles[style]))


def code(text):
    # Preformatted preserves MATLAB line breaks without executing anything.
    story.append(Preformatted(text, styles['CodeBlock']))


def footer(canvas, doc):
    canvas.setFont('Body', 7)
    canvas.setFillColor(colors.HexColor('#607080'))
    canvas.drawString(18*mm, 12*mm, 'Dynamic Response 2 · MATLAB simulations')
    canvas.drawRightString(192*mm, 12*mm, str(doc.page))


para('Dynamic Response 2', 'Cover')
para('MATLAB simulations, response plots and brief analysis', 'Heading')
para('Sistemas Dinámicos y Control · Universidad Nacional de Colombia')
para('Source: Juan David Bastidas Rodríguez, <i>4 Dynamic Response 2.pdf</i>, '
     '39 slides. The presentation cites Franklin, Powell and Emami-Naeini, '
     '<i>Feedback Control of Dynamic Systems</i>, 8th ed., Pearson, 2019.')
para('Scope', 'Sub')
para('Every distinct worked example is included: partial fractions; two final-value '
     'examples; DC-gain design; three differential equations; cruise control; both '
     'DC-motor outputs; and both satellite pulse experiments. Repeated solution '
     'slides are combined. The general Laplace tables and symbolic definitions '
     'are reference material, rather than additional parameterized systems.')
rows = [['Report case', 'Presentation slides', 'Response']]
for row in [
    ['1–4', '9–17', 'Partial fractions, final values, DC gain'],
    ['5–7', '18–24', 'Initial-state and forced ODE solutions'],
    ['8', '29', 'Car position and speed'],
    ['9', '30–34', 'Motor speed and angle'],
    ['10–11', '35–39', 'Single and opposing satellite pulses'],
]:
    rows.append(row)
table = Table(rows, colWidths=[29*mm, 40*mm, 103*mm])
table.setStyle(TableStyle([
    ('FONTNAME', (0,0), (-1,-1), 'Body'), ('FONTSIZE', (0,0), (-1,-1), 8),
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#dcebf4')),
    ('FONTNAME', (0,0), (-1,0), 'BodyBold'),
    ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ('TOPPADDING', (0,0), (-1,-1), 8),
    ('LINEBELOW', (0,0), (-1,-1), .4, colors.HexColor('#ccd6df')),
]))
story.append(table)
story.append(Spacer(1, 12))
para('Simulation conventions', 'Sub')
para('Time is in seconds. Abstract examples use normalized input/output units. '
     'All physical models start from rest; only cases 5–6 use selected nonzero '
     'initial conditions, y(0)=1 and y′(0)=0.5. The 500 N car step and 1 V motor '
     'step are explicit simulation choices. The satellite pulse amplitudes and '
     'times come directly from the slides.')
para('MATLAB Control System Toolbox <font name="Code">step</font>, '
     '<font name="Code">initial</font> and <font name="Code">lsim</font> '
     'compute continuous-time LTI responses on the shown uniform time grids. '
     'Step/pulse inputs use zero-order hold (ZOH); the smooth exponential input '
     'uses first-order hold (FOH). There is no adaptive ODE or Simulink solver '
     'setting in these simulations. Black points check the analytical solution '
     'or, for the motor, an independently formulated physical state model.')
para('Run the simulations', 'Sub')
code("% In MATLAB, from this report's folder:\nresults = run_dynamic_response_2();\n% results.outputDir contains PNG plots, MAT data and validation.json")
para('The following code excerpts are the executed simulation sections. They share '
     '<font name="Code">s = tf(\'s\');</font> and an output directory. '
     'The plotting helper appears at the end; the accompanying .m file is fully runnable.', 'SmallText')

cases = [
    ('01', '1 · Partial fractions', 'Slides 9–10',
     'Y(s)=(s+4)(s+3)/[s(s+9)(s+2)]. To simulate the inverse transform with a '
     'unit-step input, use G(s)=sY(s); Y(s) itself is the output transform.',
     'The response starts at y(0+)=1, falls below its final value, then tends to '
     '2/3. The fast term exp(−9t) decays first; the slower negative exp(−2t) '
     'term controls the final approach. The instantaneous jump is consistent '
     'with the direct feedthrough of G(s).'),
    ('02', '2 · A valid final-value calculation', 'Slides 12–14, example 1',
     'Y(s)=7(s+5)/[2s(s²+2s+3)]. Equivalent step-driven system: '
     'G(s)=7(s+5)/[2(s²+2s+3)], with zero initial state.',
     'The system poles are −1 ± j√2. The decaying oscillation approaches '
     '35/6 = 5.833333. The final-value theorem applies because every pole of '
     'sY(s) lies strictly in the left half-plane.'),
    ('03', '3 · An invalid final-value calculation', 'Slides 13–14, example 2',
     'Y(s)=4/[s(s²−5s+6)]. Equivalent step-driven system: '
     'G(s)=4/[(s−2)(s−3)], with zero initial state.',
     f'The output grows to {RESULT["unstableAt3"]:.3f} by t=3 s and is unbounded. '
     'The poles +2 and +3 generate growing exponentials. Although '
     'lim sY(s) as s→0 equals 2/3, this is not a time-domain final value: '
     'the theorem’s stability condition fails.'),
    ('04', '4 · Design for a DC gain of 2.5', 'Slides 15–17',
     'G(s)=4(s+A)/(s²+7s+5). Setting G(0)=4A/5=2.5 gives A=3.125. '
     'Apply a unit step with zero initial state.',
     'The output tends monotonically to 2.5. Both poles, approximately −0.8074 '
     'and −6.1926, are stable real numbers. The pole closest to zero dominates '
     'the slower final approach; the zero at −3.125 changes the transient coefficients.'),
    ('05', '5 · Unforced oscillator', 'Slides 18–19',
     'y″+y=0; y(0)=α, y′(0)=β. The slides leave α and β symbolic. '
     'This run selects α=1 and β=0.5; the input is zero.',
     'y(t)=cos(t)+0.5 sin(t) oscillates indefinitely, with amplitude √1.25 '
     '≈1.1180 and period 2π≈6.2832 s. The poles ±j lie on the imaginary axis, '
     'so there is no decay or constant final value. The response comes entirely '
     'from stored initial energy.'),
    ('06', '6 · Forced second-order equation', 'Slides 20–21',
     'y″+5y′+4y=3. Use state x=[y; y′], input u=3, and selected '
     'initial conditions y(0)=1, y′(0)=0.5.',
     'With these initial values, y(t)=3/4+(1/2)exp(−t)−(1/4)exp(−4t). '
     'The response initially rises because y′(0)>0, then decays toward 3/4. '
     'The initial conditions change the transient but not the final value '
     'because both natural modes are stable.'),
    ('07', '7 · First order with a varying input', 'Slides 22–24',
     'y′+6y=u(t), y(0)=0, u(t)=1−0.3 exp(−3t); G(s)=1/(s+6). '
     'The smooth input is sampled every 0.001 s and interpolated linearly.',
     'The input rises from 0.7 to 1 and the output tends to 1/6≈0.166667. '
     'The response includes the plant mode exp(−6t) and the slower input mode '
     'exp(−3t). The partial-fraction line on slide 22 has sign typos: the '
     'residues are +1/6, −1/10 and −1/15. Its final time-domain expression, '
     'used here, has the correct negative signs.'),
    ('08', '8 · Cruise control: position and speed', 'Slide 29',
     'm x″+b x′=u, with m=1000 kg and b=50 N·s/m, as implied by the slide’s '
     'Gx(s)=0.001/[s(s+0.05)]. Add Gv(s)=0.001/(s+0.05) to show speed. '
     'Apply 500 N from rest.',
     f'Speed approaches 10 m/s with time constant 20 s; at 120 s it is '
     f'{RESULT["carSpeedAt120"]:.6f} m/s. Position is '
     f'{RESULT["carPositionAt120"]:.6f} m and continues growing, approaching '
     'a ramp of slope 10 m/s. The position integrator explains why position '
     'does not settle even though speed does.'),
    ('09', '9 · DC motor: speed and angle', 'Slides 30–34',
     'Jm=0.02 kg·m², b=0.005 N·m·s/rad, Kt=0.5 N·m/A, '
     'Ke=0.5 V·s/rad, Ra=2.5 Ω, La=0.1 H. '
     'Gω(s)=250/(s²+25.25s+131.25); Gθ(s)=Gω(s)/s. '
     'Apply 1 V with zero current, speed and angle; no external load torque.',
     f'The speed poles are {RESULT["motorPoles"][0]:.4f} and '
     f'{RESULT["motorPoles"][1]:.4f} s<super>−1</super>. Speed rises without overshoot toward '
     f'{RESULT["motorSteadySpeed"]:.6f} rad/s, reproducing the final motor plot. '
     'Angle grows continuously and eventually becomes a ramp with that slope. '
     'The additional pole at zero belongs to the angle output, not the speed output.'),
    ('10', '10 · Satellite: one thrust pulse', 'Slides 35–37',
     'I θ″=d Fc, with d=1 m, I=5000 kg·m² and zero disturbance torque. '
     'H(s)=0.0002/s². Apply +25 N on [5.0,5.1) s; θ(0)=θ′(0)=0.',
     'During thrust the acceleration is 0.005 rad/s². The 2.5 N·s impulse '
     'leaves a constant angular speed of 0.0005 rad/s (0.028648 deg/s), '
     'so the satellite keeps rotating after the force stops. At 10 s, '
     f'θ={RESULT["satelliteSingleAt10Deg"]:.6f}°. This explains the ramp '
     'at the end of the presentation’s single-pulse plot.'),
    ('11', '11 · Satellite: opposing thrust pulses', 'Slides 38–39',
     'Use the same satellite and +25 N pulse, then −25 N on [6.1,6.2) s. '
     'The grid is 0.01 s and ZOH holds each pulse sample over its full interval.',
     'The second pulse removes the angular speed created by the first, so '
     'the attitude remains constant after 6.2 s. Its final value is '
     f'0.000550 rad = {RESULT["satelliteDoubleFinalDeg"]:.6f}°. '
     'Equal opposing impulses cancel velocity, not the displacement accumulated '
     'between them. The flat ending matches the presentation. ZOH and explicit '
     'time masks avoid the slide code’s one-sample timing shift and edge interpolation.'),
]

for case_id, title, slides, model, analysis in cases:
    story.append(PageBreak())
    para(title, 'Heading')
    para(slides, 'SmallText')
    para(model)
    image_path = RUN / f'{case_id}.png'
    assert image_path.is_file(), image_path
    story.append(Image(str(image_path), width=174*mm, height=102.82*mm))
    para('MATLAB code', 'Sub')
    snippet = re.search(rf'% CASE {case_id}\n(.*?)% END CASE', SOURCE, re.S)[1]
    code(snippet.rstrip())
    para('Brief analysis', 'Sub')
    para(analysis)

story.append(PageBreak())
para('Numerical validation and reproducibility', 'Heading')
para(f'Executed with MATLAB {escape(RESULT["matlabVersion"])} and Control System '
     f'Toolbox. All {len(RESULT["checks"])} numerical assertions passed. '
     'The graphs in this PDF are MATLAB exports, not reconstructed illustrations.')
rows = [['Check', 'Maximum absolute error', 'Tolerance']]
for check in RESULT['checks']:
    rows.append([check['name'], f"{check['error']:.3g}", f"{check['tolerance']:.3g}"])
table = Table(rows, colWidths=[95*mm, 47*mm, 30*mm])
table.setStyle(TableStyle([
    ('FONTNAME', (0,0), (-1,-1), 'Body'), ('FONTSIZE', (0,0), (-1,-1), 7.3),
    ('FONTNAME', (0,0), (-1,0), 'BodyBold'),
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#dcebf4')),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ('LINEBELOW', (0,0), (-1,-1), .3, colors.HexColor('#ccd6df')),
]))
story.append(table)
story.append(Spacer(1, 12))
para('What was checked', 'Sub')
para('Closed-form time responses check the partial fractions, final-value cases, '
     'gain design, three ODEs, cruise control and satellite dynamics. The motor’s '
     'transfer-function output is compared with current/speed/angle state equations. '
     'Additional checks verify DC gains, thrust impulses, final attitude and '
     'zero residual angular speed. The small FOH discrepancy is from approximating '
     'the exponential input by straight segments.')
para('Files and rerun instructions', 'Sub')
para('<font name="Code">run_dynamic_response_2.m</font> contains all simulation '
     'and validation code. It creates a fresh folder under '
     '<font name="Code">artifacts/dynamic_response_2/</font> by default. '
     'The returned folder contains eleven PNG plots, '
     '<font name="Code">simulation_data.mat</font> and '
     '<font name="Code">validation.json</font>. The MAT file stores radians for '
     'satellite angles; the plots convert to degrees.')
code('python build_report.py /path/returned/in/results.outputDir')
para('The PDF assembly step requires Python with reportlab. Numerical checks '
     'validate these ideal linear models; no hardware experiment is claimed. '
     'The shared MATLAB session was unavailable, so execution used a separate '
     'batch process. Existing user models and workspaces were preserved.', 'SmallText')
para('Runtime note: MATLAB reported that graphics acceleration hardware was '
     'unavailable. All figure exports completed and the batch process exited '
     'normally (status 0). Code Analyzer returned no issues.', 'SmallText')

story.append(PageBreak())
para('Shared MATLAB plotting helper', 'Heading')
para('Every case uses this helper to place the input above its output(s), label '
     'physical units, overlay reference samples and export the figure. Only '
     'the figure created by this function is closed. The enclosing function '
     'sets <font name="Code">s=tf(\'s\')</font> and creates '
     '<font name="Code">outputDir</font> before running the excerpts.')
code(SOURCE[SOURCE.index('function responsePlot'):].rstrip())
para('Case 11 continues case 10 and reuses its time grid, satellite model and '
     'pulse sample indices. Running the complete .m function executes the cases '
     'in order and performs the checks automatically.', 'SmallText')

target = HERE / 'Dynamic_Response_2_Simulations.pdf'
doc = SimpleDocTemplate(str(target), pagesize=(210*mm, 297*mm),
                        rightMargin=18*mm, leftMargin=18*mm,
                        topMargin=17*mm, bottomMargin=19*mm,
                        title='Dynamic Response 2 — MATLAB simulations',
                        author='Dynamic Systems and Control coursework')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(target)
