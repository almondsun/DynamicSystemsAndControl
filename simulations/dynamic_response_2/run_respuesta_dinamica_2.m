function results = run_respuesta_dinamica_2(outputDir)
% Simula todos los sistemas de Respuesta dinamica 2 (39 diapositivas).
% Requiere MATLAB y Control System Toolbox. Conserva el espacio de trabajo.
if nargin < 1
    root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
    outputDir = fullfile(root,'artifacts','dynamic_response_2', ...
        ['es_' char(datetime('now','Format','yyyyMMdd_HHmmss_SSS'))]);
end
if ~isfolder(outputDir), mkdir(outputDir); end
s = tf('s');
checks = struct('name',{},'error',{},'tolerance',{});
data = struct;

% CASE 01
t = (0:0.005:6)'; u = ones(size(t));
% Y(s) es la transformada de salida; G(s)=s*Y(s) la reproduce con un escalon.
G = (s+4)*(s+3)/((s+9)*(s+2));
y = step(G,t);
yExact = 2/3 + (10/21)*exp(-9*t) - (1/7)*exp(-2*t);
responsePlot(outputDir,'01',t,u,y,'Escalón unitario','y(t)', ...
    'Fracciones parciales: polos reales distintos',yExact);
% END CASE
checks(end+1) = check('Fracciones parciales',y,yExact,1e-10);
data.partial = [t u y];

% CASE 02
t = (0:0.005:10)'; u = ones(size(t));
G = 7*(s+5)/(2*(s^2+2*s+3));
y = step(G,t);
w = sqrt(2);
yExact = 35/6-exp(-t).*((35/6)*cos(w*t) ...
    +(7/(3*w))*sin(w*t));
responsePlot(outputDir,'02',t,u,y,'Escalón unitario','y(t)', ...
    'Ejemplo estable del valor final',yExact);
% END CASE
checks(end+1) = check('Respuesta estable del valor final',y,yExact,1e-10);
checks(end+1) = check('Ganancia estatica estable',dcgain(G),35/6,1e-12);
data.stable = [t u y];

% CASE 03
t = (0:0.002:3)'; u = ones(size(t));
G = 4/(s^2-5*s+6);
y = step(G,t);
yExact = 2/3-2*exp(2*t)+(4/3)*exp(3*t);
responsePlot(outputDir,'03',t,u,y,'Escalón unitario','y(t)', ...
    'Polos inestables: sin valor final finito',yExact);
% END CASE
checks(end+1) = check('Respuesta inestable',y,yExact,1e-6);
data.unstable = [t u y];

% CASE 04
t = (0:0.01:12)'; u = ones(size(t));
A = 3.125;
G = 4*(s+A)/(s^2+7*s+5);
y = step(G,t);
p = roots([1 7 5]);
c = [1 1; p(1) p(2)]\[-2.5;4];
yExact = 2.5+c(1)*exp(p(1)*t)+c(2)*exp(p(2)*t);
responsePlot(outputDir,'04',t,u,y,'Escalón unitario','y(t)', ...
    'Ganancia estática: A = 3.125',yExact);
% END CASE
checks(end+1) = check('Respuesta de ganancia estatica',y,yExact,1e-10);
checks(end+1) = check('Objetivo de ganancia estatica',dcgain(G),2.5,1e-12);
data.gain = [t u y];

% CASE 05
t = (0:0.01:20)'; u = zeros(size(t));
alpha = 1; beta = 0.5; % Valores elegidos: y(0), ydot(0).
sys = ss([0 1;-1 0],[0;1],[1 0],0);
y = initial(sys,[alpha;beta],t);
yExact = alpha*cos(t)+beta*sin(t);
responsePlot(outputDir,'05',t,u,y,'Entrada externa','y(t)', ...
    'Oscilador libre: estado inicial no nulo',yExact);
% END CASE
checks(end+1) = check('EDO homogenea',y,yExact,1e-10);
data.homogeneous = [t u y];

% CASE 06
t = (0:0.005:8)'; u = 3*ones(size(t));
alpha = 1; beta = 0.5; % Mismas condiciones iniciales elegidas.
sys = ss([0 1;-4 -5],[0;1],[1 0],0);
y = lsim(sys,u,t,[alpha;beta],'zoh');
yExact = 3/4+(-3+beta+4*alpha)/3*exp(-t) ...
    +(3-4*alpha-4*beta)/12*exp(-4*t);
responsePlot(outputDir,'06',t,u,y,'Entrada u(t)','y(t)', ...
    'Ecuación forzada de segundo orden',yExact);
