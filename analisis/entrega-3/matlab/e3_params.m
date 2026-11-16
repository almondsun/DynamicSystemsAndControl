function p = e3_params(varargin)
%E3_PARAMS  Parameters of the Rev C buck board (Entrega 3 design model).
%   p = e3_params('Name', value, ...) overrides any field. Ts, D0 and the
%   ADC step are recomputed after the overrides.
%
%   Sources: BOM_RevC.csv, BRINGUP_AND_TEST_GUIDE.md section 6, datasheets of
%   SRR1280-331K (DCR 0.6 ohm max each), SS34, AOD4184A. The driver delays
%   come from the ngspice simulation of the Rev C driver (td_on 0.09 us,
%   td_off 0.32 us).
p = struct( ...
    'Vin',   12, ...            % V    bench supply
    'Vf',    0.40, ...          % V    SS34 drop at ~1 A (small-signal design model)
    'V0',    0.30, ...          % V    SS34 knee  (V0 + Rd*1 A = Vf)
    'Rd',    0.10, ...          % ohm  SS34 slope resistance
    'Rds',   0.007, ...         % ohm  AOD4184A on-resistance
    'L',     660e-6, ...        % H    2 x SRR1280-331K in series
    'rL',    1.2, ...           % ohm  2 x 0.6 ohm (datasheet max DCR)
    'C',     20e-6, ...         % F    2 x 10 uF X5R 1206 (nominal, no DC bias)
    'rC',    1.5e-3, ...        % ohm  ESR of the two ceramics in parallel
    'R',     6, ...             % ohm  nominal load: 7.2 || 36
    'k',     0.25, ...          % -    divider 30 k / 10 k
    'tau',   7.5e3*4.7e-9, ...  % s    ADC RC filter: 7.5 kohm Thevenin, 4.7 nF
    'fs',    20e3, ...          % Hz   PWM frequency = control rate
    'nbits', 12, ...            % -    ADC resolution
    'Vadc',  3.3, ...           % V    ADC reference
    'ARR',   4000, ...          % -    timer counts per period (80 MHz / 20 kHz)
    'tdrv',  0.23e-6, ...       % s    driver delay mismatch, lengthens the on-time
    'dmin',  0, ...             % -    duty clamp (firmware)
    'dmax',  0.85, ...
    'Vo',    6);                % V    nominal output
for i = 1:2:numel(varargin)
    p.(varargin{i}) = varargin{i+1};
end
p.Ts  = 1/p.fs;
p.ARR = round(80e6/p.fs);
p.D0  = (p.Vo*(1 + p.rL/p.R) + p.Vf)/(p.Vin + p.Vf);   % operating duty (averaged model)
p.lsb = p.Vadc/(2^p.nbits - 1)/p.k;                     % ADC step referred to vo
end
