"""Genera el informe español con capturas originales y análisis de polos/ceros.

Uso: python build_report_es.py /ruta/al/resultado/de/MATLAB
Requiere reportlab y pymupdf. Las gráficas proceden de MATLAB.
"""
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import pymupdf
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Preformatted,
    Table, TableStyle,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RUN = Path(sys.argv[1]).resolve()
RESULT = json.loads((RUN / 'validation.json').read_text())
assert RESULT['passed'] and len(RESULT['poleZero']) == 12
SOURCE = (HERE / 'run_respuesta_dinamica_2.m').read_text()
FONT = Path('/usr/share/fonts/liberation')
for name, file in [('Body', 'LiberationSans-Regular.ttf'),
                   ('Bold', 'LiberationSans-Bold.ttf'),
                   ('Code', 'LiberationMono-Regular.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONT / file)))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='Bold')
styles = {
    'body': ParagraphStyle('body', fontName='Body', fontSize=10, leading=14,
                           spaceAfter=9, textColor=colors.HexColor('#243447')),
    'small': ParagraphStyle('small', fontName='Body', fontSize=8, leading=11,
                            spaceAfter=7, textColor=colors.HexColor('#526575')),
    'title': ParagraphStyle('title', fontName='Bold', fontSize=18, leading=23,
                            spaceAfter=11, textColor=colors.HexColor('#114b70')),
    'cover': ParagraphStyle('cover', fontName='Bold', fontSize=29, leading=35,
                            spaceAfter=18, textColor=colors.HexColor('#114b70')),
    'sub': ParagraphStyle('sub', fontName='Bold', fontSize=11, leading=15,
                          spaceAfter=6, spaceBefore=6),
    'code': ParagraphStyle('code', fontName='Code', fontSize=7.8, leading=10.5,
                           spaceAfter=10),
}
story = []


def p(text, style='body'):
    story.append(Paragraph(text, styles[style]))


def code(text):
    story.append(Preformatted(text.rstrip(), styles['code']))


def table(rows, widths, fontsize=8, padding=5):
    t = Table(rows, colWidths=[w*mm for w in widths], hAlign='LEFT')
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Body'),
        ('FONTNAME', (0, 0), (-1, 0), 'Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), fontsize),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dcebf4')),
        ('TOPPADDING', (0, 0), (-1, -1), padding),
        ('BOTTOMPADDING', (0, 0), (-1, -1), padding),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, -1), .3, colors.HexColor('#ccd6df')),
    ]))
    story.append(t)
    story.append(Spacer(1, 9))


def footer(canvas, doc):
    canvas.setFont('Body', 7)
    canvas.setFillColor(colors.HexColor('#607080'))
    canvas.drawString(18*mm, 12*mm, 'Respuesta dinámica 2 · Simulaciones en MATLAB')
    canvas.drawRightString(192*mm, 12*mm, str(doc.page))


p('Respuesta dinámica 2', 'cover')
p('Simulaciones en MATLAB, contexto y análisis de polos y ceros', 'title')
p('Sistemas Dinámicos y Control · Universidad Nacional de Colombia')
p('Fuente: Juan David Bastidas Rodríguez, <i>4 Dynamic Response 2.pdf</i>, '
  '39 diapositivas. Bibliografía de la presentación: Franklin, Powell y '
  'Emami-Naeini, <i>Feedback Control of Dynamic Systems</i>, 8.ª ed., Pearson, 2019.')
p('Alcance y organización', 'sub')
p('Se incluyen los once casos que cubren todos los ejemplos resueltos de la '
  'presentación. Cada caso contiene una captura de la diapositiva original, '
  'el modelo, sus polos y ceros, gráficas de entrada y salida, código MATLAB '
  'y un análisis breve. Las capturas conservan el idioma original de la fuente. '
  'Las diapositivas repetidas se agrupan; las tablas generales de Laplace '
  'son material de consulta, no sistemas adicionales.')
