# Diseño y validación del regulador PI

Entrega 3: Control de tensión de salida

Martín Ramírez Espinosa — maramirezes@unal.edu.co

Jerónimo Vargas Orozco — jevargaso@unal.edu.co

Andrew Esteban Henao Becerra — anhenaobe@unal.edu.co

Mateo Alexander Cardenas Cuesta — macardenascu@unal.edu.co

Universidad Nacional de Colombia, Sede Manizales

## Resumen

Se diseña un PI mediante respuesta en frecuencia para regular 6 V. Se documentan signo, saturación, anti-windup y discretización. Cuatro escenarios de referencia y carga se contrastan en modelos promediados, PWM digital y circuito completo. Los resultados son exclusivamente numéricos.

## Especificaciones y signo del lazo

La guía pide un compensador de la familia PID y cuatro escenarios [1]. Se elige PI ($K_d=0$). Las siguientes metas son decisiones de diseño y se aplican a la tensión media por periodo.

*Metas de diseño*

| Magnitud | Criterio |

| --- | --- |

| Referencia nominal | $6\,\mathrm{V}$ |

| Error final | $<20\,\mathrm{mV}$ |

| $t_s$ en referencia | $<10\,\mathrm{ms}$; banda $\pm20\,\mathrm{mV}$ |

| $M_p$ en referencia | $<10\%$ del escalón de $1\,\mathrm{V}$ |

| $t_s$ en carga | $<10\,\mathrm{ms}$; banda $\pm0.12\,\mathrm{V}$ |

| Pico en carga | $<0.8\,\mathrm{V}$ |

| Duty físico | $0.05\leq d\leq0.95$ |

| Margen de fase | $>60^\circ$ (modelo continuo) |

Se define $e=r-\bar v_o$ y se diseña sobre $G_d=-G_{d^{\prime}}$, positiva. El compensador hacia $d^{\prime}$ es $H=-K$; así $G_{d^{\prime}}H=G_dK$. La Fig.~1 muestra el complemento explícito.

$$
\begin{aligned}K(s)&=K_p+\frac{K_i}{s},\\d^{\prime}&=1-\operatorname{sat}(0.5+K_pe+z).\end{aligned}
$$

*Figura (control): Lazo de regulación. PI incluye sesgo, saturación y anti-windup. PWM y driver convierten $d^{\prime}$ en duty físico $d$.*

Fuente vectorial en entrega_3.tex; datos en data/.

## Diseño por respuesta en frecuencia

Se aplica la condición de cruce de clase [2]. Se fijan $\omega_c=1000\,\mathrm{rad/s}$ ($159.15\,\mathrm{Hz}$) y $\omega_z=3000\,\mathrm{rad/s}$, muy por debajo de $f_s=10\,\mathrm{kHz}$:

$$
\begin{aligned}A_c&=1-LC\omega_c^2,\quad B_c=L\omega_c/R,\\|G_d(j\omega_c)|&=\frac{V_{\mathrm{in}}}{\sqrt{A_c^2+B_c^2}}=12.08566\,\mathrm{V},\\K_p&=\frac{1}{|G_d(j\omega_c)|\sqrt{1+(\omega_z/\omega_c)^2}},\\K_i&=\omega_zK_p.\end{aligned}
$$

$$
\begin{aligned}K_p&=0.026165529\,\mathrm{V}^{-1},\\K_i&=78.496586\,(\mathrm{V\,s})^{-1},\\T_i&=K_p/K_i=0.333333\,\mathrm{ms}.\end{aligned}
$$

$\angle G_d(j\omega_c)=-6.3606^\circ$ y $\angle K(j\omega_c)=-71.5651^\circ$. MATLAB [3] obtiene margen de fase $102.075^\circ$ y cruce $1000.019\,\mathrm{rad/s}$ (Fig.~2).

*Figura (bode): Lazo continuo $K(j\omega)G_d(j\omega)$; línea vertical en $\omega_c$. No hay cruce finito de $-180^\circ$.*

Fuente vectorial en entrega_3.tex; datos en data/.

El margen de ganancia nominal es infinito dentro del modelo continuo; no incluye retardos ni polos parásitos del hardware. La integral corrige errores constantes y se omite la derivada para evitar amplificar ruido y rizado.

$$
\begin{aligned}T(s)&=\frac{V_{\mathrm{in}}(K_ps+K_i)}{D_{\mathrm{cl}}(s)},\\D_{\mathrm{cl}}(s)&=LCs^3+(L/R)s^2\\&\quad+(1+V_{\mathrm{in}}K_p)s+V_{\mathrm{in}}K_i.\end{aligned}
$$

