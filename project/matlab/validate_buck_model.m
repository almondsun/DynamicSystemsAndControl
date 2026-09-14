function validate_buck_model(outputFolder)
%VALIDATE_BUCK_MODEL Run the delivered model without changing its parameters.
arguments
    outputFolder (1,1) string
end
assert(~isfolder(outputFolder),'Choose a new output folder.');
assert(~bdIsLoaded('buck_control'), ...
    'Run validation in a fresh batch session to preserve any open user model.');
mkdir(outputFolder);
project = fileparts(fileparts(mfilename('fullpath')));
open_system(fullfile(project,'models','buck_control.slx'));
refs = [7,5,6,6]; loads = [6,6,7.2,4.8];
names = ["ref_up","ref_down","load_up","load_down"];
for k=1:4
    in = Simulink.SimulationInput('buck_control');
    in = in.setVariable('RefFinal',refs(k),'Workspace','buck_control');
    in = in.setVariable('RFinal',loads(k),'Workspace','buck_control');
    out = sim(in);
    t = out.buck_signals.Time;
    data = out.buck_signals.Data;
    assert(all(isfinite(data),'all'),'Non-finite simulation result.');
    assert(max(abs(data(t>=.025,1)-refs(k)))<.02,'Regulation failed.');
    assert(all(data(:,3)>=.05 & data(:,3)<=.95),'Duty bound failed.');
    writetable(array2table([t,data],'VariableNames', ...
        {'time_s','voltage_V','current_A','dprime','reference_V'}), ...
        fullfile(outputFolder,names(k)+".csv"));
end
disp('PASS: delivered Simulink model, four scenarios and duty bounds');
end
