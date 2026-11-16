function o = e3_linsim(p, Kp, Ki, dr, N, nev)
%E3_LINSIM  Linear sampled-data model used for the design (no ripple, no
%   saturation, no quantization). Reference step dr at period nev.
%   Returns the per-period average of vo (incremental, V) and the duty.
[A, B, ~] = e3_plant(p);
A4 = [A, zeros(3, 1); 0 1 0 0];          % q = integral of vC
B4 = [B; 0];
[Ad, Bd] = e3_zoh(A4, B4, p.Ts);
x = zeros(4, 1); I = 0; d_pend = 0;
o.vavg = zeros(N, 1); o.d = zeros(N, 1);
for n = 0:N-1
    r = dr*(n >= nev);
    d_app = d_pend;
    e = r - x(3);
    I = I + Ki*p.Ts*e;
    d_pend = Kp*e + I;
    x(4) = 0;
    x = Ad*x + Bd*d_app;
    o.vavg(n+1) = x(4)/p.Ts;
    o.d(n+1) = d_app;
end
o.tp = (0:N-1)'*p.Ts;
o.Ts = p.Ts;
end