table([['Casos', 'Diapositivas', 'Contenido'],
       ['1–4', '9–17', 'Fracciones parciales, valor final y ganancia estática'],
       ['5–7', '18–24', 'Ecuaciones diferenciales libres y forzadas'],
       ['8', '29', 'Posición y velocidad del automóvil'],
       ['9', '30–34', 'Velocidad y ángulo del motor de corriente continua'],
       ['10–11', '35–39', 'Un pulso y dos pulsos opuestos en el satélite']], [20, 30, 124])
p('Condiciones y método numérico', 'sub')
p('El tiempo se expresa en segundos. Los ejemplos abstractos usan unidades '
  'normalizadas. Los modelos físicos parten del reposo. En los casos 5 y 6 '
  'se eligen y(0)=1 y y′(0)=0.5 porque la fuente deja esos valores simbólicos. '
  'El escalón de 500 N del automóvil y el de 1 V del motor son elecciones '
  'de simulación; los pulsos del satélite provienen de la presentación.')
p('Control System Toolbox calcula las respuestas LTI continuas con '
  '<font name="Code">step</font>, <font name="Code">initial</font> y '
  '<font name="Code">lsim</font>. Se usa retención de orden cero (ZOH) para '
  'entradas constantes y pulsos, y de primer orden (FOH) para la entrada '
  'exponencial. Cada bloque de código indica su malla temporal. No se configura '
  'un integrador adaptativo ni un solver de Simulink.')
p('Cómo interpretar los polos y ceros', 'sub')
p('Los polos de G(s) determinan los modos naturales; los ceros modifican la '
  'respuesta transitoria. Estabilidad BIBO significa que entradas acotadas '
  'producen salidas acotadas. Un sistema racional propio es BIBO estable cuando '
  'todos sus polos están estrictamente en el semiplano izquierdo, sin modos '
  'internos inestables ocultos. Un polo en el origen o en el eje imaginario '
  'impide afirmar estabilidad BIBO. Se distinguen G(s), la entrada U(s) y '
  'la transformada de salida Y(s): no tienen necesariamente los mismos polos.')
code('% Desde la carpeta del informe, en MATLAB:\nresults = run_respuesta_dinamica_2();')
p('Los fragmentos comparten s=tf(\'s\') y outputDir. El archivo .m adjunto '
  'es ejecutable y crea una carpeta nueva con imágenes, datos y validaciones.', 'small')

