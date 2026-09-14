function result = validate_matlab_agent()
% Validate the course example in an isolated folder, preserving user models.
projectRoot = fileparts(fileparts(mfilename('fullpath')));
artifactRoot = fullfile(projectRoot, 'artifacts');
if ~isfolder(artifactRoot)
    mkdir(artifactRoot);
end
outputDir = tempname(artifactRoot);
mkdir(outputDir);
originalDir = pwd;
restoreDir = onCleanup(@() cd(originalDir));
copyfile(fullfile(projectRoot, 'simulations', 'cruise_control.m'), ...
    fullfile(outputDir, 'cruise_control.m'));
cd(outputDir);
run(fullfile(outputDir, 'cruise_control.m'));

assert(abs(force/b - 10) < 1e-12);
assert(abs(m/b - 20) < 1e-12);
assert(abs(t(end) - 120) < 1e-9);
assert(abs(v(end) - 10*(1-exp(-6))) < 1e-3);
assert(maxError < 1e-3);

validationFigure = figure('Visible', 'off', 'Color', 'w');
closeFigure = onCleanup(@() close(validationFigure));
plot(t, v, 'b-', t, vExact, 'r--', 'LineWidth', 1.5);
xlabel('Time [s]'); ylabel('Speed [m/s]'); grid on;
title('Cruise control validation');
legend('Simulink', 'Exact solution', 'Location', 'southeast');
plotFile = fullfile(outputDir, 'speed.png');
exportgraphics(validationFigure, plotFile);

result = struct('model', model, 'modelFile', modelFile, ...
    'outputDir', outputDir, 'plotFile', plotFile, ...
    'finalSpeed', v(end), 'maxError', maxError, ...
    'steadySpeed', force/b, 'timeConstant', m/b);
save(fullfile(outputDir, 'validation.mat'), 'result', 't', 'v', 'vExact');
fprintf('AGENT_VALIDATION_PASS: %s\n', jsonencode(result));
end
