"""Explicit semantic blocks; all mathematics is authored in LaTeX."""
from dataclasses import dataclass

@dataclass
class Block:
    kind: str
    text: str
    label: str = ''
    rows: list | None = None
    asset: str = ''

def P(s): return Block('paragraph', s)
def S(s): return Block('section', s)
def E(s, label): return Block('equation', s, label)
def F(label, s): return Block('figure', s, label)
def T(label, caption, rows): return Block('table', caption, label, rows)

AUTHORS = [('Martín Ramírez Espinosa','maramirezes@unal.edu.co'),
 ('Jerónimo Vargas Orozco','jevargaso@unal.edu.co'),
 ('Andrew Esteban Henao Becerra','anhenaobe@unal.edu.co'),
 ('Mateo Alexander Cardenas Cuesta','macardenascu@unal.edu.co')]
REFS = {
 'guide': r'J. D. Bastidas Rodríguez, ``Proyecto de Curso: Convertidor Buck con control de tensión de salida,'' Universidad Nacional de Colombia, mayo 2025, pp. 1--3.',
 'dynamics': r'Material de Sistemas Dinámicos y Control, ``Dynamic Response,'' Universidad Nacional de Colombia, material de clase.',
 'frequency': r'Material de Sistemas Dinámicos y Control, ``The Frequency-Response Design Method,'' cap. 10, material de clase.',
 'matlab': r'MathWorks, \emph{MATLAB, Simulink y Control System Toolbox}, R2026a, documentación de \texttt{lsim}, \texttt{margin}, \texttt{feedback}, \texttt{c2d} y \texttt{stepinfo}, 2026.',
 'ngspice': r'The ngspice team, \emph{ngspice User Manual}, versión 44.2. Disponible: \url{https://ngspice.sourceforge.io/docs.html}.'}

def nominal():
 return T('nominal','Parámetros de la guía',[
 ['Magnitud','Valor'],[r'$V_{\mathrm{in}}$',r'$12\,\mathrm{V}$'],
 ['$L$; $C$',r'$660\,\mu\mathrm{H}$; $20\,\mu\mathrm{F}$'],
 ['$R$; $f_s$',r'$6\,\Omega$; $10\,\mathrm{kHz}$'],
 [r"$D'=0.5$",r'$V_o=6\,\mathrm{V}$; $I_L=1\,\mathrm{A}$']])

def error_blocks():
 return [P(r'Se compara la media por periodo $\bar v_c[k]$ con el modelo $v_m[k]$ interpolado en el centro de cada periodo. Para $N$ muestras:'),
 E(r'\begin{aligned}e_k&=\bar v_c[k]-v_m[k],\\E_{\mathrm{RMS}}&=\sqrt{\frac1N\sum_{k=1}^N e_k^2},\quad E_{\max}=\max_k|e_k|.\end{aligned}','errors'),
 P(r'El error incremental resta a cada curva su propia media previa al evento, $v_{c,0}$ o $v_{m,0}$:'),
 E(r'e_{\Delta,k}=(\bar v_c[k]-v_{c,0})-(v_m[k]-v_{m,0}).','incremental'),
 P(r'$E_{\mathrm{RMS},\Delta}$ usa la misma raíz cuadrática con $e_{\Delta,k}$. El error normalizado es $100E_{\mathrm{RMS}}/|\Delta V_{\mathrm{ideal}}|$, donde el cambio nominal tiene magnitud $1.2\,\mathrm{V}$.')]