# id, título, captura, modelo, índices de la tabla de MATLAB, análisis P/Z,
# análisis temporal. Los índices corresponden al orden de results.poleZero.
cases = [
('01', '1 · Fracciones parciales', 9,
 'Y(s)=(s+4)(s+3)/[s(s+9)(s+2)]. Se emplea G(s)=sY(s) con un escalón '
 'unitario para reproducir la transformada de salida de la diapositiva.', [0],
 'G(s) tiene polos −9 y −2 y ceros −4 y −3, todos en el semiplano izquierdo. '
 'Es BIBO estable y no hay cancelaciones. El modo lento tiene constante de '
 'tiempo 1/2 s y el rápido 1/9 s. El grado relativo es cero: existe paso '
 'directo y y(0+)=1. Y(s) añade un polo en cero por el escalón; ese polo no '
 'pertenece a G(s). Los ceros determinan los coeficientes de los modos y '
 'contribuyen a la caída inicial por debajo del valor final.',
 'La salida comienza en 1, cae por debajo de 2/3 y luego converge a ese valor. '
 'El término exp(−9t) desaparece rápidamente; el término negativo exp(−2t) '
 'domina el acercamiento final. El salto inicial es consistente con el paso directo.'),
('02', '2 · Aplicación válida del valor final', 13,
 'Y(s)=7(s+5)/[2s(s²+2s+3)]. Se simula G(s)=7(s+5)/[2(s²+2s+3)] '
 'con escalón unitario y estado inicial nulo.', [1],
 'Los polos son −1±j√2 y el cero es −5. El sistema es BIBO estable, '
 'subamortiguado, con frecuencia natural √3 rad/s y amortiguamiento '
 'ζ=1/√3≈0.5774. La envolvente decae como exp(−t); la frecuencia amortiguada '
 'es √2 rad/s. El cero estable modifica la forma transitoria sin alterar los '
 'polos. El único polo adicional de Y(s) está en cero y proviene de la entrada. '
 'Todos los polos de sY(s) son estables: el teorema del valor final sí aplica.',
 'La oscilación amortiguada converge a 35/6=5.833333. Los puntos de referencia '
 'coinciden con la respuesta analítica, incluido el sobreimpulso.'),
('03', '3 · Uso incorrecto del valor final', 13,
 'Y(s)=4/[s(s²−5s+6)]. Se usa G(s)=4/[(s−2)(s−3)] con '
 'escalón unitario y estado inicial nulo.', [2],
 'Los polos +2 y +3 están en el semiplano derecho: el sistema es inestable '
 'y no tiene ceros finitos que modifiquen o cancelen esos modos. Las componentes '
 'exp(2t) y exp(3t) crecen; a largo plazo domina el polo +3. Aunque '
 'lim sY(s), cuando s→0, vale 2/3, no representa el valor final temporal '
 'porque los polos de sY(s) no cumplen la condición de estabilidad.',
 f'La salida alcanza {RESULT["unstableAt3"]:.3f} en t=3 s y crece sin límite. '
 'Este ejemplo muestra por qué se deben examinar los polos antes de aplicar el teorema.'),
('04', '4 · Ganancia estática de 2.5', 16,
 'G(s)=4(s+A)/(s²+7s+5). La condición G(0)=4A/5=2.5 '
 'da A=3.125. Se aplica un escalón unitario desde el reposo.', [3],
 'Los polos son (−7±√29)/2, aproximadamente −0.8074 y −6.1926. '
 'El cero está en −3.125. Los polos reales negativos garantizan estabilidad '
 'BIBO; no hay cancelaciones. El polo −0.8074 domina la aproximación final, '
 'con constante de tiempo aproximada de 1.2385 s. Ajustar A cambia el cero '
 'y la ganancia estática, pero deja intactos los polos del denominador.',
 'La respuesta aumenta monótonamente hasta 2.5. La comprobación con '
 'dcgain confirma exactamente el objetivo de diseño.'),
('05', '5 · Oscilador libre', 18,
 'y″+y=0; y(0)=α y y′(0)=β. Se eligen α=1 y β=0.5, sin entrada externa. '
 'Para estudiar el sistema se considera la transferencia de referencia '
 'G(s)=1/(s²+1), asociada a y″+y=u.', [4],
 'Los polos son ±j y no hay ceros finitos. Son polos simples sobre el eje '
 'imaginario: la respuesta libre es acotada, pero no converge al equilibrio. '
 'El sistema no es asintóticamente estable ni BIBO estable; una entrada '
 'resonante puede producir crecimiento. Con las condiciones iniciales elegidas, '
 'Y(s)=(s+0.5)/(s²+1) tiene un cero en −0.5; ese cero corresponde a la '
 'respuesta inicial, no a la transferencia de referencia G(s).',
 'y(t)=cos(t)+0.5 sin(t) oscila indefinidamente con amplitud √1.25≈1.1180 '
 'y período 2π≈6.2832 s. La energía inicial explica la respuesta pese a que u(t)=0.'),
('06', '6 · Ecuación forzada de segundo orden', 20,
 'y″+5y′+4y=3. Se usa x=[y; y′], u=3, y(0)=1 y y′(0)=0.5. '
 'La transferencia entre u e y, con condiciones iniciales nulas, es '
 'G(s)=1/[(s+1)(s+4)].', [5],
 'Los polos −1 y −4 son estables y no existen ceros finitos. Sus constantes '
 'de tiempo son 1 s y 0.25 s. El estado inicial cambia los coeficientes de '
 'los modos, pero no su ubicación. Para este experimento, '
 'Y(s)=(s²+5.5s+3)/[s(s+1)(s+4)]: el polo en cero procede de la entrada '
 'constante y los ceros de Y(s) dependen también del estado inicial; '
 'no son ceros de G(s).',
 'y(t)=3/4+(1/2)exp(−t)−(1/4)exp(−4t). La salida aumenta al principio '
 'porque y′(0)>0, pero luego desciende hasta 3/4. Los modos naturales '
 'se extinguen y la entrada constante determina el valor final.'),
('07', '7 · Primer orden con entrada variable', 22,
 'y′+6y=u(t), y(0)=0, u(t)=1−0.3 exp(−3t); G(s)=1/(s+6). '
 'La entrada suave se interpola linealmente con paso de 0.001 s.', [6],
 'La planta tiene un polo en −6 y ningún cero finito: es BIBO estable y '
 'su constante de tiempo es 1/6 s. La entrada tiene polos en 0 y −3. '
 'Por eso Y(s)=(0.7s+3)/[s(s+3)(s+6)] tiene tres polos y un cero '
 'en −30/7≈−4.2857. El término exp(−3t), más lento que el modo propio, '
 'proviene de la entrada. La línea de fracciones parciales de la diapositiva '
 '22 contiene signos erróneos: los residuos correctos son +1/6, −1/10 y −1/15; '
 'la expresión temporal final de esa diapositiva sí es correcta.',
 'La entrada aumenta de 0.7 a 1 y la salida tiende a 1/6≈0.166667. '
 'La solución exacta es y(t)=1/6−exp(−3t)/10−exp(−6t)/15. '
 'La pequeña diferencia numérica procede de la interpolación FOH.'),
('08', '8 · Automóvil: posición y velocidad', 29,
 'm x″+b x′=u, con m=1000 kg y b=50 N·s/m, según '
 'Gx(s)=0.001/[s(s+0.05)] de la fuente. Se añade '
 'Gv(s)=0.001/(s+0.05) y se aplica un escalón de 500 N desde el reposo.', [7, 8],
 'La posición tiene polos en 0 y −0.05, sin ceros finitos. El polo en cero '
 'es el integrador cinemático: una fuerza constante produce posición creciente, '
 'de modo que Gx no es BIBO estable. La velocidad tiene únicamente el polo '
 '−0.05: es BIBO estable y su constante de tiempo es 20 s. El cambio de '
 'salida explica la diferencia; la velocidad elimina la integración de posición. '
 'No se está ocultando un modo inestable mediante una cancelación aproximada.',
 f'La velocidad tiende a 10 m/s y alcanza {RESULT["carSpeedAt120"]:.6f} m/s '
 f'a los 120 s. La posición es {RESULT["carPositionAt120"]:.6f} m y sigue '
 'creciendo; finalmente se aproxima a una rampa de pendiente 10 m/s.'),
('09', '9 · Motor CC: velocidad y ángulo', 30,
 'Jm=0.02 kg·m²; b=0.005 N·m·s/rad; Kt=0.5 N·m/A; '
 'Ke=0.5 V·s/rad; Ra=2.5 Ω; La=0.1 H. '
 'Gω(s)=250/(s²+25.25s+131.25); Gθ(s)=Gω(s)/s. '
 'Se aplica 1 V, sin par de carga externo, desde corriente, velocidad y ángulo nulos.', [9, 10],
 'La transferencia de velocidad tiene dos polos reales negativos, '
 f'{RESULT["motorPoles"][0]:.4f} y {RESULT["motorPoles"][1]:.4f}, '
 'y no tiene ceros finitos. Es BIBO estable y sobreamortiguada. El polo '
 '−7.3202 domina el transitorio, con constante de tiempo aproximada de 0.1366 s. '
 'El ángulo añade un polo en cero, por lo que su transferencia no es BIBO '
 'estable: una tensión constante mantiene una velocidad no nula y acumula giro.',
 f'La velocidad aumenta sin sobreimpulso hacia {RESULT["motorSteadySpeed"]:.6f} '
 'rad/s. El ángulo crece y se aproxima a una rampa de esa pendiente. '
 'Un modelo independiente de corriente, velocidad y ángulo verifica ambas respuestas.'),
('10', '10 · Satélite: un pulso de empuje', 37,
 'I θ″=d Fc; d=1 m; I=5000 kg·m²; par perturbador nulo. '
 'H(s)=0.0002/s². Se aplica +25 N durante [5.0,5.1) s, '
 'con θ(0)=θ′(0)=0.', [11],
 'H(s) tiene un polo doble en el origen y ningún cero finito. Es un doble '
 'integrador y no es BIBO estable. Tampoco basta clasificarlo como un oscilador '
 'marginal: una velocidad angular inicial no nula genera una orientación que '
 'crece linealmente aun sin entrada. El pulso deja una velocidad residual '
 'porque el modelo no incluye amortiguamiento ni realimentación.',
 'La aceleración durante el pulso es 0.005 rad/s². Su impulso de 2.5 N·s '
 'deja una velocidad angular de 0.0005 rad/s (0.028648 grados/s). '
 f'A los 10 s, θ={RESULT["satelliteSingleAt10Deg"]:.6f}°. '
 'El satélite sigue girando después de cesar el empuje.'),
('11', '11 · Satélite: dos pulsos opuestos', 39,
 'Se conserva H(s)=0.0002/s² y el pulso de +25 N del caso anterior. '
 'Se añade −25 N durante [6.1,6.2) s. El paso es 0.01 s y se emplea ZOH.', [11],
 'Los polos siguen siendo 0 y 0: cambiar la entrada no modifica H(s). '
 'La orientación constante al final de este experimento no convierte a la '
 'planta en estable. Los dos impulsos iguales y opuestos anulan la velocidad '
 'residual para este mando concreto, pero un error de impulso dejaría deriva. '
 'El resultado es una maniobra en lazo abierto; no se han desplazado polos '
 'mediante realimentación ni se han añadido ceros a la planta.',
 'El segundo pulso elimina la velocidad angular del primero y la orientación '
 'permanece constante después de 6.2 s. El valor final es 0.000550 rad '
 f'= {RESULT["satelliteDoubleFinalDeg"]:.6f}°. Se cancela la velocidad, '
 'pero no el desplazamiento acumulado. Las máscaras temporales y ZOH evitan '
 'el desplazamiento de una muestra y la interpolación de bordes del código de la fuente.'),
]