La respuesta continua tiene subida 10--90\% de $2.613\,\mathrm{ms}$, establecimiento al 2\% de $4.832\,\mathrm{ms}$ y sobreimpulso nulo.

## Perturbaciones y algoritmo digital

La carga cambia a $7.2$ o $4.8\,\Omega$ manteniendo $r=6\,\mathrm{V}$. Para corriente adicional extraída de la salida:

$$
\frac{\widetilde V_o}{\widetilde I_{\mathrm{carga}}}=\frac{-Ls}{LCs^2+(L/R)s+1}\frac1{1+G_dK}.
$$

La aproximación $\tilde i_{\mathrm{carga}}\simeq-V_o\tilde R/R^2$ es local. Los ensayos de $\pm20\%$ usan $R(t)$ directamente. Al aumentar $R$, la tensión sube inicialmente porque disminuye la corriente de carga.

$$
\begin{aligned}u_k&=0.5+K_pe_k+z_k,\\d_k^{\mathrm{cmd}}&=\min(0.95,\max(0.05,u_k)),\\z_{k+1}&=\begin{cases}z_k,&\mathcal S_k,\\z_k+K_iT_se_k,&\text{en otro caso},\end{cases}\\\mathcal S_k&=(u_k\geq0.95\land e_k>0)\\&\quad\lor(u_k\leq0.05\land e_k<0).\end{aligned}
$$

El integrador se congela sólo si profundiza la saturación. Se usa $T_s=100\,\mu\mathrm{s}$, medida media del periodo completado y orden aplicada $d_k^{\mathrm{ap}}=d_{k-1}^{\mathrm{cmd}}$. En el equilibrio ideal: $V_o=6\,\mathrm{V}$, $I_L=1\,\mathrm{A}$ y $z_0=0$.

*Figura (timing): Temporización digital: cálculo con la media anterior y orden aplicada un periodo después. El promedio también modifica la dinámica de medida.*

Fuente vectorial en entrega_3.tex; datos en data/.

## Validación y alcance

MATLAB usa `ode45`, tolerancias relativa $10^{-8}$ y absoluta $10^{-10}$, paso máximo $10\,\mu\mathrm{s}$ y tramos separados en el evento de $10\,\mathrm{ms}$. Simulink representa las mismas ecuaciones. ngspice emplea PI continuo y parte desde reposo; el PWM ideal usa PI digital con promedio y retardo. Las gráficas identifican estas realizaciones distintas.

La máxima diferencia MATLAB--Simulink es $43.414\,\mu\mathrm{V}$. El modelo lineal ZOH con retardo de un periodo tiene radio de polos $0.915396<1$. Son estables las 27 combinaciones de $R,L,C$ al 80, 100 y 120\%, tanto continuas como discretas. La malla no prueba todas las tolerancias ni la transición CCM/DCM.

## Resultados

El error final es $|\operatorname{media}_{25\text{--}30\,\mathrm{ms}}(\bar v_o)-r_f|$. El establecimiento se obtiene del último incumplimiento de la banda desde el evento, con resolución $T_s$. El sobreimpulso se normaliza por $1\,\mathrm{V}$ en referencia; en carga se mide $\max|\bar v_o-6|$. Las Figs.~4--7 muestran los cuatro casos.

*PWM ideal con PI digital*

| Caso | $t_s$ (ms) | $|e_\infty|$ (mV) | $M_p$/pico | Rizado (V) |

| --- | --- | --- | --- | --- |

| $6\to7\,\mathrm{V}$ | 4.15 | 0.0002 | 0.000\% | 0.277 |

| $6\to5\,\mathrm{V}$ | 4.05 | 0.0002 | 0.000\% | 0.277 |

| $R:+20\%$ | 0.85 | 0.0000 | 0.560 V | 0.286 |

| $R:-20\%$ | 0.85 | 0.0000 | 0.691 V | 0.282 |

*Circuito con PI continuo*

| Caso | $t_s$ (ms) | $|e_\infty|$ (mV) | $M_p$/pico | Rizado (V) |

| --- | --- | --- | --- | --- |

| $6\to7\,\mathrm{V}$ | 4.95 | 0.0048 | 0.012\% | 0.279 |

| $6\to5\,\mathrm{V}$ | 4.95 | 0.0110 | 0.012\% | 0.288 |

| $R:+20\%$ | 0.65 | 0.0146 | 0.487 V | 0.293 |

| $R:-20\%$ | 0.65 | 0.0159 | 0.605 V | 0.289 |

El rizado es pico a pico. Los errores medios menores que $0.02\,\mathrm{mV}$ son precisión numérica del modelo, no una garantía para ADC reales. Ambas realizaciones cumplen las metas nominales.

