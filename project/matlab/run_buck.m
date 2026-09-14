function results = run_buck(outputFolder)
%RUN_BUCK Averaged-model validation, without clearing the user's workspace.
arguments
    outputFolder (1,1) string = ""
end
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
if outputFolder == ""
    outputFolder = string(tempname(fullfile(root,'artifacts')));
end
assert(~isfolder(outputFolder),'Choose a new output folder.');
mkdir(outputFolder);
p = buck_parameters();
s = tf('s');
K = p.Kp+p.Ki/s;
T = feedback(K*p.Gd,1);
assert(isstable(T),'Continuous closed loop unstable.');
[gm,pm,wgm,wpm] = margin(K*p.Gd);
results.parameters = rmfield(p,{'Gd','Gdp'});
results.poles = [real(pole(p.Gd)),imag(pole(p.Gd))];
results.wn_rad_s = 1/sqrt(p.L*p.C);
results.zeta = sqrt(p.L/p.C)/(2*p.R);
results.gain_margin_db = 20*log10(gm);
results.phase_margin_deg = pm;
results.phase_cross_rad_s = wgm;
results.gain_cross_rad_s = wpm;
results.closed_step = stepinfo(T);
z = tf('z',p.Ts);
Kd = p.Kp+p.Ki*p.Ts/(z-1);
Td = feedback(c2d(p.Gd,p.Ts,'zoh')*Kd/z,1);
results.digital_pole_radius = max(abs(pole(Td)));
assert(isstable(Td),'Delayed discrete closed loop unstable.');
t = (0:2e-6:0.02)';
for delta = [-0.1,0.1]
    name = "open_"+string(round(10*delta));
    dp = delta*double(t>=0.01);
    v = p.V0+lsim(p.Gdp,dp,t);
    assert(abs(v(end)-(p.V0-p.Vin*delta))<1e-6,'Open-loop sign/final value failed.');
    writetable(table(t,p.dp0+dp,v,'VariableNames',{'time_s','dprime','voltage_V'}), ...
        fullfile(outputFolder,name+".csv"));
end
names = ["ref_up","ref_down","load_up","load_down"];
refs = [7,5,6,6]; loads = p.R*[1,1,1.2,0.8];
options = odeset('RelTol',1e-8,'AbsTol',1e-10,'MaxStep',p.Ts/10);
for k = 1:4
    [ta,xa] = ode45(@(~,x) dynamics(x,p.V0,p.R,p),[0,0.01], ...
        [p.V0/p.R;p.V0;0],options);
    [tb,xb] = ode45(@(~,x) dynamics(x,refs(k),loads(k),p),[0.01,0.03], ...
        xa(end,:)',options);
    time = [ta;tb(2:end)]; x = [xa;xb(2:end,:)];
    ref = p.V0+(refs(k)-p.V0)*double(time>=0.01);
    duty = min(p.dmax,max(p.dmin,p.dp0+p.Kp*(ref-x(:,2))+x(:,3)));
    err = x(time>=0.025,2)-refs(k);
    results.cases.(names(k)).final_error_V = abs(x(end,2)-refs(k));
    results.cases.(names(k)).tail_max_error_V = max(abs(err));
    results.cases.(names(k)).peak_deviation_V = max(abs(x(time>=0.01,2)-refs(k)));
    assert(max(abs(err))<0.02,'Steady-state specification failed.');
    writetable(table(time,x(:,1),x(:,2),ref,1-duty, ...
        'VariableNames',{'time_s','current_A','voltage_V','reference_V','dprime'}), ...
        fullfile(outputFolder,names(k)+".csv"));
end
results.robust_cases = 0;
for lscale = [0.8,1,1.2]
    for cscale = [0.8,1,1.2]
        for rscale = [0.8,1,1.2]
            G = p.Vin/(p.L*lscale*p.C*cscale*s^2+p.L*lscale/(p.R*rscale)*s+1);
            assert(isstable(feedback(G*K,1)),'Robustness grid unstable.');
            assert(isstable(feedback(c2d(G,p.Ts,'zoh')*Kd/z,1)), ...
                'Discrete robustness grid unstable.');
            results.robust_cases = results.robust_cases+1;
        end
    end
end
results.validation = 'PASS: signs, final values, 4 closed-loop cases, 27 parameter combinations';
save(fullfile(outputFolder,'results.mat'),'results','p','T','Td');
fid = fopen(fullfile(outputFolder,'results.json'),'w');
assert(fid>=0,'Cannot create results.json');
cleanup = onCleanup(@() fclose(fid));
fprintf(fid,'%s',jsonencode(results,PrettyPrint=true));
disp(results);
fprintf('OUTPUT_FOLDER=%s\n',outputFolder);
end

function dx = dynamics(x,ref,R,p)
error = ref-x(2);
raw = p.dp0+p.Kp*error+x(3);
duty = min(p.dmax,max(p.dmin,raw));
integralRate = p.Ki*error;
if (raw>=p.dmax && error>0) || (raw<=p.dmin && error<0)
    integralRate = 0;
end
dx = [(p.Vin*duty-x(2))/p.L;(x(1)-x(2)/R)/p.C;integralRate];
end
