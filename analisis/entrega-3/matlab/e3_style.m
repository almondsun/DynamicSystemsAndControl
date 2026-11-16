function S = e3_style(mode)
%E3_STYLE  Colours and sizes shared by the Entrega 3 figures.
%   mode = 'slides' (default): pixel-sized figures, 15 pt text, exported at 2x
%   mode = 'report'          : IEEE column-sized figures, 8 pt text, vector PDF
%   Colours follow the Entrega 1 deck (orange #F19820, teal #0097B2, black).
if nargin < 1, mode = 'slides'; end
hex = @(h) sscanf(h(2:end), '%2x%2x%2x', [1 3])/255;
S.mode   = mode;
S.ink    = hex('#111111');
S.body   = hex('#333333');
S.paper  = [1 1 1];
S.axbg   = [1 1 1];
S.teal   = hex('#0097B2');
S.orange = hex('#F19820');
S.raw    = hex('#B9C5CC');
S.gray   = hex('#7D8B95');
S.grid   = hex('#DDDDDD');
S.font   = 'Arial';
switch mode
    case 'slides'
        S.fs = 15; S.lw = 2.2; S.lw2 = 1.6; S.ms = 8;
    case 'report'
        S.font = 'Helvetica';
        S.fs = 8; S.lw = 1.1; S.lw2 = 0.8; S.ms = 4;
    otherwise
        error('mode must be slides or report');
end
end