% END CASE
checks(end+1) = check('EDO forzada',y,yExact,1e-10);
data.forced = [t u y];

% CASE 07
t = (0:0.001:3)'; u = 1-0.3*exp(-3*t);
G = 1/(s+6);
y = lsim(G,u,t,0,'foh');
yExact = 1/6-exp(-3*t)/10-exp(-6*t)/15;
responsePlot(outputDir,'07',t,u,y,'Entrada u(t)','y(t)', ...
    'Primer orden con entrada exponencial',yExact);
% END CASE
checks(end+1) = check('EDO de primer orden, entrada FOH',y,yExact,3e-8);
data.firstOrder = [t u y];

% CASE 08
t = (0:0.05:120)'; u = 500*ones(size(t));
m = 1000; b = 50; % kg, N*s/m; coeficientes de la diapositiva 29.
Gx = 1/(m*s^2+b*s); Gv = 1/(m*s+b);
x = lsim(Gx,u,t,[],'zoh');
v = lsim(Gv,u,t,[],'zoh');
xExact = 10*(t-20*(1-exp(-t/20)));
vExact = 10*(1-exp(-t/20));
responsePlot(outputDir,'08',t,u,[x v],'Fuerza [N]', ...
    {'Posición [m]','Velocidad [m/s]'},'Control de crucero: escalón de 500 N', ...
    [xExact vExact]);
% END CASE
checks(end+1) = check('Posicion del automovil',x,xExact,1e-7);
checks(end+1) = check('Velocidad del automovil',v,vExact,1e-9);
data.cruise = [t u x v];

% CASE 09
t = (0:0.001:1)'; u = ones(size(t)); % Tension de armadura: 1 V.
Jm = 0.02; b = 0.005; Kt = 0.5; Ke = 0.5;
Ra = 2.5; La = 0.1;
Gw = Kt/((Jm*s+b)*(La*s+Ra)+Kt*Ke);
Gtheta = Gw/s;
omega = step(Gw,t); theta = step(Gtheta,t);
% Modelo independiente: estados [corriente; velocidad; angulo].
Am = [-Ra/La -Ke/La 0; Kt/Jm -b/Jm 0; 0 1 0];
motor = ss(Am,[1/La;0;0],[0 1 0;0 0 1],[0;0]);
ym = lsim(motor,u,t,zeros(3,1),'zoh');
responsePlot(outputDir,'09',t,u,[omega theta],'Tensión [V]', ...
    {'Velocidad [rad/s]','Ángulo [rad]'},'Motor CC: escalón de 1 V',ym);
% END CASE
checks(end+1) = check('Motor: transferencia frente a estados', ...
    [omega theta],ym,1e-10);
checks(end+1) = check('Velocidad final del motor',dcgain(Gw),40/21,1e-12);
data.motor = [t u omega theta];

% CASE 10
t = (0:0.01:10)'; k = (0:1000)';
d = 1; I = 5000; H = d/(I*s^2);
u = 25*double(k>=500 & k<510); % Exactamente [5.0, 5.1) segundos.
theta = lsim(H,u,t,[],'zoh');
thetaExact = 0.0025*(max(t-5,0).^2-max(t-5.1,0).^2);
responsePlot(outputDir,'10',t,u,rad2deg(theta),'Empuje [N]', ...
    'Orientación [grados]','Satélite: un pulso de empuje', ...
    rad2deg(thetaExact));
% END CASE
checks(end+1) = check('Satelite: pulso unico [rad]',theta,thetaExact,1e-12);
data.singlePulse = [t u theta];

% CASE 11
u = 25*double(k>=500 & k<510) ...
    -25*double(k>=610 & k<620); % Pulso negativo [6.1, 6.2).
theta = lsim(H,u,t,[],'zoh');
thetaExact = 0.0025*(max(t-5,0).^2-max(t-5.1,0).^2 ...
    -max(t-6.1,0).^2+max(t-6.2,0).^2);
omega = lsim(d/(I*s),u,t,[],'zoh');
responsePlot(outputDir,'11',t,u,rad2deg(theta),'Empuje [N]', ...
    'Orientación [grados]','Satélite: pulsos iguales y opuestos', ...
    rad2deg(thetaExact));
