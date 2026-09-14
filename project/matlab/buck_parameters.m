function p = buck_parameters()
%BUCK_PARAMETERS Project schematic values, in SI units.
p.Vin = 12;
p.L = 660e-6;
p.C = 20e-6;
p.R = 6;
p.fs = 1e4;
p.Ts = 1/p.fs;
p.V0 = 6;
p.dp0 = 0.5;
p.wc = 1000;
p.wz = 3000;
s = tf('s');
p.Gd = p.Vin/(p.L*p.C*s^2 + p.L/p.R*s + 1);
p.Gdp = -p.Gd;
p.Kp = 1/(abs(evalfr(p.Gd,1i*p.wc))*sqrt(1+(p.wz/p.wc)^2));
p.Ki = p.wz*p.Kp;
p.dmin = 0.05;
p.dmax = 0.95;
end
