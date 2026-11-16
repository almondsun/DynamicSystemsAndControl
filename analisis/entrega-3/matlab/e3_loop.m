function [Lw, Gw, Cw] = e3_loop(w, p, Kp, Ki, kind)
%E3_LOOP  Loop frequency response L(jw) of the digital PI + Rev C plant.
%   kind = 'cont': design approximation
%          L(s) = (Kp + Ki/s) * Gvd(s) * 1/(1 + tau s) * exp(-1.5 Ts s)
%          (ZOH ~ half a period + one period of computation delay)
%   kind = 'disc': exact sampled-data loop, z = exp(j w Ts)
%          L(z) = (Kp + Ki Ts z/(z-1)) * z^-1 * G_zoh(z)
%          G_zoh = ZOH discretization of plant + RC filter (PWM duty held
%          over the period, ADC sample at the period start, duty applied in
%          the next period).
%   Gw is the plant+sensor part (without delays for 'cont'), Cw the PI.
s  = 1j*w(:);
Ts = p.Ts;
[A, B, Cm, G] = e3_plant(p);
switch kind
    case 'cont'
        Gw = G.num ./ (s.^2 + G.den(2)*s + G.den(3)) ./ (1 + p.tau*s);
        Cw = Kp + Ki./s;
        Lw = Cw .* Gw .* exp(-1.5*Ts*s);
    case 'disc'
        [Ad, Bd] = e3_zoh(A, B, Ts);
        [V, D] = eig(Ad);
        lam = diag(D);
        cv = (Cm*V).';
        bv = V\Bd;
        z  = exp(s*Ts);
        Gw = zeros(size(z));
        for i = 1:numel(lam)
            Gw = Gw + cv(i)*bv(i)./(z - lam(i));
        end
        Gw = real(Gw) + 1j*imag(Gw);
        Cw = Kp + Ki*Ts*z./(z - 1);
        Lw = Cw .* Gw ./ z;
    otherwise
        error('kind must be cont or disc');
end
end
