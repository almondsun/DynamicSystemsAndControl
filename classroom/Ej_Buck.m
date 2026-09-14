%% Ejemplo Convertidor Buck
clear; clc;

%% Respuesta al escalón: V/D
L = 270e-6;
C = 20e-6;
R = 6;
Vi = 12;

s = tf('s');
G = Vi/(L*C)/(s^2 + s*1/(R*C) + 1/(L*C));
zpk(G);

step(G);

%% Respuesta controlador P
C = -0.9/Vi;

T = feedback(C*G,1);
% zpk(T);

%% Sintonización controlador PI

C = pidtune(G,'PI'); % design a PI for G
% pidTuner(G,C); % pidTuner app

T = feedback(C*G,1);
step(T);
