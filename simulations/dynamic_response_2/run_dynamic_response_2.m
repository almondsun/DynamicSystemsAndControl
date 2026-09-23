function results = run_dynamic_response_2(outputDir)
% Simulate every distinct worked system in Dynamic Response 2 (39 slides).
% Requires MATLAB and Control System Toolbox. No existing workspace is reset.
if nargin < 1
    root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
    outputDir = fullfile(root,'artifacts','dynamic_response_2', ...
        ['run_' char(datetime('now','Format','yyyyMMdd_HHmmss_SSS'))]);
end
if ~isfolder(outputDir), mkdir(outputDir); end
s = tf('s');
checks = struct('name',{},'error',{},'tolerance',{});
data = struct;

% CASE 01
t = (0:0.005:6)'; u = ones(size(t));
% Y(s) is a signal transform; G(s)=s*Y(s) reproduces it with a step.
G = (s+4)*(s+3)/((s+9)*(s+2));
y = step(G,t);
yExact = 2/3 + (10/21)*exp(-9*t) - (1/7)*exp(-2*t);
responsePlot(outputDir,'01',t,u,y,'Unit step','y(t)', ...
    'Partial fractions: distinct real poles',yExact);
% END CASE
checks(end+1) = check('Partial fractions',y,yExact,1e-10);
data.partial = [t u y];

% CASE 02
t = (0:0.005:10)'; u = ones(size(t));
G = 7*(s+5)/(2*(s^2+2*s+3));
y = step(G,t);
w = sqrt(2);
yExact = 35/6-exp(-t).*((35/6)*cos(w*t) ...
    +(7/(3*w))*sin(w*t));
responsePlot(outputDir,'02',t,u,y,'Unit step','y(t)', ...
    'Stable final-value example',yExact);
% END CASE
checks(end+1) = check('Stable final value response',y,yExact,1e-10);
checks(end+1) = check('Stable DC gain',dcgain(G),35/6,1e-12);
data.stable = [t u y];

% CASE 03
t = (0:0.002:3)'; u = ones(size(t));
G = 4/(s^2-5*s+6);
y = step(G,t);
yExact = 2/3-2*exp(2*t)+(4/3)*exp(3*t);
responsePlot(outputDir,'03',t,u,y,'Unit step','y(t)', ...
    'Unstable poles: no finite final value',yExact);
% END CASE
checks(end+1) = check('Unstable response',y,yExact,1e-6);
data.unstable = [t u y];

% CASE 04
t = (0:0.01:12)'; u = ones(size(t));
A = 3.125;
G = 4*(s+A)/(s^2+7*s+5);
y = step(G,t);
p = roots([1 7 5]);
c = [1 1; p(1) p(2)]\[-2.5;4];
yExact = 2.5+c(1)*exp(p(1)*t)+c(2)*exp(p(2)*t);
responsePlot(outputDir,'04',t,u,y,'Unit step','y(t)', ...
    'DC-gain design: A = 3.125',yExact);
% END CASE
checks(end+1) = check('DC-gain response',y,yExact,1e-10);
checks(end+1) = check('DC gain target',dcgain(G),2.5,1e-12);
data.gain = [t u y];

% CASE 05
t = (0:0.01:20)'; u = zeros(size(t));
alpha = 1; beta = 0.5; % Selected example: y(0), ydot(0).
sys = ss([0 1;-1 0],[0;1],[1 0],0);
y = initial(sys,[alpha;beta],t);
yExact = alpha*cos(t)+beta*sin(t);
responsePlot(outputDir,'05',t,u,y,'External input','y(t)', ...
    'Unforced oscillator: nonzero initial state',yExact);
% END CASE
checks(end+1) = check('Homogeneous ODE',y,yExact,1e-10);
data.homogeneous = [t u y];

% CASE 06
t = (0:0.005:8)'; u = 3*ones(size(t));
alpha = 1; beta = 0.5; % Same selected initial conditions.
sys = ss([0 1;-4 -5],[0;1],[1 0],0);
y = lsim(sys,u,t,[alpha;beta],'zoh');
yExact = 3/4+(-3+beta+4*alpha)/3*exp(-t) ...
    +(3-4*alpha-4*beta)/12*exp(-4*t);
responsePlot(outputDir,'06',t,u,y,'Forcing u(t)','y(t)', ...
    'Forced second-order equation',yExact);
% END CASE
checks(end+1) = check('Forced ODE',y,yExact,1e-10);
data.forced = [t u y];

% CASE 07
t = (0:0.001:3)'; u = 1-0.3*exp(-3*t);
G = 1/(s+6);
y = lsim(G,u,t,0,'foh');
yExact = 1/6-exp(-3*t)/10-exp(-6*t)/15;
responsePlot(outputDir,'07',t,u,y,'Input u(t)','y(t)', ...
    'First-order system with exponential input',yExact);
% END CASE
checks(end+1) = check('First-order ODE, FOH input',y,yExact,3e-8);
data.firstOrder = [t u y];

