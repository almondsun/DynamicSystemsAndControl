%E3_MAIN  Entrega 3: PI design for the Rev C buck and its validation in simulation.
%   Plain MATLAB (no toolboxes). Writes ../results/e3_results.json (all the
%   numbers used in the slides and the report) and ../results/e3_sims.mat
%   (traces for e3_figures.m).
here = fileparts(mfilename('fullpath'));
outd = fullfile(here, '..', 'results');
if ~exist(outd, 'dir'), mkdir(outd); end
addpath(here);

%% 1. Plant
p = e3_params();
[A, B, Cm, G] = e3_plant(p);
[~, ~, ~, GE1] = e3_plant(e3_params('rL', 0, 'Vf', 0));   % Entrega 1 ideal model
res.params = rmfield(p, {});
res.plant = struct('num', G.num, 'den', G.den, 'wn', G.wn, 'zeta', G.zeta, 'K0', G.K0, ...
    'poles_re', real(G.poles(1)), 'poles_im', abs(imag(G.poles(1))), 'D0', p.D0, ...
    'wn_E1', GE1.wn, 'zeta_E1', GE1.zeta, 'K0_E1', GE1.K0);
for Cx = [14e-6 22e-6]
    [~, ~, ~, Gx] = e3_plant(e3_params('C', Cx));
    res.plant.(sprintf('wn_C%d', round(Cx*1e6)))   = Gx.wn;
    res.plant.(sprintf('zeta_C%d', round(Cx*1e6))) = Gx.zeta;
end
% CCM and ripple (ideal-ripple formulas at the operating point)
vL_on = p.Vin - p.rL*p.Vo/p.R - p.Vo;
res.ccm.diL  = vL_on*p.D0*p.Ts/p.L;
res.ccm.iLmin = p.Vo/p.R - res.ccm.diL/2;
res.ccm.dvo   = res.ccm.diL/(8*p.C*p.fs);
res.ccm.dvo14 = res.ccm.diL/(8*14e-6*p.fs);

%% 2. Design: PI by frequency response
wc = 1000;           % rad/s, ~ wn/10: away from the LC resonance and the delay
wz = 3*wc;           % PI zero above crossover (see section 3)
[Kp, Ki] = e3_design(p, wc, wz);
res.design = struct('wc_target', wc, 'wz', wz, 'Kp', Kp, 'Ki', Ki, 'KiTs', Ki*p.Ts, ...
    'delay_us', 1.5*p.Ts*1e6);
w  = logspace(1, log10(pi/p.Ts*0.9999), 20000)';
Ld = e3_loop(w, p, Kp, Ki, 'disc');  mD = e3_margins(w, Ld);
Lc = e3_loop(w, p, Kp, Ki, 'cont');  mC = e3_margins(w, Lc);
res.margins.disc = mD;
res.margins.cont = mC;
% phase budget at crossover (continuous approximation)
s = 1j*mD.wc;
res.design.phase_plant = angle(G.num/(s^2 + G.den(2)*s + G.den(3)))*180/pi;
res.design.phase_rc    = -atan(mD.wc*p.tau)*180/pi;
res.design.phase_delay = -1.5*p.Ts*mD.wc*180/pi;
res.design.phase_pi    = angle(Kp + Ki/s)*180/pi;

%% 3. Why the zero goes above crossover: classic PI (wz = wc/5) for comparison
[Kp5, Ki5] = e3_design(p, wc, wc/5);
mA = e3_margins(w, e3_loop(w, p, Kp5, Ki5, 'disc'));
res.alt = struct('wz', wc/5, 'Kp', Kp5, 'Ki', Ki5, 'wc', mA.wc, 'PM', mA.PM, 'GM', mA.GM);
Lalt = e3_loop(w, p, Kp5, Ki5, 'disc');

%% 4. Tolerance corners (108): margins
P  = e3_corners(p);
wq = logspace(1, log10(pi/p.Ts*0.9999), 6000)';
mq = cell(numel(P), 1);
Lmag = zeros(numel(wq), numel(P)); Lph = Lmag;
for i = 1:numel(P)
    Lq = e3_loop(wq, P(i), Kp, Ki, 'disc');
    mq{i} = e3_margins(wq, Lq);
    Lmag(:, i) = abs(Lq);
    ph = unwrap(angle(Lq))*180/pi;
    Lph(:, i) = ph - 360*ceil(ph(1)/360);
end
mq = [mq{:}];
[~, iw] = min([mq.GM]);
res.corners = struct('n', numel(P), 'PMmin', min([mq.PM]), 'PMmax', max([mq.PM]), ...
    'GMmin', min([mq.GM]), 'GMmax', max([mq.GM]), 'wcmin', min([mq.wc]), 'wcmax', max([mq.wc]), ...
    'worst', struct('L', P(iw).L, 'C', P(iw).C, 'R', P(iw).R, 'rL', P(iw).rL, 'Vin', P(iw).Vin));

