function o = e3_sim(p, Kp, Ki, sc, mode)
%E3_SIM  Sampled-data simulation of the Rev C buck with the digital PI.
%   mode = 'avg' : large-signal averaged model, one exact step per PWM period
%   mode = 'sw'  : switched circuit (MOSFET on / diode on / DCM), exact
%                  matrix-exponential steps, sc.m sub-steps per interval
%   Both include rL, MOSFET Rds, diode V0 + Rd*i, ESR, driver delay, the
%   ADC RC filter, 12-bit quantization, timer resolution, the duty clamp and
%   conditional anti-windup.
%
%   Timing (STM32 TIM1, one PI run per period):
%     t = n*Ts : update event -> new CCR becomes active, ADC samples vm
%     PI computes d from that sample -> written to the CCR preload
%     -> applied from t = (n+1)*Ts. So the loop has one period of delay.
%
%   sc fields: t_end, t_ev, ref0, ref1, R0, R1, closed (true/false),
%              d_ol (open-loop duty), m (sub-steps per interval, 'sw')
%   States x = [iL; vC; vm_pin; q], vm_pin = ADC pin voltage, q = int(vo).
if ~isfield(sc, 'm'), sc.m = 12; end
Ts  = p.Ts;
N   = round(sc.t_end/Ts);
nev = round(sc.t_ev/Ts);
lsb_pin = p.Vadc/(2^p.nbits - 1);
R   = sc.R0;
ref = sc.ref0;
D0  = (ref*(1 + p.rL/R) + p.Vf)/(p.Vin + p.Vf);
x   = [ref/R; ref; p.k*ref; 0];
I   = D0;
d_pend = D0;
if ~sc.closed, d_pend = sc.d_ol; end
o.tp = (0:N-1)'*Ts;
[o.d, o.vavg, o.y, o.ref, o.R, o.iL, o.I] = deal(zeros(N, 1));
raw = cell(N, 1);
for n = 0:N-1
    if n >= nev
        ref = sc.ref1;
        R   = sc.R1;
    end
    d_app = d_pend;                         % CCR loaded at this update event
    code = min(max(round(x(3)/lsb_pin), 0), 2^p.nbits - 1);
    y = code*p.lsb;                         % firmware reading, volts at vo
    if sc.closed
        e  = ref - y;
        In = I + Ki*Ts*e;                   % backward-Euler integral
        u  = Kp*e + In;
        if (u > p.dmax && e > 0) || (u < p.dmin && e < 0)
            In = I;                         % conditional integration
            u  = Kp*e + I;
        end
        I = In;
        u = min(max(u, p.dmin), p.dmax);
        d_pend = round(u*p.ARR)/p.ARR;      % timer resolution
    end
    o.iL(n+1) = x(1);
    x(4) = 0;
    switch mode
        case 'avg'
            x = step_avg(x, d_app, R, p);
        case 'sw'
            [x, rt, rv, ri, rm] = step_sw(x, d_app, R, p, sc.m);
            raw{n+1} = [n*Ts + rt(:), rv(:), ri(:), rm(:)/p.k];
        otherwise
            error('mode must be avg or sw');
    end
    o.d(n+1)    = d_app;
    o.vavg(n+1) = x(4)/Ts;                  % exact average of vo over the period
    o.y(n+1)    = y;
    o.ref(n+1)  = ref;
    o.R(n+1)    = R;
    o.I(n+1)    = I;
end
o.Ts = Ts;
if strcmp(mode, 'sw')
    o.raw = vertcat(raw{:});
end
end

% ------------------------------------------------------------------------
function x = step_avg(x, d, R, p)
de = d;
if d > 0, de = min(d + p.tdrv/p.Ts, 1); end
[A, b] = sys_mat(p, R, de*p.Rds + (1 - de)*p.Rd, de*p.Vin - (1 - de)*p.V0, false);
x = aff(A, b, x, p.Ts);
end

function [x, tt, vv, ii, mm] = step_sw(x, d, R, p, m)
Ts = p.Ts;
ton = 0;
if d > 0, ton = min(d*Ts + p.tdrv, Ts); end
toff = Ts - ton;
tt = zeros(2*m, 1); vv = tt; ii = tt; mm = tt; k = 0; t = 0;
a1 = 1/(1 + p.rC/R); a2 = p.rC*a1;
if ton > 0
    [A, b] = sys_mat(p, R, p.Rds, p.Vin, false);
    h = ton/m;
    [Md, md] = affm(A, b, h);
    for j = 1:m
        x = Md*x + md; t = t + h; k = k + 1;
        tt(k) = t; vv(k) = a1*x(2) + a2*x(1); ii(k) = x(1); mm(k) = x(3);
    end
end
if toff > 0
    [A, b]   = sys_mat(p, R, p.Rd, -p.V0, false);
    [Az, bz] = sys_mat(p, R, 0, 0, true);
    h = toff/m;
    [Md, md] = affm(A, b, h);
    [Mz, mz] = affm(Az, bz, h);
    dcm = x(1) <= 0;
    for j = 1:m
        if ~dcm
            xn = Md*x + md;
            if xn(1) < 0                       % diode current reaches zero
                f = x(1)/(x(1) - xn(1));
                x = aff(A, b, x, f*h); x(1) = 0;
                x = aff(Az, bz, x, (1 - f)*h);
                dcm = true;
            else
                x = xn;
            end
        else
            x = Mz*x + mz;
        end
        t = t + h; k = k + 1;
        tt(k) = t; vv(k) = a1*x(2) + a2*x(1); ii(k) = x(1); mm(k) = x(3);
    end
end
tt = tt(1:k); vv = vv(1:k); ii = ii(1:k); mm = mm(1:k);
end

function [A, b] = sys_mat(p, R, Rsw, Vsrc, dcm)
% dx/dt = A x + b,  x = [iL; vC; vm_pin; q],  vo = a1 vC + a2 iL
a1 = 1/(1 + p.rC/R); a2 = p.rC*a1;
A = zeros(4); b = zeros(4, 1);
if ~dcm
    A(1, :) = [-(p.rL + Rsw + a2)/p.L, -a1/p.L, 0, 0];
    b(1) = Vsrc/p.L;
end
A(2, :) = [(1 - a2/R)/p.C, -a1/(R*p.C), 0, 0];
A(3, :) = [p.k*a2/p.tau, p.k*a1/p.tau, -1/p.tau, 0];
A(4, :) = [a2, a1, 0, 0];
end

function x = aff(A, b, x, h)
[Md, md] = affm(A, b, h);
x = Md*x + md;
end

function [Md, md] = affm(A, b, h)
n = size(A, 1);
M = expm([A, b; zeros(1, n + 1)]*h);
Md = M(1:n, 1:n);
md = M(1:n, n+1);
end
