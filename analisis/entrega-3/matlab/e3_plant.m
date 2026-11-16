function [A, B, Cm, G] = e3_plant(p)
%E3_PLANT  Small-signal averaged model of the Rev C buck (input d, CCM).
%   States x = [iL; vC; vm], vm = measured vo after the ADC RC filter,
%   expressed in volts at the vo scale (the firmware divides by k).
%     L diL/dt = (Vin + Vf) d - rL iL - vC
%     C dvC/dt = iL - vC/R
%     tau dvm/dt = vC - vm
%   G holds the plant transfer function Vo(s)/D(s) (without the sensor):
%     Gvd(s) = (Vin+Vf) / (L C s^2 + (L/R + rL C) s + 1 + rL/R)
A  = [-p.rL/p.L, -1/p.L,        0;
       1/p.C,    -1/(p.R*p.C),  0;
       0,         1/p.tau,     -1/p.tau];
B  = [(p.Vin + p.Vf)/p.L; 0; 0];
Cm = [0 0 1];
LC = p.L*p.C;
G.num  = (p.Vin + p.Vf)/LC;
G.den  = [1, (p.L/p.R + p.rL*p.C)/LC, (1 + p.rL/p.R)/LC];
G.wn   = sqrt(G.den(3));
G.zeta = G.den(2)/(2*G.wn);
G.K0   = (p.Vin + p.Vf)/(1 + p.rL/p.R);      % DC gain, V per unit duty
G.poles = roots(G.den);
end
