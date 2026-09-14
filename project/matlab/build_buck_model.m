function modelPath = build_buck_model(outputFolder, toolkitFolder)
%BUILD_BUCK_MODEL Create and validate an averaged closed-loop model via SATK.
% A fresh folder is required. Structural edits exclusively use model_edit.
arguments
    outputFolder (1,1) string
    toolkitFolder (1,1) string = "/home/mitin/.matlab/agentic-toolkits/simulink"
end
assert(~isfolder(outputFolder),'Choose a new output folder.');
mkdir(outputFolder);
addpath(genpath(fullfile(toolkitFolder,'tools')));
gate = library.settingsLookup();
assert(gate.gatePass,'Custom library setup is required.');
assert(~gate.found,'Review configured custom library index before building.');
p = buck_parameters();
[~,suffix] = fileparts(tempname);
model = "buck_"+extractAfter(string(suffix),max(0,strlength(string(suffix))-10));
new_system(model);
open_system(model);
disp(model_read(char(model),'root','0'));
mw = get_param(model,'ModelWorkspace');
variables = struct('Vin',p.Vin,'L',p.L,'C',p.C,'R0',p.R,'V0',p.V0, ...
    'I0',p.V0/p.R,'Kp',p.Kp,'Ki',p.Ki,'RefFinal',7,'RFinal',p.R);
fields = fieldnames(variables);
for k=1:numel(fields)
    assignin(mw,fields{k},variables.(fields{k}));
end
spec = {
 'reference','Step',struct('Time','0.01','InitialValue','V0','FinalValue','RefFinal');
 'load','Step',struct('Time','0.01','InitialValue','R0','FinalValue','RFinal');
 'error','Sum',struct('Inputs','+-');
 'proportional','Gain',struct('Gain','Kp');
 'integral_gain','Gain',struct('Gain','Ki');
 'integral_state','Integrator',struct('InitialCondition','0');
 'bias','Constant',struct('Value','0.5');
 'raw_duty','Sum',struct('Inputs','+++');
 'duty_limit','Saturate',struct('UpperLimit','0.95','LowerLimit','0.05');
 'one','Constant',struct('Value','1');
 'dprime','Sum',struct('Inputs','+-');
 'driver_inversion','Sum',struct('Inputs','+-');
 'input_voltage','Gain',struct('Gain','Vin');
 'inductor_voltage','Sum',struct('Inputs','+-');
 'inverse_L','Gain',struct('Gain','1/L');
 'inductor_current','Integrator',struct('InitialCondition','I0');
 'load_current','Product',struct('Inputs','*/');
 'capacitor_current','Sum',struct('Inputs','+-');
 'inverse_C','Gain',struct('Gain','1/C');
 'output_voltage','Integrator',struct('InitialCondition','V0');
 'saturation_excess','Sum',struct('Inputs','+-');
 'windup_direction','Product',struct('Inputs','**');
 'zero','Constant',struct('Value','0');
 'antiwindup','Switch',struct('Criteria','u2 > Threshold','Threshold','0');
 'signals','Mux',struct('Inputs','4');
 'record','ToWorkspace',struct('VariableName','buck_signals','SaveFormat','Timeseries')};
ops = cell(size(spec,1),1);
for k=1:size(spec,1)
    ops{k} = struct('op','add_block','type',spec{k,2},'name',spec{k,1},'ref',spec{k,1});
end
response = model_edit(char(model),'root',jsonencode(ops),'full');
disp(response);
if ~contains(string(response),'status: ok')
    disp(model_read(char(model),'root','0'));
    disp(model_check(char(model),'root','["unconnected_ports","unconnected_lines"]'));
    error('Block creation incomplete.');
end
ids = struct();
for k=1:size(spec,1)
    match = regexp(response,[spec{k,1},': (blk_\d+)'],'tokens','once');
    assert(~isempty(match),'Missing block ID.');
    ids.(spec{k,1}) = match{1};
