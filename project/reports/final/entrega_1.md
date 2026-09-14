# Modelado y validación de un convertidor Buck

Entrega 1: Modelo y simulación

Martín Ramírez Espinosa — maramirezes@unal.edu.co

Jerónimo Vargas Orozco — jevargaso@unal.edu.co

Andrew Esteban Henao Becerra — anhenaobe@unal.edu.co

Mateo Alexander Cardenas Cuesta — macardenascu@unal.edu.co

Universidad Nacional de Colombia, Sede Manizales

## Resumen

Se deriva el modelo del Buck desde sus estados de conmutación. Se comparan la función de transferencia, el PWM ideal y un circuito completo ante dos escalones del complemento del ciclo de trabajo. Se separan sesgo estático, error incremental y rizado. Los resultados son de simulación.

## Parámetros y circuito

*Parámetros de la guía*

| Magnitud | Valor |

| --- | --- |

| $V_{\mathrm{in}}$ | $12\,\mathrm{V}$ |

| $L$; $C$ | $660\,\mu\mathrm{H}$; $20\,\mu\mathrm{F}$ |

| $R$; $f_s$ | $6\,\Omega$; $10\,\mathrm{kHz}$ |

| $D'=0.5$ | $V_o=6\,\mathrm{V}$; $I_L=1\,\mathrm{A}$ |

Se usan los valores de la guía [1]. La Fig.~1 representa el circuito simulado. Se suponen DCR $r_L=0.1\,\Omega$ y ESR $r_C=0.05\,\Omega$; los semiconductores usan modelos genéricos. No son parámetros medidos.

*Figura (power): Etapa de potencia y sensor del netlist. El driver excita $g$; el divisor entrega $v_s=v_o/4$.*

Fuente vectorial en entrega_1.tex; datos en data/.

*Figura (driver): Driver inversor y bootstrap del netlist. Q1: 2N2222; Q2: 2N3904; Q3: 2N2907, con modelos genéricos. $sw$ es el nodo de conmutación.*

Fuente vectorial en entrega_1.tex; datos en data/.

## Derivación del modelo

$i_L(t)$ y $v_o(t)$ son instantáneas; una barra indica promedio sobre $T_s$, mayúscula indica equilibrio y tilde indica perturbación. Se supone conducción continua (CCM), fuente constante y elementos ideales. Las ecuaciones ON/OFF son:

$$
L\frac{di_L}{dt}=\begin{cases}V_{\mathrm{in}}-v_o,&\mathrm{ON},\\-v_o,&\mathrm{OFF},\end{cases}
$$

$$
C\frac{dv_o}{dt}=i_L-\frac{v_o}{R}\quad\text{en ambos estados}.
$$

El driver invierte PWM: $d=1-d'$. Promediando los intervalos con pesos $d$ y $1-d$:

