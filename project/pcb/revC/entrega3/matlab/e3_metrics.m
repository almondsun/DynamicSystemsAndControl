function m = e3_metrics(o, sc)
%E3_METRICS  Step metrics on the per-period average of vo (ripple removed).
%   Reference steps: tr (10-90 %), Mp (% of the change), ts (band +-2 % of
%   the change), ess. Load steps: peak deviation dVmax, trec (back inside
%   +-2 % of Vref = +-0.12 V), ts20 (inside +-20 mV), ess.
t  = o.tp + o.Ts/2 - sc.t_ev;       % centre of each period, event at t = 0
v  = o.vavg;
v0 = mean(v(t > -2e-3 & t < 0));
vf = mean(v(t > t(end) - 2e-3));
after = t > 0;
m = struct('v0', v0, 'vf', vf, 'ess', vf - sc.ref1, 'dmin', min(o.d(after)), ...
           'dmax', max(o.d(after)), 'tr', NaN, 'Mp', NaN, 'ts', NaN, ...
           'dVmax', NaN, 'trec', NaN, 'ts20', NaN);
if sc.ref1 ~= sc.ref0
    dV = sc.ref1 - sc.ref0;
    s  = (v - v0)/dV;                 % normalized response
    ta = t(after); sa = s(after);
    i10 = find(sa >= 0.1, 1); i90 = find(sa >= 0.9, 1);
    if ~isempty(i10) && ~isempty(i90)
        m.tr = interp_cross(ta, sa, i90, 0.9) - interp_cross(ta, sa, i10, 0.1);
    end
    m.Mp = max(0, 100*(max(sa) - (vf - v0)/dV));
    out = find(after & abs(v - vf) > 0.02*abs(dV), 1, 'last');
    if isempty(out), m.ts = 0; else, m.ts = t(out) + o.Ts/2; end
else
    dev = v(after) - sc.ref1;
    [~, k] = max(abs(dev));
    m.dVmax = dev(k);
    out = find(after & abs(v - sc.ref1) > 0.02*sc.ref1, 1, 'last');
    if isempty(out), m.trec = 0; else, m.trec = t(out) + o.Ts/2; end
    out = find(after & abs(v - sc.ref1) > 0.02, 1, 'last');
    if isempty(out), m.ts20 = 0; else, m.ts20 = t(out) + o.Ts/2; end
end
end

function tc = interp_cross(t, s, i, lev)
if i == 1, tc = t(1); return; end
tc = t(i-1) + (lev - s(i-1))*(t(i) - t(i-1))/(s(i) - s(i-1));
end
