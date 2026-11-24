function e3_figures(mode)
%E3_FIGURES  Figures for the Entrega 3 slides and report (run e3_main first).
%   e3_figures('slides') -> ../figuras/*.png (2x, white background) and the
%                           equation images (transparent PNG)
%   e3_figures('report') -> ../figuras/informe/*.pdf (vector, IEEE column sizes)
if nargin < 1, mode = 'slides'; end
here = fileparts(mfilename('fullpath'));
addpath(here);
L = load(fullfile(here, '..', 'resultados', 'e3_sims.mat'));
res = L.res; sims = L.sims; rob = L.rob; p = L.p; base = L.base;
S = e3_style(mode);
rep = strcmp(mode, 'report');
if rep
    figd = fullfile(here, '..', 'figuras', 'informe');
else
    figd = fullfile(here, '..', 'figuras');
end
if ~exist(figd, 'dir'), mkdir(figd); end
tev = base.t_ev;
% sizes: slides in px (96 dpi), report in inches -> px
if rep
    sz = struct('ref', [7.16 3.5], 'carga', [7.16 3.5], 'bode', [3.5 3.3], 'planta', [3.5 3.1], ...
                'cero', [3.5 2.4], 'rizado', [3.5 2.3], 'robustez', [7.16 2.5], 'dvsd', [3.5 2.8]);
    sz = structfun(@(v) v*96, sz, 'UniformOutput', false);
else
    sz = struct('ref', [1120 760], 'carga', [1120 760], 'bode', [1000 760], 'planta', [960 720], ...
                'cero', [900 560], 'rizado', [820 520], 'robustez', [1120 570], 'dvsd', [900 640]);
end
lgfs = S.fs - 2 + rep;     % legend font

%% Reference steps
f = newfig(sz.ref, S);
tl = tiledlayout(f, 2, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
cases = {'up', '6 V \rightarrow 7 V'; 'down', '6 V \rightarrow 5 V'};
for c = 1:2
    tr = sims.(cases{c, 1}); r = res.sim.(cases{c, 1});
    ax = nexttile(tl, c); hold(ax, 'on'); sty(ax, S);
    vf = tr.sc.ref1; dV = vf - tr.sc.ref0;
    plot(ax, (tr.sw.raw(:, 1) - tev)*1e3, tr.sw.raw(:, 2), 'Color', S.raw, 'LineWidth', S.lw2/1.6);
    tp = (tr.sw.tp + p.Ts/2 - tev)*1e3;
    plot(ax, tp, tr.sw.vavg, 'Color', S.teal, 'LineWidth', S.lw);
    plot(ax, tp, tr.avg.vavg, '--', 'Color', S.orange, 'LineWidth', S.lw);
    plot(ax, tp, tr.lin.vavg, ':', 'Color', S.ink, 'LineWidth', S.lw);
    stairs(ax, (tr.sw.tp - tev)*1e3, tr.sw.ref, '-', 'Color', S.gray, 'LineWidth', S.lw2/1.6);
    xlim(ax, [-1 9]);
    if dV > 0, ylim(ax, [5.85 7.15]); else, ylim(ax, [4.85 6.15]); end
    title(ax, cases{c, 2}, 'FontWeight', 'bold', 'Color', S.ink);
    xline(ax, r.sw.ts*1e3, '-', sprintf('t_s = %.1f ms', r.sw.ts*1e3), 'Color', S.ink, ...
          'LineWidth', S.lw2/1.6, 'FontSize', S.fs - 1, 'LabelOrientation', 'horizontal', ...
          'LabelVerticalAlignment', 'middle', 'LabelHorizontalAlignment', 'right', ...
          'FontName', S.font, 'HandleVisibility', 'off');
    if c == 1
        ylabel(ax, 'v_o (V)');
        lg = legend(ax, {'Conmutado (instantáneo)', 'Conmutado (prom. T_s)', 'Promediado', ...
                         'Lineal (diseño)', 'Referencia'}, 'Orientation', 'horizontal', ...
                    'NumColumns', 5, 'FontSize', lgfs, 'Box', 'off', 'TextColor', S.ink);
        lg.Layout.Tile = 'north';
    end
    ax = nexttile(tl, c + 2); hold(ax, 'on'); sty(ax, S);
    stairs(ax, (tr.sw.tp - tev)*1e3, tr.sw.d, 'Color', S.teal, 'LineWidth', S.lw);
    stairs(ax, (tr.avg.tp - tev)*1e3, tr.avg.d, '--', 'Color', S.orange, 'LineWidth', S.lw2);
    xlim(ax, [-1 9]); ylim(ax, [0.45 0.75]);
    xlabel(ax, 't - t_{escalón} (ms)');
    if c == 1, ylabel(ax, 'd'); end
end
save_fig(f, figd, 'fig_ref', rep);

%% Load steps (closed vs open loop)
f = newfig(sz.carga, S);
tl = tiledlayout(f, 2, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
cases = {'Rp', 'R: 6 \rightarrow 7.2 \Omega  (+20 %)'; 'Rm', 'R: 6 \rightarrow 4.8 \Omega  (-20 %)'};
for c = 1:2
    tr = sims.(cases{c, 1}); r = res.sim.(cases{c, 1});
    ax = nexttile(tl, c); hold(ax, 'on'); sty(ax, S);
    patch(ax, [-1 -1 9 9], 6 + 0.02*[-1 1 1 -1], S.orange, 'FaceAlpha', 0.15, 'EdgeColor', 'none', ...
          'HandleVisibility', 'off');
    plot(ax, (tr.sw.raw(:, 1) - tev)*1e3, tr.sw.raw(:, 2), 'Color', S.raw, 'LineWidth', S.lw2/1.6);
    tp = (tr.sw.tp + p.Ts/2 - tev)*1e3;
    plot(ax, tp, tr.ol_sw.vavg, '--', 'Color', S.gray, 'LineWidth', S.lw);
    plot(ax, tp, tr.sw.vavg, 'Color', S.teal, 'LineWidth', S.lw);
    plot(ax, tp, tr.avg.vavg, '--', 'Color', S.orange, 'LineWidth', S.lw);
    xlim(ax, [-1 9]);
    if c == 1, ylim(ax, [5.6 6.8]); else, ylim(ax, [5.2 6.4]); end
    title(ax, cases{c, 2}, 'FontWeight', 'bold', 'Color', S.ink);
    text(ax, 8.8, r.ol_sw.vf + 0.07*sign(r.ol_sw.vf - 6), sprintf('lazo abierto: %.2f V', r.ol_sw.vf), ...
         'HorizontalAlignment', 'right', 'FontSize', S.fs - 1, 'Color', S.gray, 'FontName', S.font);
    if c == 1
        ylabel(ax, 'v_o (V)');
        lg = legend(ax, {'Conmutado (instantáneo)', 'Lazo abierto (d fijo)', 'PI: conmutado (prom. T_s)', ...
                         'PI: promediado'}, 'Orientation', 'horizontal', 'NumColumns', 4, ...
                    'FontSize', lgfs, 'Box', 'off', 'TextColor', S.ink);
        lg.Layout.Tile = 'north';
    end
    ax = nexttile(tl, c + 2); hold(ax, 'on'); sty(ax, S);
    stairs(ax, (tr.sw.tp - tev)*1e3, tr.sw.d, 'Color', S.teal, 'LineWidth', S.lw);
    stairs(ax, (tr.ol_sw.tp - tev)*1e3, tr.ol_sw.d, '--', 'Color', S.gray, 'LineWidth', S.lw2);
    xlim(ax, [-1 9]); ylim(ax, [0.55 0.66]);
    xlabel(ax, 't - t_{escalón} (ms)');
    if c == 1, ylabel(ax, 'd'); end
end
save_fig(f, figd, 'fig_carga', rep);

%% Loop Bode (exact sampled-data loop) with the tolerance envelope
f = newfig(sz.bode, S);
tl = tiledlayout(f, 2, 1, 'TileSpacing', 'compact', 'Padding', 'compact');
wN = pi/p.Ts;
md = res.margins.disc;
w = L.w; Ld = L.Ld; wq = L.wq;
ax = nexttile(tl); hold(ax, 'on'); sty(ax, S); set(ax, 'XScale', 'log');
mg = 20*log10(L.Lmag);
patch(ax, [wq; flipud(wq)], [min(mg, [], 2); flipud(max(mg, [], 2))], S.teal, ...
      'FaceAlpha', 0.2, 'EdgeColor', 'none');
plot(ax, w, 20*log10(abs(Ld)), 'Color', S.teal, 'LineWidth', S.lw);
yline(ax, 0, '-', 'Color', S.gray, 'LineWidth', S.lw2/1.6, 'HandleVisibility', 'off');
bar_log(ax, md.w180, -md.GM, 0, S.orange);
text(ax, md.w180*1.12, -md.GM/2, sprintf('MG = %.1f dB', md.GM), 'Color', S.orange, ...
     'FontSize', S.fs, 'FontWeight', 'bold', 'FontName', S.font);
plot(ax, md.wc, 0, 'o', 'MarkerSize', S.ms, 'MarkerFaceColor', S.ink, 'MarkerEdgeColor', S.ink, ...
     'HandleVisibility', 'off');
text(ax, md.wc*1.15, 7, sprintf('\\omega_c = %.0f rad/s', md.wc), 'Color', S.ink, 'FontSize', S.fs, ...
     'FontName', S.font);
xlim(ax, [10 wN]); ylim(ax, [-60 60]);
ylabel(ax, '|L(e^{j\omegaT_s})| (dB)');
legend(ax, {sprintf('%d esquinas de tolerancia', res.corners.n), 'Nominal'}, 'Location', 'southwest', ...
       'FontSize', lgfs, 'Box', 'off', 'TextColor', S.ink);
ax = nexttile(tl); hold(ax, 'on'); sty(ax, S); set(ax, 'XScale', 'log');
phN = unwrap(angle(Ld))*180/pi; phN = phN - 360*ceil(phN(1)/360);
patch(ax, [wq; flipud(wq)], [min(L.Lph, [], 2); flipud(max(L.Lph, [], 2))], S.teal, ...
      'FaceAlpha', 0.2, 'EdgeColor', 'none', 'HandleVisibility', 'off');
plot(ax, w, phN, 'Color', S.teal, 'LineWidth', S.lw);
yline(ax, -180, '-', 'Color', S.gray, 'LineWidth', S.lw2/1.6);
bar_log(ax, md.wc, -180, -180 + md.PM, S.orange);
text(ax, md.wc*1.15, -180 + md.PM*0.45, sprintf('MF = %.0f°', md.PM), 'Color', S.orange, ...
     'FontSize', S.fs, 'FontWeight', 'bold', 'FontName', S.font);
xline(ax, res.plant.wn, ':', 'Color', S.gray, 'LineWidth', S.lw2);
text(ax, res.plant.wn*0.9, -95, '\omega_n', 'Color', S.gray, 'FontSize', S.fs, 'FontName', S.font, ...
     'HorizontalAlignment', 'right');
xlim(ax, [10 wN]); ylim(ax, [-300 -60]); yticks(ax, -270:45:-90);
xlabel(ax, '\omega (rad/s)'); ylabel(ax, 'Fase (°)');
save_fig(f, figd, 'fig_bode', rep);

%% Plant Bode used in the design (|G_vd H| and phase, crossover marked)
wc = res.design.wc_target;
wp = logspace(2, log10(wN*0.9999), 4000)';
[~, Gw] = e3_loop(wp, p, 1, 0, 'cont');
Gdl = Gw.*exp(-1.5*p.Ts*1j*wp);
[~, Gc] = e3_loop(wc, p, 1, 0, 'cont');
Gcd = Gc*exp(-1.5*p.Ts*1j*wc);
f = newfig(sz.planta, S);
tl = tiledlayout(f, 2, 1, 'TileSpacing', 'compact', 'Padding', 'compact');
ax = nexttile(tl); hold(ax, 'on'); sty(ax, S); set(ax, 'XScale', 'log');
plot(ax, wp, 20*log10(abs(Gw)), 'Color', S.teal, 'LineWidth', S.lw);
xline(ax, wc, '--', 'Color', S.orange, 'LineWidth', S.lw2, 'HandleVisibility', 'off');
xline(ax, res.plant.wn, ':', 'Color', S.gray, 'LineWidth', S.lw2, 'HandleVisibility', 'off');
plot(ax, wc, 20*log10(abs(Gc)), 'o', 'MarkerSize', S.ms, 'MarkerFaceColor', S.orange, 'MarkerEdgeColor', S.orange);
text(ax, wc*1.15, 20*log10(abs(Gc)) - 9, sprintf('%.1f dB en \\omega_c', 20*log10(abs(Gc))), ...
     'Color', S.ink, 'FontSize', S.fs, 'FontName', S.font);
text(ax, res.plant.wn*0.88, -22, '\omega_n', 'Color', S.gray, 'FontSize', S.fs, 'FontName', S.font, ...
     'HorizontalAlignment', 'right');
xlim(ax, [100 wN]); ylim(ax, [-30 30]);
ylabel(ax, '|G_{vd}H| (dB)');
title(ax, 'Planta + sensor (entrada d)', 'FontWeight', 'bold', 'Color', S.ink);
ax = nexttile(tl); hold(ax, 'on'); sty(ax, S); set(ax, 'XScale', 'log');
ph1 = unwrap(angle(Gw))*180/pi; ph2 = unwrap(angle(Gdl))*180/pi;
plot(ax, wp, ph1, 'Color', S.teal, 'LineWidth', S.lw);
plot(ax, wp, ph2, '--', 'Color', S.ink, 'LineWidth', S.lw);
xline(ax, wc, '--', 'Color', S.orange, 'LineWidth', S.lw2, 'HandleVisibility', 'off');
xline(ax, res.plant.wn, ':', 'Color', S.gray, 'LineWidth', S.lw2, 'HandleVisibility', 'off');
plot(ax, wc, angle(Gcd)*180/pi, 'o', 'MarkerSize', S.ms, 'MarkerFaceColor', S.orange, ...
     'MarkerEdgeColor', S.orange, 'HandleVisibility', 'off');
text(ax, wc*1.15, angle(Gcd)*180/pi - 30, sprintf('%.0f° en \\omega_c', angle(Gcd)*180/pi), ...
     'Color', S.ink, 'FontSize', S.fs, 'FontName', S.font);
xlim(ax, [100 wN]); ylim(ax, [-360 20]); yticks(ax, -360:90:0);
xlabel(ax, '\omega (rad/s)'); ylabel(ax, 'Fase (°)');
legend(ax, {'G_{vd}H', 'con retardo 1.5 T_s'}, 'Location', 'southwest', 'FontSize', lgfs, ...
       'Box', 'off', 'TextColor', S.ink);
save_fig(f, figd, 'fig_planta', rep);

%% Why the PI zero goes above crossover
f = newfig(sz.cero, S);
ax = axes(f); hold(ax, 'on'); sty(ax, S); set(ax, 'XScale', 'log');
[~, Gw2] = e3_loop(w, p, 1, 0, 'cont');
plot(ax, w, 20*log10(abs(Gw2)), ':', 'Color', S.gray, 'LineWidth', S.lw);
plot(ax, w, 20*log10(abs(L.Lalt)), '--', 'Color', S.orange, 'LineWidth', S.lw);
plot(ax, w, 20*log10(abs(Ld)), '-', 'Color', S.teal, 'LineWidth', S.lw);
yline(ax, 0, '-', 'Color', S.ink, 'LineWidth', S.lw2/1.6, 'HandleVisibility', 'off');
xline(ax, res.plant.wn, ':', 'Color', S.gray, 'LineWidth', S.lw2, 'HandleVisibility', 'off');
xlim(ax, [100 wN]); ylim(ax, [-40 40]);
xlabel(ax, '\omega (rad/s)'); ylabel(ax, 'Magnitud (dB)');
legend(ax, {'Planta + sensor  G_{vd}H', ...
            sprintf('L con \\omega_z = \\omega_c/5:  MG = %.1f dB', res.alt.GM), ...
            sprintf('L con \\omega_z = 3\\omega_c:  MG = %.1f dB', res.margins.disc.GM)}, ...
       'Location', 'southwest', 'FontSize', lgfs, 'Box', 'off', 'TextColor', S.ink);
save_fig(f, figd, 'fig_cero', rep);

%% d versus d' (same magnitude, phase shifted 180 deg)
f = newfig(sz.dvsd, S);
tl = tiledlayout(f, 2, 1, 'TileSpacing', 'compact', 'Padding', 'compact');
[A, B, ~, G] = e3_plant(p); %#ok<ASGLU>
Gv = G.num./((1j*wp).^2 + G.den(2)*1j*wp + G.den(3));
ax = nexttile(tl); hold(ax, 'on'); sty(ax, S); set(ax, 'XScale', 'log');
plot(ax, wp, 20*log10(abs(Gv)), 'Color', S.teal, 'LineWidth', 2*S.lw);
plot(ax, wp, 20*log10(abs(-Gv)), '--', 'Color', S.orange, 'LineWidth', S.lw);
xlim(ax, [100 wN]); ylim(ax, [-30 30]);
ylabel(ax, 'Magnitud (dB)');
legend(ax, {'G_{vd}: entrada d (placa Rev C)', 'G_{vd''} = -G_{vd}: entrada d'' = 1 - d'}, ...
       'Location', 'southwest', 'FontSize', lgfs, 'Box', 'off', 'TextColor', S.ink);
ax = nexttile(tl); hold(ax, 'on'); sty(ax, S); set(ax, 'XScale', 'log');
phd = unwrap(angle(Gv))*180/pi;
plot(ax, wp, phd, 'Color', S.teal, 'LineWidth', S.lw);
plot(ax, wp, phd + 180, '--', 'Color', S.orange, 'LineWidth', S.lw);
xlim(ax, [100 wN]); ylim(ax, [-200 200]); yticks(ax, -180:90:180);
xlabel(ax, '\omega (rad/s)'); ylabel(ax, 'Fase (°)');
save_fig(f, figd, 'fig_dvsd', rep);

%% Steady-state ripple and ADC samples (switched model, 6 ohm, 20 kHz)
f = newfig(sz.rizado, S);
ax = axes(f); hold(ax, 'on'); sty(ax, S);
raw = sims.up.sw.raw;
t0 = tev - 4*p.Ts;
k = raw(:, 1) >= t0 & raw(:, 1) <= tev;
tt = (raw(k, 1) - t0)*1e6;
plot(ax, tt, raw(k, 2), 'Color', S.teal, 'LineWidth', S.lw);
plot(ax, tt, raw(k, 4), 'Color', S.orange, 'LineWidth', S.lw);
ns = round(t0/p.Ts):round(tev/p.Ts) - 1;
plot(ax, (ns*p.Ts - t0)*1e6 + 1e-3, sims.up.sw.y(ns + 1), 'o', 'MarkerSize', S.ms + 1, ...
     'MarkerFaceColor', S.ink, 'MarkerEdgeColor', S.ink);
xlim(ax, [0 200]); ylim(ax, [5.94 6.06]);
xlabel(ax, 't (\mus)'); ylabel(ax, 'V');
legend(ax, {sprintf('v_o  (%.0f mV p-p)', 1e3*res.ripple.dvo_pp), ...
            sprintf('v_m tras el filtro RC  (%.0f mV p-p)', 1e3*res.ripple.dvm_pp), ...
            'Muestras del ADC (una por periodo)'}, 'Location', 'northoutside', ...
       'FontSize', lgfs, 'Box', 'off', 'TextColor', S.ink);
save_fig(f, figd, 'fig_rizado', rep);

%% Robustness: averaged model over 36 corners (L, C, rL, Vin)
f = newfig(sz.robustez, S);
tl = tiledlayout(f, 1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
tp = ((0:numel(rob(1).up.v) - 1)'*p.Ts + p.Ts/2 - tev)*1e3;
panels = {'up', 'Referencia 6 V \rightarrow 7 V', [5.85 7.15], 7, 6; ...
          'Rm', 'Carga -20 %  (6 \rightarrow 4.8 \Omega)', [5.15 6.25], 6, 4.8};
for c = 1:2
    ax = nexttile(tl); hold(ax, 'on'); sty(ax, S);
    for i = 1:numel(rob)
        plot(ax, tp, rob(i).(panels{c, 1}).v, 'Color', [S.teal 0.35], 'LineWidth', S.lw2*0.75);
    end
    sc = base; sc.ref1 = panels{c, 4}; sc.R1 = panels{c, 5};
    pn = e3_sim(p, L.Kp, L.Ki, sc, 'avg');
    plot(ax, tp, pn.vavg, 'Color', S.ink, 'LineWidth', S.lw);
    xlim(ax, [-1 9]); ylim(ax, panels{c, 3});
    title(ax, panels{c, 2}, 'FontWeight', 'bold', 'Color', S.ink);
    xlabel(ax, 't - t_{escalón} (ms)');
    if c == 1, ylabel(ax, 'v_o promedio (V)'); end
end
save_fig(f, figd, 'fig_robustez', rep);

if rep, disp('report figures done'); return; end

%% Circuit (power stage, sensor, NUCLEO and driver) - slides only
fig_circuit(S, figd);

%% Equations (LaTeX rendered by MATLAB, transparent PNG) - slides only
Gp = res.plant;
eq = { ...
 'eq_gvd',   {'$\displaystyle G_{vd}(s)=\frac{\tilde{v}_o(s)}{\tilde{d}(s)}=\frac{V_{in}+V_F}{LC\,s^{2}+\left(\frac{L}{R}+r_L C\right)s+1+\frac{r_L}{R}}$'};
 'eq_num',   {sprintf('$\\displaystyle G_{vd}(s)=\\frac{%.3f\\times10^{8}}{s^{2}+%s\\,s+%.3f\\times10^{7}}$', ...
              Gp.num/1e8, strrep(sprintf('%.0f', Gp.den(2)), '10', '10\,'), Gp.den(3)/1e7)};
 'eq_op',    {'$\displaystyle D=\frac{V_o\,(1+r_L/R)+V_F}{V_{in}+V_F}=0.613$'};
 'eq_vals',  {sprintf('$\\omega_n = %.0f\\ \\mathrm{rad/s}$', Gp.wn), sprintf('$\\zeta = %.3f$', Gp.zeta), ...
              sprintf('$K_0 = %.2f\\ \\mathrm{V}$', Gp.K0), sprintf('$p_{1,2} = %.0f \\pm j%.0f$', Gp.poles_re, Gp.poles_im), ...
              sprintf('$\\Delta i_{L,pp} = %.2f\\ \\mathrm{A}$', res.ccm.diL)};
 'eq_dvsd',  {'$\displaystyle d'' = 1 - d \;\Rightarrow\; \tilde{d}'' = -\tilde{d}$', ...
              '$\displaystyle G_{vd''}(s)=\frac{\tilde{v}_o}{\tilde{d}''}=-\,G_{vd}(s)$'};
 'eq_pi',    {'$\displaystyle C(s)=K_p+\frac{K_i}{s}=K_p\,\frac{s+\omega_z}{s}$'};
 'eq_gains', {sprintf('$K_p = %.4f\\ \\mathrm{V^{-1}}$', L.Kp), sprintf('$K_i = %.1f\\ \\mathrm{V^{-1}s^{-1}}$', L.Ki)};
 'eq_law',   {'$e[k]=v_{ref}-v_m[k]$', '$I[k]=I[k-1]+K_i T_s\,e[k]$', ...
              '$d[k+1]=\mathrm{sat}_{[0,\;0.85]}\left(K_p\,e[k]+I[k]\right)$'};
 'eq_loop',  {'$\displaystyle L(s)\approx C(s)\,G_{vd}(s)\,\frac{1}{1+\tau s}\,e^{-1.5\,T_s s}$'}};
for i = 1:size(eq, 1)
    fig_eq(eq{i, 2}, fullfile(figd, [eq{i, 1} '.png']), S);
end
disp('slide figures done');
end

%% ------------------------------------------------------------------------
function f = newfig(sz, S)
f = figure('Visible', 'off', 'Units', 'inches', 'Position', [0.5 0.5 sz(1)/96 sz(2)/96], ...
           'Color', S.paper, 'PaperPositionMode', 'auto');
try, theme(f, 'light'); catch, end
end

function sty(ax, S)
set(ax, 'FontName', S.font, 'FontSize', S.fs, 'Color', S.axbg, ...
    'XColor', S.body, 'YColor', S.body, 'GridColor', S.grid, 'GridAlpha', 1, ...
    'MinorGridColor', S.grid, 'MinorGridAlpha', 0.6, 'LineWidth', 0.5 + 0.5*strcmp(S.mode, 'slides'), ...
    'Box', 'on', 'TickDir', 'out');
grid(ax, 'on');
ax.Title.FontSize = S.fs + 1;
end

function bar_log(ax, x, y1, y2, col)
patch(ax, x*[0.975 1.025 1.025 0.975], [y1 y1 y2 y2], col, 'EdgeColor', 'none', ...
      'HandleVisibility', 'off');
end

function save_fig(f, figd, name, rep)
if rep
    exportgraphics(f, fullfile(figd, [name '.pdf']), 'ContentType', 'vector', 'BackgroundColor', 'none');
else
    exportgraphics(f, fullfile(figd, [name '.png']), 'Resolution', 192, 'BackgroundColor', 'current');
end
close(f);
end

function fig_eq(lines, file, S)
f = figure('Visible', 'off', 'Units', 'inches', 'Position', [0.5 0.5 12 4], 'Color', [1 1 1]);
try, theme(f, 'light'); catch, end
ax = axes(f, 'Position', [0 0 1 1], 'Visible', 'off'); xlim(ax, [0 1]); ylim(ax, [0 1]);
text(ax, 0.5, 0.5, lines, 'Interpreter', 'latex', 'FontSize', 30, 'Color', [0 0 0], ...
     'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle');
exportgraphics(f, file, 'Resolution', 192, 'BackgroundColor', 'current');
close(f);
% black text on white -> black with alpha (transparent background)
im = im2double(imread(file));
a = 1 - mean(im, 3);
imwrite(zeros(size(im)), file, 'Alpha', a);
end

function fig_circuit(S, figd)
f = figure('Visible', 'off', 'Units', 'inches', 'Position', [0.5 0.5 1100/96 540/96], 'Color', S.paper);
try, theme(f, 'light'); catch, end
ax = axes(f, 'Position', [0 0 1 1]); hold(ax, 'on'); axis(ax, 'off');
xlim(ax, [-12 116]); ylim(ax, [-9 54]); daspect(ax, [1 1 1]);
c = S.ink; lw = 2;
box = 0.88*[1 1 1] + 0.12*S.teal;
W = @(x, y) plot(ax, x, y, '-', 'Color', c, 'LineWidth', lw);
T = @(x, y, s, ha, va) text(ax, x, y, s, 'Interpreter', 'latex', 'FontSize', 17, 'Color', c, ...
                            'HorizontalAlignment', ha, 'VerticalAlignment', va);
yT = 44; yG = 12;
src(ax, 8, 28, 3.5, c, lw); W([8 8], [31.5 yT]); W([8 8], [24.5 yG]); gnd(ax, 8, yG, c, lw);
T(3.5, 28, '$V_{in}=12\,\mathrm{V}$', 'right', 'middle');
W([8 18.5], [yT yT]); W([18.5 18.5], [yT 42]);
W([18 19.6], [42 42]); W([20.2 21.8], [42 42]); W([22.4 24], [42 42]);
W([23.5 23.5], [42 yT]); W([21 21], [42 43.2]);
fill(ax, [21 20.3 21.7], [42.1 43 43], c, 'EdgeColor', c);
W([18 24], [40.8 40.8]); W([21 21], [40.8 33]);
W([23.5 34], [yT yT]);
T(21, 46.4, '$Q_1$ AOD4184A', 'center', 'bottom');
rectangle(ax, 'Position', [13.5 21 15 12], 'Curvature', 0.15, 'EdgeColor', S.teal, 'LineWidth', lw, ...
          'FaceColor', box);
T(21, 27, {'\textbf{Driver}', 'bootstrap', 'no inversor'}, 'center', 'middle');
plot(ax, 34, yT, 'o', 'MarkerSize', 6, 'MarkerFaceColor', c, 'MarkerEdgeColor', c);
T(33.4, 41.8, '$sw$', 'right', 'top');
W([34 34], [yT 29.6]); W([34 34], [26.4 yG]); gnd(ax, 34, yG, c, lw);
fill(ax, [31.8 36.2 34], [26.4 26.4 29.6], [1 1 1], 'EdgeColor', c, 'LineWidth', lw);
W([31.8 36.2], [29.6 29.6]);
T(37.2, 28, {'$D_1$', 'SS34'}, 'left', 'middle');
W([34 38], [yT yT]);
th = linspace(pi, 0, 30);
for b = 0:3
    plot(ax, 39.5 + 3*b + 1.5*cos(th), yT + 1.5*sin(th), 'Color', c, 'LineWidth', lw);
end
W([50 52], [yT yT]);
zig(ax, 52, 60, yT, c, lw);
W([60 64], [yT yT]);
T(44.5, 46.6, '$L=2\times330\,\mu\mathrm{H}$', 'center', 'bottom');
T(56, 46.6, '$r_L\le1.2\,\Omega$', 'left', 'bottom');
plot(ax, 64, yT, 'o', 'MarkerSize', 6, 'MarkerFaceColor', c, 'MarkerEdgeColor', c);
T(64.8, 41.6, '$v_o$', 'left', 'top');
W([64 64], [yT 29]); W([61 67], [29 29]); W([61 67], [27.4 27.4]); W([64 64], [27.4 yG]); gnd(ax, 64, yG, c, lw);
T(60.3, 28.2, '$C=2\times10\,\mu\mathrm{F}$', 'right', 'middle');
W([64 94], [yT yT]);
plot(ax, 78, yT, 'o', 'MarkerSize', 6, 'MarkerFaceColor', c, 'MarkerEdgeColor', c);
W([78 78], [yT 33]); zigv(ax, 78, 33, 23, c, lw); W([78 78], [23 yG]); gnd(ax, 78, yG, c, lw);
T(80.2, 28, {'$R=6\,\Omega$', '$\pm20\%$'}, 'left', 'middle');
W([94 94], [yT 41]); zigv(ax, 94, 41, 33, c, lw); W([94 94], [33 27]);
plot(ax, 94, 27, 'o', 'MarkerSize', 6, 'MarkerFaceColor', c, 'MarkerEdgeColor', c);
W([94 94], [27 24]); zigv(ax, 94, 24, 16, c, lw); W([94 94], [16 yG]); gnd(ax, 94, yG, c, lw);
T(92, 37, '$30\,\mathrm{k}\Omega$', 'right', 'middle');
T(92, 20, '$10\,\mathrm{k}\Omega$', 'right', 'middle');
W([94 104], [27 27]); W([104 104], [27 21]); W([101 107], [21 21]); W([101 107], [19.4 19.4]);
W([104 104], [19.4 yG]); gnd(ax, 104, yG, c, lw);
T(102.6, 15.2, '$4.7\,\mathrm{nF}$', 'right', 'middle');
plot(ax, 104, 27, 'o', 'MarkerSize', 6, 'MarkerFaceColor', c, 'MarkerEdgeColor', c);
W([104 110], [27 27]); W([110 110], [27 -2]); W([110 101.2], [-2 -2]);
fill(ax, [100.2 102 102], [-2 -2.9 -1.1], c, 'EdgeColor', c);
T(106, 28.4, '$v_m$', 'center', 'bottom');
T(105.5, -1.2, 'PA1', 'center', 'bottom');
rectangle(ax, 'Position', [13.5 -7.5 86.7 11], 'Curvature', 0.1, 'EdgeColor', S.teal, ...
          'LineWidth', lw, 'FaceColor', box);
T(56.8, -2, '\textbf{NUCLEO-L432KC}: ADC 12 bits $\rightarrow$ PI digital $\rightarrow$ PWM 20 kHz', 'center', 'middle');
W([21 21], [3.5 21]); fill(ax, [21 20.1 21.9], [21 19.3 19.3], c, 'EdgeColor', c);
T(19.8, 12, 'PWM $d$', 'right', 'middle');
exportgraphics(f, fullfile(figd, 'fig_circuito.png'), 'Resolution', 192, 'BackgroundColor', 'current');
close(f);
end

function src(ax, x, y, r, c, lw)
th = linspace(0, 2*pi, 80);
plot(ax, x + r*cos(th), y + r*sin(th), 'Color', c, 'LineWidth', lw);
text(ax, x, y + 1.4, '$+$', 'Interpreter', 'latex', 'FontSize', 15, 'Color', c, 'HorizontalAlignment', 'center');
text(ax, x, y - 1.5, '$-$', 'Interpreter', 'latex', 'FontSize', 15, 'Color', c, 'HorizontalAlignment', 'center');
end

function gnd(ax, x, y, c, lw)
plot(ax, [x x], [y y - 1], 'Color', c, 'LineWidth', lw);
plot(ax, x + [-2 2], [y y] - 1, 'Color', c, 'LineWidth', lw);
plot(ax, x + [-1.3 1.3], [y y] - 1.8, 'Color', c, 'LineWidth', lw);
plot(ax, x + [-0.6 0.6], [y y] - 2.6, 'Color', c, 'LineWidth', lw);
end

function zig(ax, x1, x2, y, c, lw)
n = 6; xs = linspace(x1, x2, 2*n + 1);
ys = y + [0, repmat([1.1 -1.1], 1, n - 1), 1.1, 0];
ys = ys(1:numel(xs)); ys(end) = y;
plot(ax, xs, ys, 'Color', c, 'LineWidth', lw);
end

function zigv(ax, x, y1, y2, c, lw)
n = 6; ys = linspace(y1, y2, 2*n + 1);
xs = x + [0, repmat([1.1 -1.1], 1, n - 1), 1.1, 0];
xs = xs(1:numel(ys)); xs(end) = x;
plot(ax, xs, ys, 'Color', c, 'LineWidth', lw);
end