slides = pymupdf.open(ROOT / 'classroom' / '4 Dynamic Response 2.pdf')
screens = RUN / 'capturas_originales'
screens.mkdir(exist_ok=True)
for case_id, title, slide, model, indices, pz_analysis, analysis in cases:
    story.append(PageBreak())
    p(title, 'title')
    p(f'Contexto de la presentación · Diapositiva {slide}', 'small')
    shot = screens / f'diapositiva_{slide:02d}.png'
    page = slides[slide-1]
    page.get_pixmap(matrix=pymupdf.Matrix(1.7, 1.7)).save(shot)
    story.append(Image(str(shot), width=174*mm,
                       height=174*mm*page.rect.height/page.rect.width))
    p(f'Captura íntegra de la diapositiva {slide} de la presentación original '
      'de Juan David Bastidas Rodríguez.', 'small')
    p('Modelo y condiciones', 'sub')
    p(model)
    p('Polos y ceros de la función de transferencia', 'sub')
    rows = [['Salida / sistema', 'Polos (s⁻¹)', 'Ceros finitos']]
    # Use simple 1/s notation: the installed font lacks superscript minus.
    rows[0][1] = 'Polos (1/s)'
    for idx in indices:
        item = RESULT['poleZero'][idx]
        poles = item['poles'].replace('i', 'j')
        zeros = 'Ninguno' if item['zeros'] in ('[]', 'zeros(1,0)') else item['zeros']
        name = item['name'].replace('estatica', 'estática').replace('Automovil', 'Automóvil')
        name = name.replace('posicion', 'posición').replace('angulo', 'ángulo').replace('Satelite', 'Satélite')
        rows.append([name, poles, zeros])
    table(rows, [47, 93, 34], 7.4)
    p(pz_analysis)
    rel = ', '.join(str(RESULT['poleZero'][i]['relativeDegree']) for i in indices)
    p(f'Grado relativo (n−m): {rel}. Este número también corresponde a los '
      'ceros en el infinito en la convención de la presentación. '
      'Los valores de la tabla se calcularon con pole y zero de MATLAB.', 'small')

    story.append(PageBreak())
    p(title + ' · Simulación', 'title')
    story.append(Image(str(RUN / f'{case_id}.png'), width=174*mm, height=102.82*mm))
    p('Código MATLAB', 'sub')
    snippet = re.search(rf'% CASE {case_id}\n(.*?)% END CASE', SOURCE, re.S)[1]
    code(snippet)
    p('Análisis breve de la respuesta', 'sub')
    p(analysis)