*Figura (ref_up): Respuesta a $6\to7\,\mathrm{V}$. Arriba: medias y banda de establecimiento; abajo: rizado estacionario del circuito.*

Fuente vectorial en entrega_3.tex; datos en data/.

*Figura (ref_down): Respuesta a $6\to5\,\mathrm{V}$. Arriba: medias y banda de establecimiento; abajo: rizado estacionario del circuito.*

Fuente vectorial en entrega_3.tex; datos en data/.

*Figura (load_up): Respuesta a $R:+20\%$. Arriba: medias y banda de establecimiento; abajo: rizado estacionario del circuito.*

Fuente vectorial en entrega_3.tex; datos en data/.

*Figura (load_down): Respuesta a $R:-20\%$. Arriba: medias y banda de establecimiento; abajo: rizado estacionario del circuito.*

Fuente vectorial en entrega_3.tex; datos en data/.

El circuito tiene menores picos de carga y mayor establecimiento en referencia que el PWM digital. Difieren tanto pérdidas como temporización; no se atribuye toda la diferencia a los semiconductores. La integral corrige el sesgo, pero no elimina el rizado de conmutación.

## Vínculo con el procedimiento de clase

El capítulo 10 de clase, sección 7, lámina 90, describe el PI y recomienda normalmente un cero muy inferior al cruce para reducir su pérdida de fase [2]. Aquí se adopta deliberadamente $\omega_z=3000\,\mathrm{rad/s}>\omega_c=1000\,\mathrm{rad/s}$: el PI aporta aproximadamente $-71.565^\circ$ y la planta $-6.36^\circ$, dejando $102.07^\circ$ de margen continuo. La elección aumenta la acción integral y se acepta por el margen calculado y los ensayos numéricos; no reproduce la recomendación usual de ubicación del cero. El procedimiento conserva selección de cruce, normalización de ganancia, verificación de margen y comprobación transitoria.

## Estimación adicional de la realización STM32

Se seleccionó STM32F103C8T6 externo, con PI C, ADC de 12 bits, 20 muestras por periodo y PWM de $10\,\mathrm{kHz}$. La simulación adicional ejecuta el algoritmo C e incluye media, cuantización y un periodo de retardo; no sustituye las curvas anteriores.

*Alcance de cada realización*

| Realización | Hipótesis principales |

| --- | --- |

| Promediado / continuo | Planta ideal; PI continuo |

| PWM ideal / digital | Media y retardo; conmutación ideal |

| ngspice / BJT | PI continuo; DCR 0.1 y ESR 0.05 ohm |

| Estimación PCB / C | DCR 0.20, ESR 0.15, shunt 0.05 ohm; ADC y retardo |

La estimación PCB usa $R_{\mathrm{DS}}=0.022\,\Omega$, $V_F=0.45\,\mathrm{V}$ y retardos de encendido/apagado de 120/94 ns como supuestos. Euler usa paso de $0.5\,\mu\mathrm{s}$ con fracción de flanco PWM; parte de energía nula y aplica el evento tras 800 ms. Se muestran 40 ms con evento en 10 ms. No modela saturación, térmica, EMI ni la recarga real del bootstrap.

*Resultados adicionales estimados; no medidos*

| Caso | $t_s$ (ms) | $|e_\infty|$ (mV) |

| --- | --- | --- |

| 6 a 7 V | 4.30 | 0.364 |

| 6 a 5 V | 4.30 | 0.988 |

| 6 a 7.2 ohm | 0.80 | 0.253 |

| 6 a 4.8 ohm | 0.90 | 0.176 |

Las bandas son $\pm20\,\mathrm{mV}$ en referencia y $\pm0.12\,\mathrm{V}$ en carga. Seis escenarios no activan la protección simulada; corriente máxima $1.549272\,\mathrm{A}$. Reducir el paso a $0.25\,\mu\mathrm{s}$ cambia la media como máximo $1.345\,\mathrm{mV}$ en referencia ascendente. Los umbrales nominales de protección no son tolerancias garantizadas.

## Conclusiones

El PI cumple los escenarios nominales y mantiene estabilidad en la malla evaluada. El signo inversor, los límites y el anti-windup son explícitos. La validación física requiere verificar adquisición, retardo y apagado y repetir los cuatro casos.

## Referencias

[1] J. D. Bastidas Rodríguez, ``Proyecto de Curso: Convertidor Buck con control de tensión de salida, Universidad Nacional de Colombia, mayo 2025, pp. 1--3.

[2] Material de Sistemas Dinámicos y Control, ``The Frequency-Response Design Method, cap. 10, material de clase.

[3] MathWorks, *MATLAB, Simulink y Control System Toolbox*, R2026a, documentación de `lsim`, `margin`, `feedback`, `c2d` y `stepinfo`, 2026.
