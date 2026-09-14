% Cruise control from "2 Dynamic Models", slides 9-13.
% Upload this file to MATLAB Online and click Run (requires Simulink).
% Equation: m*dv/dt + b*v = u, with v(0) = 0.

assert(~isempty(ver('simulink')), ...
    'This script requires Simulink in your MATLAB account.');

m = 1000;              % Car mass [kg]
b = 50;                % Viscous drag coefficient [N*s/m]
force = 500;           % Applied force for t >= 0 [N]
stopTime = 120;        % Simulation duration [s]

% Use a fresh model name on each run to preserve existing models/files.
modelBase = 'cruise_control';
model = modelBase;
suffix = 1;
while bdIsLoaded(model) || ~isempty(which(model)) || ...
        isfile([model '.slx']) || isfile([model '.mdl'])
    model = sprintf('%s_%d', modelBase, suffix);
    suffix = suffix + 1;
end

load_system('simulink');
new_system(model);

add_block('simulink/Sources/Step', [model '/Driving Force'], ...
    'Time', '0', 'Before', '0', 'After', num2str(force), ...
    'Position', [40 90 80 130]);
add_block('simulink/Continuous/Transfer Fcn', [model '/Car Dynamics'], ...
    'Numerator', '1', 'Denominator', mat2str([m b]), ...
    'Position', [155 85 285 135]);
add_block('simulink/Sinks/Scope', [model '/Speed Scope'], ...
    'Position', [370 75 410 115]);
add_block('simulink/Sinks/To Workspace', [model '/Record Speed'], ...
    'VariableName', 'speed', 'SaveFormat', 'Timeseries', ...
    'MaxDataPoints', 'inf', ...
    'Position', [350 165 460 205]);

add_line(model, 'Driving Force/1', 'Car Dynamics/1', 'autorouting', 'on');
add_line(model, 'Car Dynamics/1', 'Speed Scope/1', 'autorouting', 'on');
add_line(model, 'Car Dynamics/1', 'Record Speed/1', 'autorouting', 'on');

set_param(model, 'StartTime', '0', 'StopTime', num2str(stopTime), ...
    'SolverType', 'Variable-step', 'Solver', 'ode45', ...
    'RelTol', '1e-6', 'AbsTol', '1e-8', 'MaxStep', '0.5', ...
    'ReturnWorkspaceOutputs', 'on');

modelFile = fullfile(pwd, [model '.slx']);
save_system(model, modelFile);
open_system(model);
simOut = sim(model);
speed = simOut.get('speed');
t = speed.Time;
v = speed.Data(:);

% Compare Simulink with the exact solution for a force step from rest.
vExact = (force / b) * (1 - exp(-(b / m) * t));
maxError = max(abs(v - vExact));
assert(maxError < 1e-3, ...
    'Simulation differs from the exact solution by %.6g m/s.', maxError);

figure('Name', 'Cruise control: speed response', 'Color', 'w');
plot(t, v, 'b-', 'LineWidth', 1.8);
hold on;
plot(t, vExact, 'r--', 'LineWidth', 1.2);
yline(force / b, 'k:', 'Steady speed: 10 m/s');
grid on;
xlabel('Time [s]');
ylabel('Speed [m/s]');
title('Car response to a 500 N driving force');
legend('Simulink', 'Exact solution', 'Steady speed', 'Location', 'southeast');

fprintf('Saved Simulink model: %s\n', modelFile);
fprintf('Steady speed: %.2f m/s (%.2f km/h)\n', force/b, 3.6*force/b);
fprintf('Time constant: %.2f s\n', m/b);
fprintf('Speed at %.0f s: %.4f m/s\n', t(end), v(end));
fprintf('Maximum error versus exact solution: %.3g m/s\n', maxError);

% Teacher's solution:
s = tf('s');
G = 1/(m*s + b);
step(force*G);