%% 5. Same PI at 10 kHz (the guide's reference frequency), for comparison
p10 = e3_params('fs', 10e3);
w10 = logspace(1, log10(pi/p10.Ts*0.9999), 6000)';
m10 = e3_margins(w10, e3_loop(w10, p10, Kp, Ki, 'disc'));
P10 = e3_corners(p10);
g10 = arrayfun(@(q) e3_margins(w10, e3_loop(w10, q, Kp, Ki, 'disc')), P10, 'UniformOutput', false);
g10 = [g10{:}];
res.fs10 = struct('PM', m10.PM, 'GM', m10.GM, 'wc', m10.wc, 'GMmin', min([g10.GM]), 'PMmin', min([g10.PM]));

%% 6. Closed-loop poles of the sampled-data loop
[Ad, Bd] = e3_zoh(A, B, p.Ts);
k1 = Kp + Ki*p.Ts; k2 = Ki*p.Ts;
Acl = [Ad, Bd, zeros(3, 1); -k1*Cm, 0, 1; -k2*Cm, 0, 1];
zc = eig(Acl);
sc_ = log(zc)/p.Ts;
[~, io] = sort(abs(sc_));
res.clpoles = struct('z_abs', abs(zc(io)).', 's_re', real(sc_(io)).', 's_im', imag(sc_(io)).');

%% 7. Time-domain validation (averaged, switched, linear; open loop for the loads)
base = struct('t_end', 0.030, 't_ev', 0.015, 'ref0', 6, 'ref1', 6, 'R0', 6, 'R1', 6, ...
              'closed', true, 'd_ol', p.D0, 'm', 12);
scn = {'up', 7, 6; 'down', 5, 6; 'Rp', 6, 7.2; 'Rm', 6, 4.8};
nev = round(base.t_ev/p.Ts); N = round(base.t_end/p.Ts);
sims = struct();
for i = 1:size(scn, 1)
    sc = base; sc.ref1 = scn{i, 2}; sc.R1 = scn{i, 3};
    oS = e3_sim(p, Kp, Ki, sc, 'sw');
    oA = e3_sim(p, Kp, Ki, sc, 'avg');
    r.sw  = e3_metrics(oS, sc);
    r.avg = e3_metrics(oA, sc);
    tr = struct('sw', oS, 'avg', oA, 'sc', sc);
    if sc.ref1 ~= sc.ref0
        oL = e3_linsim(p, Kp, Ki, sc.ref1 - sc.ref0, N, nev);
        oL.vavg = oL.vavg + sc.ref0;
        oL.d = oL.d + p.D0;
        r.lin = e3_metrics(oL, sc);
        tr.lin = oL;
    else
        % open loop with the duty the closed loop had before the event
        so = sc; so.closed = false;
        so.d_ol = mean(oS.d(nev-40:nev-1));
        oOS = e3_sim(p, 0, 0, so, 'sw');
        so.d_ol = mean(oA.d(nev-40:nev-1));
        oOA = e3_sim(p, 0, 0, so, 'avg');
        r.ol_sw  = e3_metrics(oOS, so);
        r.ol_avg = e3_metrics(oOA, so);
        tr.ol_sw = oOS; tr.ol_avg = oOA;
    end
    res.sim.(scn{i, 1}) = r;
    sims.(scn{i, 1}) = tr;
    clear r
end
% steady-state ripple, ADC-sampling bias and minimum inductor current (switched)
raw = sims.up.sw.raw;
win = raw(:, 1) > base.t_ev - 2e-3 & raw(:, 1) < base.t_ev;
res.ripple = struct('dvo_pp', max(raw(win, 2)) - min(raw(win, 2)), ...
    'vo_mean', mean(raw(win, 2)), 'diL_pp', max(raw(win, 3)) - min(raw(win, 3)), ...
    'dvm_pp', max(raw(win, 4)) - min(raw(win, 4)));
iLmin = inf;
for f = fieldnames(sims)'
    iLmin = min(iLmin, min(sims.(f{1}).sw.raw(:, 3)));
end
res.ripple.iLmin_all = iLmin;
% ripple at 10 kHz and with C derated to 14 uF (steady state, 6 ohm)
for v = {{'fs10', e3_params('fs', 10e3)}, {'C14', e3_params('C', 14e-6)}}
    q = v{1}{2};
    s0 = base; s0.t_end = 0.012; s0.t_ev = 1;      % no event
    o = e3_sim(q, Kp, Ki, s0, 'sw');
    ww = o.raw(:, 1) > 0.010;
    res.ripple.(['dvo_pp_' v{1}{1}]) = max(o.raw(ww, 2)) - min(o.raw(ww, 2));
end

%% 8. Robustness in the time domain: averaged model over L, C, rL, Vin corners
Ls = p.L*[0.9 1 1.1]; Cs = [14 20 22]*1e-6; rLs = [0.9 1.2]; Vs = [11.5 12.5];
rob = struct('L', {}, 'C', {}, 'rL', {}, 'Vin', {}, 'up', {}, 'down', {}, 'Rp', {}, 'Rm', {});
k = 0;
for L = Ls, for C = Cs, for rL = rLs, for V = Vs %#ok<ALIGN>
    q = e3_params('L', L, 'C', C, 'rL', rL, 'Vin', V);
    k = k + 1;
    rob(k).L = L; rob(k).C = C; rob(k).rL = rL; rob(k).Vin = V;
    for i = 1:size(scn, 1)
        sc = base; sc.ref1 = scn{i, 2}; sc.R1 = scn{i, 3};
        o = e3_sim(q, Kp, Ki, sc, 'avg');
        rob(k).(scn{i, 1}) = struct('m', e3_metrics(o, sc), 'v', o.vavg, 'd', o.d);
    end
end, end, end, end
mm = @(f, g) arrayfun(@(x) x.(f).m.(g), rob);
res.robust = struct( ...
    'n', numel(rob), ...
    'ts_up', [min(mm('up', 'ts')), max(mm('up', 'ts'))], ...
    'ts_down', [min(mm('down', 'ts')), max(mm('down', 'ts'))], ...
    'Mp_up', [min(mm('up', 'Mp')), max(mm('up', 'Mp'))], ...
    'Mp_down', [min(mm('down', 'Mp')), max(mm('down', 'Mp'))], ...
    'pk_Rp', [min(mm('Rp', 'dVmax')), max(mm('Rp', 'dVmax'))], ...
    'pk_Rm', [min(mm('Rm', 'dVmax')), max(mm('Rm', 'dVmax'))], ...
    'ts20_Rp', [min(mm('Rp', 'ts20')), max(mm('Rp', 'ts20'))], ...
    'ts20_Rm', [min(mm('Rm', 'ts20')), max(mm('Rm', 'ts20'))], ...
    'dmax_all', max([mm('up', 'dmax'), mm('down', 'dmax'), mm('Rp', 'dmax'), mm('Rm', 'dmax')]), ...
    'dmin_all', min([mm('up', 'dmin'), mm('down', 'dmin'), mm('Rp', 'dmin'), mm('Rm', 'dmin')]), ...
    'ess_max', max(abs([mm('up', 'ess'), mm('down', 'ess'), mm('Rp', 'ess'), mm('Rm', 'ess')])));

%% 9. Save
fid = fopen(fullfile(outd, 'e3_results.json'), 'w');
fprintf(fid, '%s', jsonencode(res, 'PrettyPrint', true));
fclose(fid);
save(fullfile(outd, 'e3_sims.mat'), 'res', 'sims', 'rob', 'w', 'Ld', 'Lc', 'Lalt', 'wq', 'Lmag', 'Lph', ...
     'mq', 'p', 'Kp', 'Ki', 'Kp5', 'Ki5', 'base');
fprintf('Kp = %.6f  Ki = %.4f  KiTs = %.7f\n', Kp, Ki, Ki*p.Ts);
fprintf('disc: wc %.0f PM %.1f GM %.2f (w180 %.0f) | cont: wc %.0f PM %.1f GM %.2f\n', ...
    mD.wc, mD.PM, mD.GM, mD.w180, mC.wc, mC.PM, mC.GM);
fprintf('corners: PM %.1f..%.1f  GM %.2f..%.2f  wc %.0f..%.0f\n', res.corners.PMmin, res.corners.PMmax, ...
    res.corners.GMmin, res.corners.GMmax, res.corners.wcmin, res.corners.wcmax);
fprintf('alt wz=wc/5: wc %.0f PM %.1f GM %.2f\n', mA.wc, mA.PM, mA.GM);
fprintf('10 kHz: PM %.1f GM %.2f, worst GM %.2f PM %.1f\n', m10.PM, m10.GM, res.fs10.GMmin, res.fs10.PMmin);
for f = fieldnames(res.sim)'
    r = res.sim.(f{1});
    fprintf('%-5s sw: tr %.2f Mp %.2f ts %.2f ms ess %+.4f dV %+.3f trec %.2f ts20 %.2f d %.3f-%.3f | avg: ts %.2f Mp %.2f dV %+.3f ts20 %.2f\n', ...
        f{1}, r.sw.tr*1e3, r.sw.Mp, r.sw.ts*1e3, r.sw.ess, r.sw.dVmax, r.sw.trec*1e3, r.sw.ts20*1e3, ...
        r.sw.dmin, r.sw.dmax, r.avg.ts*1e3, r.avg.Mp, r.avg.dVmax, r.avg.ts20*1e3);
    if isfield(r, 'lin'), fprintf('      lin: tr %.2f Mp %.2f ts %.2f\n', r.lin.tr*1e3, r.lin.Mp, r.lin.ts*1e3); end
    if isfield(r, 'ol_sw'), fprintf('      open loop sw: peak %+.3f final %.3f | avg peak %+.3f final %.3f\n', ...
            r.ol_sw.dVmax, r.ol_sw.vf, r.ol_avg.dVmax, r.ol_avg.vf); end
end
disp(res.ripple); disp(res.robust); disp(res.clpoles);