% CASE 08
t = (0:0.05:120)'; u = 500*ones(size(t));
m = 1000; b = 50; % kg, N*s/m; slide 29 transfer coefficients.
Gx = 1/(m*s^2+b*s); Gv = 1/(m*s+b);
x = lsim(Gx,u,t,[],'zoh');
v = lsim(Gv,u,t,[],'zoh');
xExact = 10*(t-20*(1-exp(-t/20)));
vExact = 10*(1-exp(-t/20));
responsePlot(outputDir,'08',t,u,[x v],'Force [N]', ...
    {'Position [m]','Speed [m/s]'},'Cruise control: 500 N step', ...
    [xExact vExact]);
% END CASE
checks(end+1) = check('Car position',x,xExact,1e-7);
checks(end+1) = check('Car speed',v,vExact,1e-9);
data.cruise = [t u x v];

% CASE 09
t = (0:0.001:1)'; u = ones(size(t)); % Armature voltage: 1 V.
Jm = 0.02; b = 0.005; Kt = 0.5; Ke = 0.5;
Ra = 2.5; La = 0.1;
Gw = Kt/((Jm*s+b)*(La*s+Ra)+Kt*Ke);
Gtheta = Gw/s;
omega = step(Gw,t); theta = step(Gtheta,t);
% Independent state model: states [armature current; speed; angle].
Am = [-Ra/La -Ke/La 0; Kt/Jm -b/Jm 0; 0 1 0];
motor = ss(Am,[1/La;0;0],[0 1 0;0 0 1],[0;0]);
ym = lsim(motor,u,t,zeros(3,1),'zoh');
responsePlot(outputDir,'09',t,u,[omega theta],'Voltage [V]', ...
    {'Speed [rad/s]','Angle [rad]'},'DC motor: 1 V step',ym);
% END CASE
checks(end+1) = check('Motor TF versus physical states', ...
    [omega theta],ym,1e-10);
checks(end+1) = check('Motor steady speed',dcgain(Gw),40/21,1e-12);
data.motor = [t u omega theta];

% CASE 10
t = (0:0.01:10)'; k = (0:1000)';
d = 1; I = 5000; H = d/(I*s^2);
u = 25*double(k>=500 & k<510); % Exactly [5.0, 5.1) seconds.
theta = lsim(H,u,t,[],'zoh');
thetaExact = 0.0025*(max(t-5,0).^2-max(t-5.1,0).^2);
responsePlot(outputDir,'10',t,u,rad2deg(theta),'Thrust [N]', ...
    'Attitude [deg]','Satellite: single thrust pulse', ...
    rad2deg(thetaExact));
% END CASE
checks(end+1) = check('Satellite single pulse [rad]',theta,thetaExact,1e-12);
data.singlePulse = [t u theta];

% CASE 11
u = 25*double(k>=500 & k<510) ...
    -25*double(k>=610 & k<620); % Negative pulse [6.1, 6.2).
theta = lsim(H,u,t,[],'zoh');
thetaExact = 0.0025*(max(t-5,0).^2-max(t-5.1,0).^2 ...
    -max(t-6.1,0).^2+max(t-6.2,0).^2);
omega = lsim(d/(I*s),u,t,[],'zoh');
responsePlot(outputDir,'11',t,u,rad2deg(theta),'Thrust [N]', ...
    'Attitude [deg]','Satellite: equal opposing thrust pulses', ...
    rad2deg(thetaExact));
% END CASE
checks(end+1) = check('Satellite double pulse [rad]',theta,thetaExact,1e-12);
checks(end+1) = check('Satellite final angle [rad]',theta(end),0.00055,1e-12);
checks(end+1) = check('Satellite residual speed [rad/s]',omega(end),0,1e-12);
checks(end+1) = check('Positive pulse impulse [N*s]',sum(u(u>0))*0.01,2.5,1e-12);
checks(end+1) = check('Negative pulse impulse [N*s]',sum(u(u<0))*0.01,-2.5,1e-12);
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
save(fullfile(outputDir,'simulation_data.mat'),'data','results');
fid = fopen(fullfile(outputDir,'validation.json'),'w');
assert(fid~=-1,'Cannot create validation.json');
cleanupFile = onCleanup(@() fclose(fid));
fprintf(fid,'%s\n',jsonencode(results,PrettyPrint=true));
disp(results);
assert(results.passed,'One or more numerical validation checks failed.');
end

function item = check(name,actual,expected,tolerance)
item = struct('name',name,'error',max(abs(actual-expected),[],'all'), ...
    'tolerance',tolerance);
end

function responsePlot(folder,id,t,u,y,inputLabel,outputLabels,heading,reference)
% Own only this figure; preserve unrelated desktop figures and root defaults.
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
    if strcmp(id,'09'), referenceName = 'Physical state model';
    else, referenceName = 'Exact solution'; end
    legend(ax,'MATLAB response',referenceName, ...
        'Location','northwest','FontSize',12);
end
xlabel(ax,'Time [s]');
drawnow;
exportgraphics(fig,fullfile(folder,[id '.png']),'Resolution',170);
end