end
% Discover exact parameter names before configuration (Step uses FinalValue).
disp(model_query_params(char(model),jsonencode(struct2cell(ids)),'["all"]','false'));
ops = {};
for k=1:size(spec,1)
    ops{end+1} = struct('op','configure','target',ids.(spec{k,1}),'params',spec{k,3}); %#ok<AGROW>
end
connections = {
 'reference',1,'error',1; 'output_voltage',1,'error',2;
 'error',1,'proportional',1; 'error',1,'integral_gain',1;
 'bias',1,'raw_duty',1; 'proportional',1,'raw_duty',2; 'integral_state',1,'raw_duty',3;
 'raw_duty',1,'duty_limit',1; 'one',1,'dprime',1; 'duty_limit',1,'dprime',2;
 'one',1,'driver_inversion',1; 'dprime',1,'driver_inversion',2;
 'driver_inversion',1,'input_voltage',1; 'input_voltage',1,'inductor_voltage',1;
 'output_voltage',1,'inductor_voltage',2; 'inductor_voltage',1,'inverse_L',1;
 'inverse_L',1,'inductor_current',1; 'inductor_current',1,'capacitor_current',1;
 'output_voltage',1,'load_current',1; 'load',1,'load_current',2;
 'load_current',1,'capacitor_current',2; 'capacitor_current',1,'inverse_C',1;
 'inverse_C',1,'output_voltage',1;
 'raw_duty',1,'saturation_excess',1; 'duty_limit',1,'saturation_excess',2;
 'saturation_excess',1,'windup_direction',1; 'error',1,'windup_direction',2;
 'zero',1,'antiwindup',1; 'windup_direction',1,'antiwindup',2;
 'integral_gain',1,'antiwindup',3; 'antiwindup',1,'integral_state',1;
 'output_voltage',1,'signals',1; 'inductor_current',1,'signals',2;
 'dprime',1,'signals',3; 'reference',1,'signals',4; 'signals',1,'record',1};
for k=1:size(connections,1)
    c = connections(k,:);
    target = sprintf('%s.y%d -> %s.u%d',ids.(c{1}),c{2},ids.(c{3}),c{4});
    ops{end+1} = struct('op','connect','target',target); %#ok<AGROW>
end
ops{end+1} = struct('op','configure','target',"config:"+model, ...
    'params',struct('Solver','ode45','StopTime','0.03','RelTol','1e-8', ...
    'AbsTol','1e-10','MaxStep','1e-5','ReturnWorkspaceOutputs','on'));
response = model_edit(char(model),'root',jsonencode(ops),'incremental');
disp(response);
disp(model_read(char(model),'root','0'));
check = model_check(char(model),'root','["unconnected_ports","unconnected_lines"]');
disp(check);
assert(contains(string(response),'status: ok'),'Model edit failed.');
assert(~contains(lower(string(check)),'severity: error'),'Connectivity errors.');
assert(~contains(string(check),'status: error'),'Model check failed.');
modelPath = fullfile(outputFolder,model+".slx");
save_system(model,modelPath);
refs = [7,5,6,6]; loads = p.R*[1,1,1.2,0.8];
names = ["ref_up","ref_down","load_up","load_down"];
for k=1:4
    in = Simulink.SimulationInput(model);
    in = in.setVariable('RefFinal',refs(k),'Workspace',model);
    in = in.setVariable('RFinal',loads(k),'Workspace',model);
    out = sim(in);
    time = out.buck_signals.Time;
    data = out.buck_signals.Data;
    assert(max(abs(data(time>=0.025,1)-refs(k)))<.02,'Simulink regulation failed.');
    writetable(array2table([time,data],'VariableNames', ...
        {'time_s','voltage_V','current_A','dprime','reference_V'}), ...
        fullfile(outputFolder,names(k)+".csv"));
end
fprintf('PASS: model connectivity and four Simulink scenarios. MODEL=%s\n',modelPath);
end