% END CASE
checks(end+1) = check('Satelite: pulso doble [rad]',theta,thetaExact,1e-12);
checks(end+1) = check('Satelite: angulo final [rad]',theta(end),0.00055,1e-12);
checks(end+1) = check('Satelite: velocidad residual [rad/s]',omega(end),0,1e-12);
checks(end+1) = check('Impulso positivo [N*s]',sum(u(u>0))*0.01,2.5,1e-12);
checks(end+1) = check('Impulso negativo [N*s]',sum(u(u<0))*0.01,-2.5,1e-12);
data.doublePulse = [t u theta omega];

results.matlabVersion = version;
results.outputDir = outputDir;
results.checks = checks;
results.passed = all([checks.error] <= [checks.tolerance]);
results.carSpeedAt120 = data.cruise(end,4);
results.carPositionAt120 = data.cruise(end,3);
results.motorSteadySpeed = dcgain(Gw);
results.motorPoles = pole(Gw)';
results.satelliteSingleAt10Deg = rad2deg(data.singlePulse(end,3));
results.satelliteDoubleFinalDeg = rad2deg(theta(end));
results.satelliteResidualRate = omega(end);
results.unstableAt3 = data.unstable(end,3);

% Polos y ceros de las funciones de transferencia (no de Y(s)).
models = {(s+4)*(s+3)/((s+9)*(s+2)), ...
    7*(s+5)/(2*(s^2+2*s+3)), 4/(s^2-5*s+6), ...
    4*(s+3.125)/(s^2+7*s+5), 1/(s^2+1), ...
    1/(s^2+5*s+4), 1/(s+6), Gx, Gv, Gw, Gtheta, H};
names = {'Fracciones parciales','Valor final estable','Valor final inestable', ...
    'Ganancia estatica','Oscilador','EDO forzada','Primer orden', ...
    'Automovil: posicion','Automovil: velocidad','Motor: velocidad', ...
    'Motor: angulo','Satelite'};
pz = struct('name',{},'poles',{},'zeros',{},'relativeDegree',{});
for q = 1:numel(models)
    pp = pole(models{q}); zz = zero(models{q});
    pz(q) = struct('name',names{q},'poles',mat2str(pp.',8), ...
        'zeros',mat2str(zz.',8),'relativeDegree',numel(pp)-numel(zz));
end
results.poleZero = pz;

save(fullfile(outputDir,'simulation_data.mat'),'data','results');
fid = fopen(fullfile(outputDir,'validation.json'),'w');
assert(fid~=-1,'No se puede crear validation.json');
cleanupFile = onCleanup(@() fclose(fid));
fprintf(fid,'%s\n',jsonencode(results,PrettyPrint=true));
disp(results);
assert(results.passed,'Fallo en una o mas comprobaciones numericas.');
end

function item = check(name,actual,expected,tolerance)
item = struct('name',name,'error',max(abs(actual-expected),[],'all'), ...
    'tolerance',tolerance);
end

function responsePlot(folder,id,t,u,y,inputLabel,outputLabels,heading,reference)
% Gestiona solo esta figura y conserva las figuras existentes.
if ischar(outputLabels), outputLabels = {outputLabels}; end
fig = figure('Visible','off','Color','w','Position',[50 50 1100 650]);
cleanupFigure = onCleanup(@() close(fig));
tl = tiledlayout(fig,size(y,2)+1,1,'TileSpacing','compact','Padding','compact');
title(tl,heading,'FontSize',15,'FontWeight','bold');
ax = nexttile(tl);
set(ax,'FontSize',15);
if strcmp(id,'07')
    plot(ax,t,u,'Color',[0.85 0.35 0.08],'LineWidth',1.7);
else
    stairs(ax,t,u,'Color',[0.85 0.35 0.08],'LineWidth',1.7);
end
ylabel(ax,inputLabel); grid(ax,'on'); xlim(ax,[t(1) t(end)]);
for j = 1:size(y,2)
    ax = nexttile(tl);
    set(ax,'FontSize',15);
    plot(ax,t,y(:,j),'Color',[0.02 0.4 0.7],'LineWidth',2);
    hold(ax,'on');
    indices = unique(round(linspace(1,numel(t),45)));
    plot(ax,t(indices),reference(indices,j),'k.','MarkerSize',8);
    ylabel(ax,outputLabels{j}); grid(ax,'on'); xlim(ax,[t(1) t(end)]);
    if strcmp(id,'09'), referenceName = 'Modelo físico de estados';
    else, referenceName = 'Solución exacta'; end
    legend(ax,'Respuesta MATLAB',referenceName, ...
        'Location','northwest','FontSize',12);
end
xlabel(ax,'Tiempo [s]');
drawnow;
exportgraphics(fig,fullfile(folder,[id '.png']),'Resolution',170);
end