story.append(PageBreak())
p('Validación numérica y reproducción', 'title')
p(f'Ejecución: MATLAB {escape(RESULT["matlabVersion"])} y Control System Toolbox. '
  f'Se aprobaron las {len(RESULT["checks"])} comprobaciones numéricas. '
  'Las once gráficas se exportaron directamente desde MATLAB. Los polos y ceros '
  'se calcularon para doce funciones de transferencia, considerando por separado '
  'las salidas de posición y velocidad del automóvil y de ángulo y velocidad del motor.')
table([['Comprobación', 'Error absoluto máximo', 'Tolerancia']] +
      [[c['name'], f"{c['error']:.3g}", f"{c['tolerance']:.3g}"]
       for c in RESULT['checks']], [94, 48, 32], 7.4, padding=3)
p('Qué se verificó', 'sub')
p('Se contrastaron las respuestas con soluciones analíticas o, en el motor, '
  'con un modelo físico independiente en espacio de estados. También se '
  'comprobaron ganancias estáticas, impulsos, orientación final y velocidad '
  'angular residual. La discrepancia FOH procede de aproximar la entrada '
  'exponencial mediante segmentos rectos.', 'small')
p('Archivos y ejecución', 'sub')
p('<font name="Code">run_respuesta_dinamica_2.m</font> guarda las gráficas, '
  '<font name="Code">simulation_data.mat</font> y '
  '<font name="Code">validation.json</font> en una carpeta nueva dentro de '
  '<font name="Code">artifacts/dynamic_response_2/</font>. '
  'Los ángulos del satélite se almacenan en radianes y se grafican en grados.', 'small')
