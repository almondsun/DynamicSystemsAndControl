"""Hardware evidence additions; no numerical simulation result is overwritten."""
import json
from pathlib import Path
from report_content import Block, P, S, T

def image(label, caption, asset):
 return Block('figure', caption, label, asset=asset)

def revise(spec):
 n,title,subtitle,abstract,blocks=spec
 if n==1:
  extra=[S('Relación con la placa diseñada'),P(r'El circuito completo evaluado aquí conserva el driver discreto BJT y sus modelos genéricos. La placa posterior usa IR2110, inversión HCT14, dos inductores de $330\,\mu\mathrm{H}$ en serie y shunt de $0.05\,\Omega$. El divisor pasa de $30/10\,\mathrm{k}\Omega$ a $3/1\,\mathrm{k}\Omega$. Se conserva $d=1-d^{\prime}$, pero cambian pérdidas y retardos. Por ello estas curvas no validan por sí solas la placa IR2110; su estimación separada se presenta en la entrega 3.')]
 elif n==2:
  for b in blocks:
   b.text=b.text.replace(r'Se propone una carga de $25\,\mathrm{W}$',r'Se seleccionan dos resistencias de $12\,\Omega$, $10\,\mathrm{W}$ en paralelo: carga nominal de $6\,\Omega$, $20\,\mathrm{W}$')
   if b.label=='measured':
    b.rows[5][1]='0.20 (sup. PCB)'; b.rows[6][1]='0.15 (sup. PCB)'
  extra=[S('Diseño preparado para construcción'),P(r'La placa de $99\times99\,\mathrm{mm}$, dos capas y 57 componentes dispone de archivos KiCad, lista de materiales y salidas de fabricación para revisión. ERC, DRC y correspondencia esquema--placa no registran infracciones. Esto verifica reglas CAD, no funcionamiento eléctrico. No se han comprado componentes ni construido el prototipo.'),
   image('pcb-power','Conectividad resumida de potencia, driver y sensor de la placa IR2110. El esquema completo con todos los pines está en el anexo de hardware.','power-summary.pdf'),
   image('pcb-3d','Vista CAD isométrica; no es una fotografía. Inductores: envolvente provisional. Capacitores: geometría genérica del encapsulado, referencia comercial pendiente.','pcb-3d.png'),
   image('pcb-layout','Vista de componentes con referencias y conectores. Las conexiones externas se detallan en el anexo.','layout.pdf'),
   P(r'La fabricación permanece retenida hasta confirmar dimensiones, saturación y DCR de L1/L2, referencia y corriente de rizado de C4/C5, y verificar bootstrap, apagado y sensores en prototipo soldado. El STM32, programador y banco de carga se conectan externamente. El objetivo de presupuesto es COP 350\,000; el estimado de COP 281\,501.95 incluye asignaciones sin cotización final, dejando COP 68\,498.05 de reserva.')]
 elif n==3:
  results=json.loads((Path(__file__).resolve().parents[1]/'pcb/release/simulation/results.json').read_text())
  extra=[S('Vínculo con el procedimiento de clase'),P(r'El capítulo 10 de clase, sección 7, lámina 90, describe el PI y recomienda normalmente un cero muy inferior al cruce para reducir su pérdida de fase \cite{frequency}. Aquí se adopta deliberadamente $\omega_z=3000\,\mathrm{rad/s}>\omega_c=1000\,\mathrm{rad/s}$: el PI aporta aproximadamente $-71.565^\circ$ y la planta $-6.36^\circ$, dejando $102.07^\circ$ de margen continuo. La elección aumenta la acción integral y se acepta por el margen calculado y los ensayos numéricos; no reproduce la recomendación usual de ubicación del cero. El procedimiento conserva selección de cruce, normalización de ganancia, verificación de margen y comprobación transitoria.'),
   S('Estimación adicional de la realización STM32'),P(r'Se seleccionó STM32F103C8T6 externo, con PI C, ADC de 12 bits, 20 muestras por periodo y PWM de $10\,\mathrm{kHz}$. La simulación adicional ejecuta el algoritmo C e incluye media, cuantización y un periodo de retardo; no sustituye las curvas anteriores.'),
   T('model-scope','Alcance de cada realización',[['Realización','Hipótesis principales'],['Promediado / continuo','Planta ideal; PI continuo'],['PWM ideal / digital','Media y retardo; conmutación ideal'],['ngspice / BJT','PI continuo; DCR 0.1 y ESR 0.05 ohm'],['Estimación PCB / C','DCR 0.20, ESR 0.15, shunt 0.05 ohm; ADC y retardo']]),
   P(r'La estimación PCB usa $R_{\mathrm{DS}}=0.022\,\Omega$, $V_F=0.45\,\mathrm{V}$ y retardos de encendido/apagado de 120/94 ns como supuestos. Euler usa paso de $0.5\,\mu\mathrm{s}$ con fracción de flanco PWM; parte de energía nula y aplica el evento tras 800 ms. Se muestran 40 ms con evento en 10 ms. No modela saturación, térmica, EMI ni la recarga real del bootstrap.'),
   T('pcb-results','Resultados adicionales estimados; no medidos',[['Caso',r'$t_s$ (ms)',r'$|e_\infty|$ (mV)'],*[[name,f'{results[k]["settling_s_after_event"]*1000:.2f}',f'{results[k]["steady_error_V"]*1000:.3f}'] for k,name in [('ref_up','6 a 7 V'),('ref_down','6 a 5 V'),('load_up','6 a 7.2 ohm'),('load_down','6 a 4.8 ohm')]]]),
   P(fr'Las bandas son $\pm20\,\mathrm{{mV}}$ en referencia y $\pm0.12\,\mathrm{{V}}$ en carga. Seis escenarios no activan la protección simulada; corriente máxima $1.549272\,\mathrm{{A}}$. Reducir el paso a $0.25\,\mu\mathrm{{s}}$ cambia la media como máximo ${results["convergence_max_cycle_mean_difference_V"]*1000:.3f}\,\mathrm{{mV}}$ en referencia ascendente. Los umbrales nominales de protección no son tolerancias garantizadas.')]
 else:
  for b in blocks:
   b.text=b.text.replace('Existe un núcleo C validado en computador; tarjeta, integración ADC/PWM, calibración y capturas están pendientes.','La placa está diseñada y el firmware STM32 compila. El código integra adquisición, DMA y PWM, y el núcleo C cuenta con pruebas en computador. Faltan el montaje, la programación del MCU, la calibración y las capturas físicas.')
   b.text=b.text.replace(r'$R_t=30\,\mathrm{k}\Omega$ y $R_b=10\,\mathrm{k}\Omega$',r'$R_t=3\,\mathrm{k}\Omega$ y $R_b=1\,\mathrm{k}\Omega$')
   b.text=b.text.replace('Deben confirmarse $N$, $V_{\\mathrm{ADC}}$, frecuencia de adquisición y filtro.','La configuración es de 12 bits, referencia nominal de 3.3 V y muestreo de 200 kHz; deben verificarse en la placa real.')
   b.text=b.text.replace('El arranque gradual debe integrarse en la tarjeta; no está implícito en el PI.','El firmware incorpora rampa de duty y transferencia al PI con ajuste de integral; falta verificarla en hardware.')
   b.text=b.text.replace('Faltan montaje identificado, firmware integrado, coeficientes cargados, calibración, temporización, apagado y doce capturas mínimas.','Faltan montaje identificado, firmware cargado en MCU, calibración, medición de temporización y apagado, y doce capturas mínimas.')
   if b.label=='hardware':
    b.text='Configurado en firmware; verificación física pendiente'
    b.rows=[['Dato','Configuración; falta medir'],['MCU y reloj','STM32F103C8T6; 72 MHz'],['ADC','12 bits; 3.3 V nominal; 200 kHz'],['Media; filtro','20 muestras; RC de 0.75 us'],['PWM','10 kHz; 7200 cuentas'],['Calibración y jitter','Pendiente'],['Instrumentos y fotografía','Pendiente']]
  extra=[S('Integración implementada y protección'),
   image('wiring','Interconexión prevista. MCU, programador, enlace serie y carga son externos a la PCB.','wiring.pdf'),
   P(r'TIM1 genera PWM por PA8 y sincroniza TIM3; este dispara ADC1/PA0 cada $5\,\mu\mathrm{s}$. DMA circular conserva dos bloques de 20 muestras. La interrupción TIM1 verifica bloque completo, promedia y precarga CCR para el siguiente periodo. La última conversión termina nominalmente a $97.667\,\mu\mathrm{s}$. DWT vigila ejecución y el watchdog exige adquisición fresca. Estos tiempos proceden de la configuración y deben medirse.'),
   T('implementation','Evidencia de implementación',[['Elemento','Estado'],['Compilación ARM','ELF, BIN y HEX generados'],['Núcleo y runtime C','Pruebas nativas y sanitizadores superadas'],['Captura serie','Cuatro pruebas automatizadas superadas'],['Programación / tiempo real','Pendiente en MCU'],['ADC / protección / térmica','Pendiente en laboratorio']]),
   P(r'INA180A1 amplifica el shunt; LM393 activa un enclavamiento HCT00 por sobrecorriente o sobretensión. RUN bajo fuerza SD alto y deshabilita IR2110. El disparo tiene prioridad sobre RESET. Los umbrales nominales son 2 A y 8.2 V; la evaluación estática de tolerancias da 1.825--2.184 A y 7.561--8.868 V. Deben comprobarse retardo y disparo real. Se requiere fusible externo de 2 A y fuente limitada.'),
   P(r'El enlace UART de 115200 baudios exporta las capturas después de detener RUN. Las 512 medias se guardan con duty aplicado y referencia; no equivalen al rizado instantáneo, que exige osciloscopio. Los escalones de carga manuales requieren captura con pretrigger. Conservar CSV crudos, calibración y versión de firmware junto a cada ensayo.')]
 # Place evidence before the final conclusions / experimental acceptance sections.
 target={1:'Conclusiones',2:'Identificación de parámetros',3:'Conclusiones',4:'Ensayos de aceptación'}[n]
 index=next(i for i,b in enumerate(blocks) if b.kind=='section' and b.text==target)
 blocks[index:index]=extra
 return n,title,subtitle,abstract,blocks
