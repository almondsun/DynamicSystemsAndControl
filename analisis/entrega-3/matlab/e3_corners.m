function P = e3_corners(p)
%E3_CORNERS  Tolerance corners: L +-10 %, C 14/20/22 uF (DC-bias derating
%   down to -30 %), R 4.8/6/7.2 ohm, rL 0.9/1.2 ohm, Vin 11.5/12.5 V.
Ls  = p.L*[0.9 1 1.1];
Cs  = [14 20 22]*1e-6;
Rs  = [4.8 6 7.2];
rLs = [0.9 1.2];
Vs  = [11.5 12.5];
P = [];
for L = Ls, for C = Cs, for R = Rs, for rL = rLs, for V = Vs %#ok<ALIGN>
    q = e3_params('L', L, 'C', C, 'R', R, 'rL', rL, 'Vin', V, 'fs', p.fs);
    P = [P; q]; %#ok<AGROW>
end, end, end, end, end
end