def original_reports(m,a):
 p=m['parameters']; c=a['circuit']; w=a['switched']
 b=[S('Parámetros y circuito'),nominal(),
 P(r'Se usan los valores de la guía \cite{guide}. La Fig.~\ref{fig:power} representa el circuito simulado. Se suponen DCR $r_L=0.1\,\Omega$ y ESR $r_C=0.05\,\Omega$; los semiconductores usan modelos genéricos. No son parámetros medidos.'),
 F('power',r'Etapa de potencia y sensor del netlist. El driver excita $g$; el divisor entrega $v_s=v_o/4$.'),
 F('driver',r'Driver inversor y bootstrap del netlist. Q1: 2N2222; Q2: 2N3904; Q3: 2N2907, con modelos genéricos. $sw$ es el nodo de conmutación.'),
 S('Derivación del modelo'),
 P(r'$i_L(t)$ y $v_o(t)$ son instantáneas; una barra indica promedio sobre $T_s$, mayúscula indica equilibrio y tilde indica perturbación. Se supone conducción continua (CCM), fuente constante y elementos ideales. Las ecuaciones ON/OFF son:'),
 E(r'L\frac{di_L}{dt}=\begin{cases}V_{\mathrm{in}}-v_o,&\mathrm{ON},\\-v_o,&\mathrm{OFF},\end{cases}','onoff'),
 E(r'C\frac{dv_o}{dt}=i_L-\frac{v_o}{R}\quad\text{en ambos estados}.','capacitor'),
 P(r"El driver invierte PWM: $d=1-d'$. Promediando los intervalos con pesos $d$ y $1-d$:"),
 E(r"\begin{aligned}L\dot{\bar i}_L&=V_{\mathrm{in}}(1-d')-\bar v_o,\\C\dot{\bar v}_o&=\bar i_L-\bar v_o/R.\end{aligned}",'average'),
 E(r"V_o=V_{\mathrm{in}}(1-D'),\qquad I_L=V_o/R.",'equilibrium'),
 P(r"Sustituir $\bar i_L=I_L+\tilde i_L$, $\bar v_o=V_o+\tilde v_o$ y $d'=D'+\tilde d'$ da el estado incremental $\tilde x=[\tilde i_L\;\tilde v_o]^{\mathsf T}$:"),
 E(r"\begin{aligned}\dot{\tilde x}&=\begin{bmatrix}0&-1/L\\1/C&-1/(RC)\end{bmatrix}\tilde x+\begin{bmatrix}-V_{\mathrm{in}}/L\\0\end{bmatrix}\tilde d',\\\tilde v_o&=\begin{bmatrix}0&1\end{bmatrix}\tilde x.\end{aligned}",'state'),
 P(r'Eliminando $\bar i_L$ se obtiene $LC\ddot{\bar v}_o+(L/R)\dot{\bar v}_o+\bar v_o=V_{\mathrm{in}}(1-d^{\prime})$. Con condiciones iniciales incrementales nulas:'),
 E(r"G_{d'}(s)=\frac{\widetilde V_o(s)}{\widetilde D'(s)}=\frac{-V_{\mathrm{in}}}{LCs^2+(L/R)s+1}.",'plant'),
 E(r"G_{d'}(s)=\frac{-9.090909\times10^8}{s^2+8333.333s+7.575758\times10^7}.",'numeric'),
 P(r'La tensión total es $6\,\mathrm{V}$ más la respuesta incremental. No se debe aplicar el duty absoluto al modelo incremental. Para $R$ constante, las ecuaciones promediadas son afines y también describen los escalones finitos dentro de sus hipótesis.'),
 S('Respuesta dinámica y conducción'),
 P(r'La forma canónica de segundo orden \cite{dynamics} permite identificar:'),
 E(r'\omega_n=\frac1{\sqrt{LC}},\quad\zeta=\frac{\sqrt{L/C}}{2R},\quad\omega_d=\omega_n\sqrt{1-\zeta^2}.','dynamic'),
 P(fr'$\omega_n={m["wn_rad_s"]:.3f}\,\mathrm{{rad/s}}$, $\zeta={m["zeta"]:.5f}$ y polos $-4166.667\pm j7641.758\,\mathrm{{s}}^{{-1}}$. No hay ceros finitos. La planta es estable y subamortiguada; su ganancia CC es $-12\,\mathrm{{V}}$ por unidad de $d^{{\prime}}$.'),
 E(r'\begin{aligned}M_p&=100e^{-\pi\zeta/\sqrt{1-\zeta^2}}=18.03\%,\\t_p&=\pi/\omega_d=0.411\,\mathrm{ms},\\t_{s,2\%}&\simeq4/(\zeta\omega_n)=0.960\,\mathrm{ms}.\end{aligned}','stepmetrics'),
 P(r'Para $\tilde d^{\prime}=a\,u(t-t_0)$ y $\tau=t-t_0\geq0$:'),
 E(r'\begin{aligned}\tilde v_o(\tau)&=-12a[1-e^{-\zeta\omega_n\tau}h(\tau)],\\h(\tau)&=\cos(\omega_d\tau)+\frac{\zeta\omega_n}{\omega_d}\sin(\omega_d\tau).\end{aligned}','response'),
 P(r'Así, $a=+0.1$ lleva a $4.8\,\mathrm{V}$ y $a=-0.1$ a $7.2\,\mathrm{V}$. En el punto nominal, despreciando ESR:'),
 E(r'\begin{aligned}\Delta i_{L,\mathrm{pp}}&\simeq\frac{V_{\mathrm{in}}d(1-d)}{Lf_s}=0.455\,\mathrm{A},\\i_{L,\min}&\simeq I_L-\Delta i_{L,\mathrm{pp}}/2=0.773\,\mathrm{A},\\\Delta v_{o,\mathrm{pp}}&\simeq\frac{\Delta i_{L,\mathrm{pp}}}{8Cf_s}=0.284\,\mathrm{V},\\L_{\mathrm{crit}}&=\frac{R(1-d)}{2f_s}=150\,\mu\mathrm{H}.\end{aligned}','ripple'),
 P(r'$i_{L,\min}>0$ y $L>L_{\mathrm{crit}}$ apoyan CCM nominal. El rizado no forma parte de la función de transferencia.'),
 S('Método de comparación'),
 P(r'MATLAB \cite{matlab} usa \texttt{lsim}, salida cada $2\,\mu\mathrm{s}$ y estado incremental inicial nulo. El PWM ideal integra cada tramo ON/OFF mediante exponenciales matriciales. ngspice 44.2 \cite{ngspice} usa Gear, tolerancia relativa $10^{-5}$ y paso máximo $500\,\mathrm{ns}$; parte desde reposo y se estabiliza antes del evento en $10\,\mathrm{ms}$.'),
 P(r'Cada escalón se ejecuta por separado. Se calculan medias de periodos completos de $100\,\mu\mathrm{s}$. La ventana de error es 10--$20\,\mathrm{ms}$ y la base incremental es la media de 9--$10\,\mathrm{ms}$.')]+error_blocks()
 rows=[['Magnitud',r'$\Delta d^{\prime}=+0.1$',r'$\Delta d^{\prime}=-0.1$'],[r'$V_{o,\mathrm{ideal}}$ (V)','4.800','7.200']]
 for label,key in [(r'$\bar v_{o,\infty}$ (V)','mean_final_V'),(r'$E_{\mathrm{RMS}}$ (V)','rmse_absolute_V'),(r'$E_{\mathrm{RMS},\Delta}$ (V)','rmse_incremental_V'),(r'$E_{\max}$ (V)','max_absolute_error_V'),(r'Error normalizado (\%)','rmse_step_percent')]:
  rows.append([label,*[f'{c[k][key]:.4f}' for k in ['open_up','open_down']]])
 b += [S('Resultados y discusión'),T('open-errors','Error del circuito respecto al modelo ideal',rows),
 P(r'Las Figs.~\ref{fig:open_up} y \ref{fig:open_down} muestran el sesgo estacionario cercano a $0.30\,\mathrm{V}$, mientras el error incremental es de 6--$7\,\mathrm{mV}$. Las pérdidas y el driver desplazan el equilibrio; la dinámica dominante permanece próxima a la ideal. No se fuerza la curva del circuito a iniciar en $6\,\mathrm{V}$.'),
 F('open_up',r'Escalón $d^{\prime}:0.5\to0.6$. Arriba: medias y destino ideal; abajo: rizado estacionario del circuito.'),
 F('open_down',r'Escalón $d^{\prime}:0.5\to0.4$, aplicado en $10\,\mathrm{ms}$. Se conserva el signo de la respuesta.'),
 T('open-dynamics','Dinámica del circuito respecto de su propio final',[
 ['Magnitud',r'$+0.1$',r'$-0.1$'],[r'$t_s$ (ms)','0.950','0.950'],[r'$M_p$ (\%)','16.43','16.01'],
 [r'Rizado pico a pico (V)',*[f'{c[k]["ripple_pp_V"]:.3f}' for k in ['open_up','open_down']]],
 [r'$i_{L,\min}$ (A)',*[f'{c[k]["min_current_A"]:.3f}' for k in ['open_up','open_down']]]]),
 P(r'El circuito no alcanza el destino ideal: su $t_s$ usa una banda del 2\% de su propio cambio final. En el PWM ideal, $t_s=1.05$ y $0.95\,\mathrm{ms}$, con $M_p=17.32\%$ y $16.87\%$. Las medias tienen resolución temporal de $0.1\,\mathrm{ms}$.'),
 P(fr'Reducir el paso máximo a $250\,\mathrm{{ns}}$ en el escalón ascendente de $d^{{\prime}}$ cambia las medias como máximo ${a["convergence_max_cycle_mean_V"]*1e3:.3f}\,\mathrm{{mV}}$. Esto comprueba convergencia numérica para ese caso, no exactitud física de los parámetros.'),
 S('Conclusiones'),P(r'El modelo reproduce el sentido y la oscilación amortiguada de ambos escalones. Separar sesgo y error incremental sustenta su uso para diseño de baja frecuencia. La validación física exige medir componentes y repetir los ensayos en laboratorio.')]
 yield 1,'Modelado y validación de un convertidor Buck','Modelo y simulación',r'Se deriva el modelo del Buck desde sus estados de conmutación. Se comparan la función de transferencia, el PWM ideal y un circuito completo ante dos escalones del complemento del ciclo de trabajo. Se separan sesgo estático, error incremental y rizado. Los resultados son de simulación.',b

 b=[S('Objetivo y estado experimental'),P(r'La guía exige medir $R$, $L$ y $C$ y contrastar ambos escalones con el modelo ajustado \cite{guide}. No se han recibido mediciones ni capturas físicas: el documento establece el protocolo y los registros pendientes.'),nominal(),
 P(r'Se propone una carga de $25\,\mathrm{W}$: el nominal disipa $6\,\mathrm{W}$ y a $7.2\,\mathrm{V}$ disipa $8.64\,\mathrm{W}$. Registrar temperatura y resistencia efectiva. Verificar terminales y referencias de los componentes reales.'),
 S('Identificación de parámetros'),T('measured','Registro con medidor de parámetros; P = pendiente',[
 ['Dato','Nominal','Medido','Incert.'],[r'$V_{\mathrm{in}}$ (V)','12','P','P'],[r'$R$ ($\Omega$)','6','P','P'],[r'$L$ ($\mu$H)','660','P','P'],[r'$C$ ($\mu$F)','20','P','P'],[r'$r_L$ ($\Omega$)','0.1 (sup.)','P','P'],[r'$r_C$ ($\Omega$)','0.05 (sup.)','P','P'],['PWM (kHz)','10','P','P']]),
 P(r'Registrar instrumento, identificación, calibración, frecuencia de prueba, resolución, fecha y temperatura. Medir sin energizar; comprobar ausencia de saturación del inductor bajo corriente. Conservar fotografías y datos originales.'),
 S('Modelo con parámetros medidos'),P(r'El subíndice $m$ denota parámetros medidos. La comparación principal actualiza la planta ideal:'),
 E(r'G_{d^{\prime},m}(s)=\frac{-V_{\mathrm{in},m}}{L_mC_ms^2+(L_m/R_m)s+1}.','measuredplant'),
 P(r'Como contraste adicional, incluir DCR y omitir ESR conduce a:'),
 E(r'\begin{aligned}G_{d^{\prime},r_L}(s)&=\frac{-V_{\mathrm{in},m}}{D_m(s)},\\D_m(s)&=L_mC_ms^2+(L_m/R_m+r_LC_m)s\\&\quad+1+r_L/R_m.\end{aligned}','lossplant'),
 P(r'Este segundo modelo no incorpora caídas de diodos ni driver. El analizador disponible resuelve el modelo ideal con parámetros medidos y duty registrado; no identifica automáticamente pérdidas. Inicializar con tensión y corriente previas medidas. Si falta corriente, declarar $i_L(t_i)=v_o(t_i)/R_m$ como hipótesis.'),
 S('Procedimiento de adquisición'),P(r'Comprobar continuidad, polaridad, PWM y apagado sin potencia. Verificar que aumentar $d^{\prime}$ reduce el tiempo ON. Energizar con fuente limitada y observar corriente y $v_{GS}$. En nodos flotantes usar medida diferencial apropiada; no conectar allí la masa de una sonda referida a tierra.'),
 P(r'Estabilizar con $d^{\prime}=0.5$. Aplicar por separado $0.5\to0.6$ y $0.5\to0.4$, regresando al nominal entre capturas. Registrar duty y tensión simultáneamente al menos $5\,\mathrm{ms}$ antes y $20\,\mathrm{ms}$ después. Realizar tres repeticiones de cada caso.'),
 P(r'Para rizado adquirir al menos $200\,\mathrm{kS/s}$; documentar ancho de banda y desfase de canales. Promediar periodos completos sincronizados al PWM y conservar la forma instantánea.'),S('Análisis y tablas de resultados')]+error_blocks()
 for key,change in [('up',r'$0.5\to0.6$'),('down',r'$0.5\to0.4$')]:
  b.append(T('lab-'+key,r'Resultados experimentales: $d^{\prime}$ '+change,[['Magnitud','Modelo medido','Experimento'],[r'$v_{o,0}$; $v_{o,\infty}$ (V)','Pendiente','Pendiente'],[r'$M_p$ (\%); $t_s$ (ms)','Pendiente','Pendiente'],[r'$E_{\mathrm{RMS}}$; $E_{\max}$ (V)','---','Pendiente'],[r'$E_{\mathrm{RMS},\Delta}$ (V)','---','Pendiente'],['Rizado (V)','No incluido','Pendiente']]))
 b += [P(r'Reportar media y dispersión de las tres repeticiones, ventanas y banda del 2\% respecto del cambio final de cada curva. La comparación absoluta evalúa exactitud; la incremental separa sesgo y dinámica. No afirmar cumplimiento de una banda menor que la incertidumbre instrumental.'),
 S('Discusión y criterio de cierre'),P(r'Superponer modelo nominal, modelo medido y experimento. Explicar tolerancias, pérdidas y errores instrumentales con evidencia. El cierre requiere ambas respuestas, parámetros medidos, incertidumbre, fotografías y conclusiones basadas en capturas. La validación física permanece pendiente.'),
 Block('appendix','Archivos de análisis'),P(r'El CSV contiene \texttt{time\_s}, \texttt{voltage\_V}, \texttt{dprime}, \texttt{load\_ohm} y \texttt{reference\_V}. El JSON contiene \texttt{Vin}, \texttt{L\_H}, \texttt{C\_F}, \texttt{R\_ohm}, \texttt{step\_time\_s}, instrumento y fecha; \texttt{initial\_current\_A} es opcional. Ejecutar \texttt{analyze\_experiment.py} según \texttt{project/data/README.md}. Conservar calibración y archivos originales de cada repetición.')]
 yield 2,'Validación experimental del Buck en lazo abierto','Metodología; mediciones pendientes',r'Se especifican la identificación de componentes, los dos ensayos de lazo abierto y las métricas de error. Se formula el modelo ajustado y se preparan tablas de registro. No hay datos de laboratorio: los resultados experimentales permanecen pendientes.',b

 cases=[('ref_up',r'$6\to7\,\mathrm{V}$'),('ref_down',r'$6\to5\,\mathrm{V}$'),('load_up',r'$R:+20\%$'),('load_down',r'$R:-20\%$')]
 b=[S('Especificaciones y signo del lazo'),P(r'La guía pide un compensador de la familia PID y cuatro escenarios \cite{guide}. Se elige PI ($K_d=0$). Las siguientes metas son decisiones de diseño y se aplican a la tensión media por periodo.'),
 T('specs','Metas de diseño', [['Magnitud','Criterio'],['Referencia nominal',r'$6\,\mathrm{V}$'],['Error final',r'$<20\,\mathrm{mV}$'],[r'$t_s$ en referencia',r'$<10\,\mathrm{ms}$; banda $\pm20\,\mathrm{mV}$'],[r'$M_p$ en referencia',r'$<10\%$ del escalón de $1\,\mathrm{V}$'],[r'$t_s$ en carga',r'$<10\,\mathrm{ms}$; banda $\pm0.12\,\mathrm{V}$'],['Pico en carga',r'$<0.8\,\mathrm{V}$'],['Duty físico',r'$0.05\leq d\leq0.95$'],['Margen de fase',r'$>60^\circ$ (modelo continuo)']]),
 P(r'Se define $e=r-\bar v_o$ y se diseña sobre $G_d=-G_{d^{\prime}}$, positiva. El compensador hacia $d^{\prime}$ es $H=-K$; así $G_{d^{\prime}}H=G_dK$. La Fig.~\ref{fig:control} muestra el complemento explícito.'),
 E(r'\begin{aligned}K(s)&=K_p+\frac{K_i}{s},\\d^{\prime}&=1-\operatorname{sat}(0.5+K_pe+z).\end{aligned}','controller'),
 F('control',r'Lazo de regulación. PI incluye sesgo, saturación y anti-windup. PWM y driver convierten $d^{\prime}$ en duty físico $d$.'),
 S('Diseño por respuesta en frecuencia'),P(r'Se aplica la condición de cruce de clase \cite{frequency}. Se fijan $\omega_c=1000\,\mathrm{rad/s}$ ($159.15\,\mathrm{Hz}$) y $\omega_z=3000\,\mathrm{rad/s}$, muy por debajo de $f_s=10\,\mathrm{kHz}$:'),
 E(r'\begin{aligned}A_c&=1-LC\omega_c^2,\quad B_c=L\omega_c/R,\\|G_d(j\omega_c)|&=\frac{V_{\mathrm{in}}}{\sqrt{A_c^2+B_c^2}}=12.08566\,\mathrm{V},\\K_p&=\frac{1}{|G_d(j\omega_c)|\sqrt{1+(\omega_z/\omega_c)^2}},\\K_i&=\omega_zK_p.\end{aligned}','design'),
 E(fr'\begin{{aligned}}K_p&={p["Kp"]:.9f}\,\mathrm{{V}}^{{-1}},\\K_i&={p["Ki"]:.6f}\,(\mathrm{{V\,s}})^{{-1}},\\T_i&=K_p/K_i=0.333333\,\mathrm{{ms}}.\end{{aligned}}','gains'),
 P(fr'$\angle G_d(j\omega_c)=-6.3606^\circ$ y $\angle K(j\omega_c)=-71.5651^\circ$. MATLAB \cite{{matlab}} obtiene margen de fase ${m["phase_margin_deg"]:.3f}^\circ$ y cruce ${m["gain_cross_rad_s"]:.3f}\,\mathrm{{rad/s}}$ (Fig.~\ref{{fig:bode}}).'),
 F('bode',r'Lazo continuo $K(j\omega)G_d(j\omega)$; línea vertical en $\omega_c$. No hay cruce finito de $-180^\circ$.'),
 P(r'El margen de ganancia nominal es infinito dentro del modelo continuo; no incluye retardos ni polos parásitos del hardware. La integral corrige errores constantes y se omite la derivada para evitar amplificar ruido y rizado.'),
 E(r'\begin{aligned}T(s)&=\frac{V_{\mathrm{in}}(K_ps+K_i)}{D_{\mathrm{cl}}(s)},\\D_{\mathrm{cl}}(s)&=LCs^3+(L/R)s^2\\&\quad+(1+V_{\mathrm{in}}K_p)s+V_{\mathrm{in}}K_i.\end{aligned}','closed'),
 P(fr'La respuesta continua tiene subida 10--90\% de ${m["closed_step"]["RiseTime"]*1e3:.3f}\,\mathrm{{ms}}$, establecimiento al 2\% de ${m["closed_step"]["SettlingTime"]*1e3:.3f}\,\mathrm{{ms}}$ y sobreimpulso nulo.'),
 S('Perturbaciones y algoritmo digital'),P(r'La carga cambia a $7.2$ o $4.8\,\Omega$ manteniendo $r=6\,\mathrm{V}$. Para corriente adicional extraída de la salida:'),
 E(r'\frac{\widetilde V_o}{\widetilde I_{\mathrm{carga}}}=\frac{-Ls}{LCs^2+(L/R)s+1}\frac1{1+G_dK}.','disturbance'),
 P(r'La aproximación $\tilde i_{\mathrm{carga}}\simeq-V_o\tilde R/R^2$ es local. Los ensayos de $\pm20\%$ usan $R(t)$ directamente. Al aumentar $R$, la tensión sube inicialmente porque disminuye la corriente de carga.'),
 E(r'\begin{aligned}u_k&=0.5+K_pe_k+z_k,\\d_k^{\mathrm{cmd}}&=\min(0.95,\max(0.05,u_k)),\\z_{k+1}&=\begin{cases}z_k,&\mathcal S_k,\\z_k+K_iT_se_k,&\text{en otro caso},\end{cases}\\\mathcal S_k&=(u_k\geq0.95\land e_k>0)\\&\quad\lor(u_k\leq0.05\land e_k<0).\end{aligned}','discrete'),
 P(r'El integrador se congela sólo si profundiza la saturación. Se usa $T_s=100\,\mu\mathrm{s}$, medida media del periodo completado y orden aplicada $d_k^{\mathrm{ap}}=d_{k-1}^{\mathrm{cmd}}$. En el equilibrio ideal: $V_o=6\,\mathrm{V}$, $I_L=1\,\mathrm{A}$ y $z_0=0$.'),
 F('timing',r'Temporización digital: cálculo con la media anterior y orden aplicada un periodo después. El promedio también modifica la dinámica de medida.'),
 S('Validación y alcance'),P(r'MATLAB usa \texttt{ode45}, tolerancias relativa $10^{-8}$ y absoluta $10^{-10}$, paso máximo $10\,\mu\mathrm{s}$ y tramos separados en el evento de $10\,\mathrm{ms}$. Simulink representa las mismas ecuaciones. ngspice emplea PI continuo y parte desde reposo; el PWM ideal usa PI digital con promedio y retardo. Las gráficas identifican estas realizaciones distintas.'),
 P(fr'La máxima diferencia MATLAB--Simulink es $43.414\,\mu\mathrm{{V}}$. El modelo lineal ZOH con retardo de un periodo tiene radio de polos ${m["digital_pole_radius"]:.6f}<1$. Son estables las {m["robust_cases"]} combinaciones de $R,L,C$ al 80, 100 y 120\%, tanto continuas como discretas. La malla no prueba todas las tolerancias ni la transición CCM/DCM.'),
 S('Resultados'),P(r'El error final es $|\operatorname{media}_{25\text{--}30\,\mathrm{ms}}(\bar v_o)-r_f|$. El establecimiento se obtiene del último incumplimiento de la banda desde el evento, con resolución $T_s$. El sobreimpulso se normaliza por $1\,\mathrm{V}$ en referencia; en carga se mide $\max|\bar v_o-6|$. Las Figs.~\ref{fig:ref_up}--\ref{fig:load_down} muestran los cuatro casos.')]
 for data,label,title in [(w,'pwm','PWM ideal con PI digital'),(c,'circuit','Circuito con PI continuo')]:
  b.append(T(label,title,[['Caso',r'$t_s$ (ms)',r'$|e_\infty|$ (mV)','$M_p$/pico','Rizado (V)'],*[[name,f'{data[k]["settling_s"]*1e3:.2f}',f'{data[k]["tail_error_V"]*1e3:.4f}',f'{data[k]["overshoot_percent"]:.3f}'+r'\%' if k.startswith('ref') else f'{data[k]["peak_deviation_V"]:.3f} V',f'{data[k]["ripple_pp_V"]:.3f}'] for k,name in cases]]))
 b += [P(r'El rizado es pico a pico. Los errores medios menores que $0.02\,\mathrm{mV}$ son precisión numérica del modelo, no una garantía para ADC reales. Ambas realizaciones cumplen las metas nominales.'),
 *[F(k,'Respuesta a '+name+r'. Arriba: medias y banda de establecimiento; abajo: rizado estacionario del circuito.') for k,name in cases],
 P(r'El circuito tiene menores picos de carga y mayor establecimiento en referencia que el PWM digital. Difieren tanto pérdidas como temporización; no se atribuye toda la diferencia a los semiconductores. La integral corrige el sesgo, pero no elimina el rizado de conmutación.'),
 S('Conclusiones'),P(r'El PI cumple los escenarios nominales y mantiene estabilidad en la malla evaluada. El signo inversor, los límites y el anti-windup son explícitos. La validación física requiere verificar adquisición, retardo y apagado y repetir los cuatro casos.')]
 yield 3,'Diseño y validación del regulador PI','Control de tensión de salida',r'Se diseña un PI mediante respuesta en frecuencia para regular 6 V. Se documentan signo, saturación, anti-windup y discretización. Cuatro escenarios de referencia y carga se contrastan en modelos promediados, PWM digital y circuito completo. Los resultados son exclusivamente numéricos.',b

 b=[S('Alcance'),P(r'La guía exige implementar y ajustar el compensador y repetir cuatro ensayos físicos \cite{guide}. Existe un núcleo C validado en computador; tarjeta, integración ADC/PWM, calibración y capturas están pendientes. No se declara completada la implementación física.'),
 S('Adquisición y calibración'),P(r'El divisor nominal tiene $R_t=30\,\mathrm{k}\Omega$ y $R_b=10\,\mathrm{k}\Omega$. Para un ADC unipolar de $N$ bits:'),
 E(r'\begin{aligned}v_s[k]&=\frac{n_kV_{\mathrm{ADC}}}{2^N-1},\\\hat v_o[k]&=a\,v_s[k]+b,\quad a_{\mathrm{nom}}=1+R_t/R_b=4,\\\Delta v_{o,\mathrm{LSB}}&=\frac{aV_{\mathrm{ADC}}}{2^N-1}.\end{aligned}','adc'),
 P(r'Obtener $a,b$ con dos tensiones conocidas y validar con un tercer punto. Medir referencia y resistencias, registrar residuos y comprobar rango del ADC durante transitorios. Comparar resolución efectiva, ruido e incertidumbre con la meta de $20\,\mathrm{mV}$.'),
 P(r'La media por periodo requiere varias muestras sincronizadas; una sola muestra no reproduce automáticamente el promedio simulado. Deben confirmarse $N$, $V_{\mathrm{ADC}}$, frecuencia de adquisición y filtro.'),
 T('hardware','Registro de adquisición y actuador',[['Dato','Valor o evidencia'],['Tarjeta, MCU y reloj','Pendiente'],[r'$N$, $V_{\mathrm{ADC}}$, frecuencia ADC','Pendiente'],[r'$a,b$ y residuos de calibración','Pendiente'],['Muestras por periodo; filtro','Pendiente'],['PWM (frecuencia; bits)','Pendiente'],['Retardo, jitter y ejecución','Pendiente'],['Instrumentos, fecha y fotografía','Pendiente']]),
 S('Algoritmo y temporización'),P(r'Se usa $e_k=r_k-\hat v_{o,k}$ y se devuelve $d^{\prime}_k=1-d_k^{\mathrm{cmd}}$. Verificar con osciloscopio la inversión del driver antes de conectar potencia.'),
 E(r'\begin{aligned}u_k&=0.5+K_pe_k+z_k,\\d_k^{\mathrm{cmd}}&=\operatorname{clip}(u_k,0.05,0.95),\\z_{k+1}&=z_k+\gamma_ke_k,\\\gamma_k&=\begin{cases}0,&u_k\geq0.95,\ e_k>0,\\0,&u_k\leq0.05,\ e_k<0,\\K_iT_s,&\text{en otro caso}.\end{cases}\end{aligned}','firmware'),
 P(r'La rutina calcula la orden con la integral anterior y luego actualiza el estado. Cada $100\,\mu\mathrm{s}$ completa la media previa y precarga el PWM para el periodo siguiente (Fig.~\ref{fig:timing}). Verificar latencia con un pin de diagnóstico y ausencia de interrupciones perdidas.'),
 F('timing',r'Secuencia que debe reproducir la tarjeta: media, cálculo y aplicación retardada de la orden.'),
 T('coefficients','Coeficientes diseñados y cargados',[['Magnitud','Diseño / núcleo C','En tarjeta'],[r'$K_p$ ($\mathrm{V}^{-1}$)',f'{p["Kp"]:.9f}','Pendiente'],[r'$K_i$ ($(\mathrm{V\,s})^{-1}$)',f'{p["Ki"]:.6f}','Pendiente'],[r'$K_iT_s$ ($\mathrm{V}^{-1}$)',f'{p["Ki"]*p["Ts"]:.9f}','Pendiente'],[r'$T_s$ ($\mu$s)','100','Pendiente'],[r'$d_{\min}$; $d_{\max}$','0.05; 0.95','Pendiente']]),
 P(r'El núcleo devuelve $d^{\prime}=1$ al deshabilitarse o enclavar fallo; detecta valores no finitos, tensiones fuera de rango y salida mayor que $8.5\,\mathrm{V}$. Verificar apagado eléctrico real. La rutina no mide corriente ni sustituye la protección de sobrecorriente.'),
 S('Puesta en marcha y reajuste'),P(r'Usar el montaje ya validado en lazo abierto, fuente limitada y referencia gradual. El arranque gradual debe integrarse en la tarjeta; no está implícito en el PI. Verificar saturación, recuperación de la integral y apagado antes de alcanzar $6\,\mathrm{V}$.'),
 P(r'Si se requiere reajuste, actualizar $G_d$ con parámetros medidos y considerar el retardo real. Recalcular la condición $|K(j\omega_c)G_d(j\omega_c)|=1$, reducir cruce si el margen resulta insuficiente y conservar ganancias y capturas anteriores.'),
 T('retuning','Registro de reajuste',[['Dato','Antes','Después'],[r'$K_p$; $K_i$','Diseño','Pendiente'],['Cruce y margen','Diseño','Pendiente'],['Motivo y evidencia','---','Pendiente'],['Versión y fecha','Pendiente','Pendiente']]),
 S('Ensayos de aceptación'),P(r'Ejecutar por separado $r:6\to7\,\mathrm{V}$, $r:6\to5\,\mathrm{V}$, $R:6\to7.2\,\Omega$ y $R:6\to4.8\,\Omega$, estos últimos con $r=6\,\mathrm{V}$. Regresar al nominal y realizar tres repeticiones por caso. Capturar referencia, tensión, orden y carga desde $5\,\mathrm{ms}$ antes hasta al menos $20\,\mathrm{ms}$ después.'),
 P(r'Usar $e_\infty=r_f-\operatorname{media}(\bar v_o)$ en una ventana final declarada. Medir $t_s$ con banda $\pm20\,\mathrm{mV}$ en referencia y $\pm0.12\,\mathrm{V}$ en carga. Medir sobreimpulso porcentual en referencia, pico $\max|\bar v_o-6|$ en carga y rizado instantáneo.'),
 T('physical','Resultados físicos; P = pendiente',[['Caso',r'$t_s$ (ms)',r'$|e_\infty|$ (mV)','$M_p$/pico','Rizado (V)'],*[[name,'P','P','P','P'] for _,name in cases]]),
 P(r'Agregar duty mínimo y máximo, corriente máxima, incertidumbre y dispersión. Comparar con la entrega 3 y explicar cuantización, latencia, pérdidas y saturación. Todo reajuste exige repetir los cuatro casos conservando el antes y después.'),
 S('Estado y conclusión experimental'),P(r'Faltan montaje identificado, firmware integrado, coeficientes cargados, calibración, temporización, apagado y doce capturas mínimas. La simulación sustenta el ajuste inicial, pero no demuestra desempeño físico.'),
 Block('appendix','Evidencia reproducible'),P(r'Conservar firmware, \texttt{buck\_control.c}, configuración de temporizador, calibración y CSV originales. El protocolo está en \texttt{project/hardware/implementacion.md}. El analizador compara el modelo promediado con duty y carga registrados; la evaluación del controlador debe añadir las métricas de aceptación y su incertidumbre.')]
 yield 4,'Implementación y validación experimental del PI','Metodología digital; ensayos pendientes',r'Se documenta la integración del PI con ADC y PWM: calibración, temporización, saturación y reajuste. Se establecen cuatro pruebas de aceptación. La integración física, las mediciones y los resultados experimentales permanecen pendientes.',b

def reports(m,a):
 from hardware_report_content import revise
 for spec in original_reports(m,a):
  yield revise(spec)