$$
\begin{aligned}L\dot{\bar i}_L&=V_{\mathrm{in}}(1-d')-\bar v_o,\\C\dot{\bar v}_o&=\bar i_L-\bar v_o/R.\end{aligned}
$$

$$
V_o=V_{\mathrm{in}}(1-D'),\qquad I_L=V_o/R.
$$

Sustituir $\bar i_L=I_L+\tilde i_L$, $\bar v_o=V_o+\tilde v_o$ y $d'=D'+\tilde d'$ da el estado incremental $\tilde x=[\tilde i_L\;\tilde v_o]^{\mathsf T}$:

$$
\begin{aligned}\dot{\tilde x}&=\begin{bmatrix}0&-1/L\\1/C&-1/(RC)\end{bmatrix}\tilde x+\begin{bmatrix}-V_{\mathrm{in}}/L\\0\end{bmatrix}\tilde d',\\\tilde v_o&=\begin{bmatrix}0&1\end{bmatrix}\tilde x.\end{aligned}
$$

Eliminando $\bar i_L$ se obtiene $LC\ddot{\bar v}_o+(L/R)\dot{\bar v}_o+\bar v_o=V_{\mathrm{in}}(1-d^{\prime})$. Con condiciones iniciales incrementales nulas:

$$
G_{d'}(s)=\frac{\widetilde V_o(s)}{\widetilde D'(s)}=\frac{-V_{\mathrm{in}}}{LCs^2+(L/R)s+1}.
$$

$$
G_{d'}(s)=\frac{-9.090909\times10^8}{s^2+8333.333s+7.575758\times10^7}.
$$

La tensión total es $6\,\mathrm{V}$ más la respuesta incremental. No se debe aplicar el duty absoluto al modelo incremental. Para $R$ constante, las ecuaciones promediadas son afines y también describen los escalones finitos dentro de sus hipótesis.

## Respuesta dinámica y conducción

La forma canónica de segundo orden [2] permite identificar:

$$
\omega_n=\frac1{\sqrt{LC}},\quad\zeta=\frac{\sqrt{L/C}}{2R},\quad\omega_d=\omega_n\sqrt{1-\zeta^2}.
$$

$\omega_n=8703.883\,\mathrm{rad/s}$, $\zeta=0.47871$ y polos $-4166.667\pm j7641.758\,\mathrm{s}^{-1}$. No hay ceros finitos. La planta es estable y subamortiguada; su ganancia CC es $-12\,\mathrm{V}$ por unidad de $d^{\prime}$.

$$
\begin{aligned}M_p&=100e^{-\pi\zeta/\sqrt{1-\zeta^2}}=18.03\%,\\t_p&=\pi/\omega_d=0.411\,\mathrm{ms},\\t_{s,2\%}&\simeq4/(\zeta\omega_n)=0.960\,\mathrm{ms}.\end{aligned}
$$

Para $\tilde d^{\prime}=a\,u(t-t_0)$ y $\tau=t-t_0\geq0$:

$$
\begin{aligned}\tilde v_o(\tau)&=-12a[1-e^{-\zeta\omega_n\tau}h(\tau)],\\h(\tau)&=\cos(\omega_d\tau)+\frac{\zeta\omega_n}{\omega_d}\sin(\omega_d\tau).\end{aligned}
$$

Así, $a=+0.1$ lleva a $4.8\,\mathrm{V}$ y $a=-0.1$ a $7.2\,\mathrm{V}$. En el punto nominal, despreciando ESR:

$$
\begin{aligned}\Delta i_{L,\mathrm{pp}}&\simeq\frac{V_{\mathrm{in}}d(1-d)}{Lf_s}=0.455\,\mathrm{A},\\i_{L,\min}&\simeq I_L-\Delta i_{L,\mathrm{pp}}/2=0.773\,\mathrm{A},\\\Delta v_{o,\mathrm{pp}}&\simeq\frac{\Delta i_{L,\mathrm{pp}}}{8Cf_s}=0.284\,\mathrm{V},\\L_{\mathrm{crit}}&=\frac{R(1-d)}{2f_s}=150\,\mu\mathrm{H}.\end{aligned}
$$

$i_{L,\min}>0$ y $L>L_{\mathrm{crit}}$ apoyan CCM nominal. El rizado no forma parte de la función de transferencia.

## Método de comparación

MATLAB [3] usa `lsim`, salida cada $2\,\mu\mathrm{s}$ y estado incremental inicial nulo. El PWM ideal integra cada tramo ON/OFF mediante exponenciales matriciales. ngspice 44.2 [4] usa Gear, tolerancia relativa $10^{-5}$ y paso máximo $500\,\mathrm{ns}$; parte desde reposo y se estabiliza antes del evento en $10\,\mathrm{ms}$.

Cada escalón se ejecuta por separado. Se calculan medias de periodos completos de $100\,\mu\mathrm{s}$. La ventana de error es 10--$20\,\mathrm{ms}$ y la base incremental es la media de 9--$10\,\mathrm{ms}$.

Se compara la media por periodo $\bar v_c[k]$ con el modelo $v_m[k]$ interpolado en el centro de cada periodo. Para $N$ muestras:

$$
\begin{aligned}e_k&=\bar v_c[k]-v_m[k],\\E_{\mathrm{RMS}}&=\sqrt{\frac1N\sum_{k=1}^N e_k^2},\quad E_{\max}=\max_k|e_k|.\end{aligned}
$$

El error incremental resta a cada curva su propia media previa al evento, $v_{c,0}$ o $v_{m,0}$:

$$
e_{\Delta,k}=(\bar v_c[k]-v_{c,0})-(v_m[k]-v_{m,0}).
$$

$E_{\mathrm{RMS},\Delta}$ usa la misma raíz cuadrática con $e_{\Delta,k}$. El error normalizado es $100E_{\mathrm{RMS}}/|\Delta V_{\mathrm{ideal}}|$, donde el cambio nominal tiene magnitud $1.2\,\mathrm{V}$.

## Resultados y discusión

*Error del circuito respecto al modelo ideal*

| Magnitud | $\Delta d^{\prime}=+0.1$ | $\Delta d^{\prime}=-0.1$ |

| --- | --- | --- |

| $V_{o,\mathrm{ideal}}$ (V) | 4.800 | 7.200 |

| $\bar v_{o,\infty}$ (V) | 4.5060 | 6.8969 |

| $E_{\mathrm{RMS}}$ (V) | 0.2934 | 0.3025 |

| $E_{\mathrm{RMS},\Delta}$ (V) | 0.0060 | 0.0069 |

| $E_{\max}$ (V) | 0.2975 | 0.3170 |

| Error normalizado (\%) | 24.4506 | 25.2111 |

Las Figs.~3 y 4 muestran el sesgo estacionario cercano a $0.30\,\mathrm{V}$, mientras el error incremental es de 6--$7\,\mathrm{mV}$. Las pérdidas y el driver desplazan el equilibrio; la dinámica dominante permanece próxima a la ideal. No se fuerza la curva del circuito a iniciar en $6\,\mathrm{V}$.

*Figura (open_up): Escalón $d^{\prime}:0.5\to0.6$. Arriba: medias y destino ideal; abajo: rizado estacionario del circuito.*

Fuente vectorial en entrega_1.tex; datos en data/.

*Figura (open_down): Escalón $d^{\prime}:0.5\to0.4$, aplicado en $10\,\mathrm{ms}$. Se conserva el signo de la respuesta.*

Fuente vectorial en entrega_1.tex; datos en data/.

*Dinámica del circuito respecto de su propio final*

| Magnitud | $+0.1$ | $-0.1$ |

| --- | --- | --- |

| $t_s$ (ms) | 0.950 | 0.950 |

| $M_p$ (\%) | 16.43 | 16.01 |

| Rizado pico a pico (V) | 0.280 | 0.281 |

| $i_{L,\min}$ (A) | 0.458 | 0.807 |

El circuito no alcanza el destino ideal: su $t_s$ usa una banda del 2\% de su propio cambio final. En el PWM ideal, $t_s=1.05$ y $0.95\,\mathrm{ms}$, con $M_p=17.32\%$ y $16.87\%$. Las medias tienen resolución temporal de $0.1\,\mathrm{ms}$.

Reducir el paso máximo a $250\,\mathrm{ns}$ en el escalón ascendente de $d^{\prime}$ cambia las medias como máximo $0.927\,\mathrm{mV}$. Esto comprueba convergencia numérica para ese caso, no exactitud física de los parámetros.

## Relación con la placa diseñada

El circuito completo evaluado aquí conserva el driver discreto BJT y sus modelos genéricos. La placa posterior usa IR2110, inversión HCT14, dos inductores de $330\,\mu\mathrm{H}$ en serie y shunt de $0.05\,\Omega$. El divisor pasa de $30/10\,\mathrm{k}\Omega$ a $3/1\,\mathrm{k}\Omega$. Se conserva $d=1-d^{\prime}$, pero cambian pérdidas y retardos. Por ello estas curvas no validan por sí solas la placa IR2110; su estimación separada se presenta en la entrega 3.

## Conclusiones

El modelo reproduce el sentido y la oscilación amortiguada de ambos escalones. Separar sesgo y error incremental sustenta su uso para diseño de baja frecuencia. La validación física exige medir componentes y repetir los ensayos en laboratorio.

## Referencias

[1] J. D. Bastidas Rodríguez, ``Proyecto de Curso: Convertidor Buck con control de tensión de salida, Universidad Nacional de Colombia, mayo 2025, pp. 1--3.

[2] Material de Sistemas Dinámicos y Control, ``Dynamic Response, Universidad Nacional de Colombia, material de clase.

[3] MathWorks, *MATLAB, Simulink y Control System Toolbox*, R2026a, documentación de `lsim`, `margin`, `feedback`, `c2d` y `stepinfo`, 2026.

[4] The ngspice team, *ngspice User Manual*, versión 44.2. Disponible: https://ngspice.sourceforge.io/docs.html.
