function [Ad, Bd] = e3_zoh(A, B, Ts)
%E3_ZOH  Zero-order-hold discretization (same result as c2d(ss(A,B,..),Ts,'zoh')).
n = size(A, 1);
m = size(B, 2);
M = expm([A, B; zeros(m, n + m)]*Ts);
Ad = M(1:n, 1:n);
Bd = M(1:n, n+1:n+m);
end
