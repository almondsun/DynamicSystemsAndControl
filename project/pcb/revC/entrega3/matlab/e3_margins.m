function m = e3_margins(w, Lw)
%E3_MARGINS  Gain/phase margins from a sampled loop frequency response.
%   m.wc   gain crossover (rad/s), m.PM phase margin (deg)
%   m.w180 phase crossover (rad/s), m.GM gain margin (dB), Inf if none
w   = w(:);
mag = abs(Lw(:));
ph  = unwrap(angle(Lw(:)))*180/pi;
% shift so the low-frequency phase starts in (-360, 0]
ph  = ph - 360*ceil(ph(1)/360);
m = struct('wc', NaN, 'PM', NaN, 'w180', NaN, 'GM', Inf, 'Mpeak', NaN);
i = find(mag(1:end-1) >= 1 & mag(2:end) < 1, 1);
if ~isempty(i)
    f = log(mag(i))/log(mag(i)/mag(i+1));
    m.wc = exp(log(w(i)) + f*(log(w(i+1)) - log(w(i))));
    m.PM = 180 + ph(i) + f*(ph(i+1) - ph(i));
end
j = find(ph(1:end-1) > -180 & ph(2:end) <= -180, 1);
if ~isempty(j)
    f = (ph(j) + 180)/(ph(j) - ph(j+1));
    m.w180 = exp(log(w(j)) + f*(log(w(j+1)) - log(w(j))));
    lm = log(mag(j)) + f*(log(mag(j+1)) - log(mag(j)));
    m.GM = -20*lm/log(10);
end
% peak of the sensitivity |1/(1+L)| (robustness indicator)
m.Mpeak = max(abs(1./(1 + Lw(:))));
end