code('python build_report_es.py /ruta/devuelta/en/results.outputDir')
p('El generador requiere reportlab, pymupdf y las fuentes Liberation. '
  'Las capturas se extraen del PDF original. Se utilizó MATLAB por lotes '
  'porque la sesión compartida no estaba disponible. El aviso sobre falta '
  'de aceleración gráfica no impidió las exportaciones; el proceso terminó '
  'con estado 0. Code Analyzer no encontró incidencias. Estas comprobaciones '
  'validan modelos numéricos ideales, no ensayos físicos.', 'small')

story.append(PageBreak())
p('Función auxiliar para las gráficas', 'title')
p('Esta función coloca la entrada encima de las salidas, añade unidades y '
  'muestras de referencia, exporta la imagen y cierra únicamente la figura '
  'que acaba de crear. El archivo completo ejecuta los casos en orden; '
  'el caso 11 reutiliza el tiempo, el modelo y los índices del caso 10.', 'small')
code(SOURCE[SOURCE.index('function responsePlot'):])
p('Consulta de polos y ceros', 'sub')
code("% Para cualquier transferencia G definida en los casos:\np = pole(G);\nz = zero(G);\n% Ejemplo: orientación del satélite\nH = 0.0002/tf('s')^2;\npole(H)   % Dos polos en cero\nzero(H)   % Sin ceros finitos")

target = HERE / 'Respuesta_Dinamica_2_Simulaciones_ES.pdf'
doc = SimpleDocTemplate(str(target), pagesize=(210*mm, 297*mm),
    leftMargin=18*mm, rightMargin=18*mm, topMargin=17*mm, bottomMargin=19*mm,
    title='Respuesta dinámica 2 — Simulaciones y análisis de polos y ceros',
    author='Sistemas Dinámicos y Control')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(target)
