function [Kp, Ki] = e3_design(p, wc, wz)
%E3_DESIGN  PI gains from the frequency-response procedure.
%   C(s) = Kp (1 + wz/s) = Kp + Ki/s, Ki = Kp*wz.
%   Kp is chosen so that |L(j wc)| = 1 on the design approximation
%   L(s) = C(s) Gvd(s) Hrc(s) exp(-1.5 Ts s).
s = 1j*wc;
[~, ~, ~, G] = e3_plant(p);
Gc = G.num/(s^2 + G.den(2)*s + G.den(3))/(1 + p.tau*s);
Kp = 1/abs((1 + wz/s)*Gc);
Ki = Kp*wz;
end
