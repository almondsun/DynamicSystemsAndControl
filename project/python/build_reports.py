"""Build IEEE LaTeX reports from saved results, preserving the report CLI."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import numpy as np
from scipy.integrate import cumulative_trapezoid
from report_content import AUTHORS, REFS, reports

ROOT = Path(__file__).resolve().parents[2]
PREAMBLE = r'''\RequirePackage[T1]{fontenc}
\documentclass[conference,letterpaper]{IEEEtran}
\usepackage[spanish,es-nodecimaldot,es-tabla,es-noshorthands]{babel}
\usepackage{amsmath,amssymb,siunitx,booktabs,tabularx}
\usepackage{tikz,circuitikz,pgfplots}
\usetikzlibrary{arrows.meta,positioning,babel}
\usepgfplotslibrary{groupplots}
\pgfplotsset{compat=1.18}
\usepackage{float}
\usepackage[nospread]{flushend}
\usepackage[hidelinks]{hyperref}
\raggedbottom
\interdisplaylinepenalty=2500
\setlength{\emergencystretch}{1em}
\newcolumntype{Y}{>{\centering\arraybackslash}X}
\newcolumntype{L}{>{\raggedright\arraybackslash}X}
\newcommand{\plotstyle}{ }
\begin{document}
\special{pdf:minorversion 7}
'''

DIAGRAMS = {
'power': r'''\resizebox{\columnwidth}{!}{\begin{circuitikz}[american,font=\small]
\draw (0,0) node[ground]{} to[V,invert,l=$12\,\mathrm{V}$] (0,3) -- (1,3)
node[nmos,rotate=90,anchor=D](M){};
\draw (M.S) -- (3,3) node[circ,label=above:$sw$]{} to[L,l=$660\,\mu\mathrm{H}$] (5,3)
to[R,l=$r_L$] (7,3) node[circ,label=above:$v_o$]{} -- (10,3);
\draw (3,0) node[ground]{} to[D,l=$D_f$] (3,3);
\draw (7,3) to[R,l=$r_C$] (7,1.6) to[C,l=$20\,\mu\mathrm{F}$] (7,0) node[ground]{};
\draw (8.5,3) to[R,l=$6\,\Omega$] (8.5,0) node[ground]{};
\draw (10,3) to[R,l=$30\,\mathrm{k}\Omega$] (10,1.5) node[circ,label=right:$v_s$]{} to[R,l=$10\,\mathrm{k}\Omega$] (10,0) node[ground]{};
\draw (M.G) -- ++(0,-.4) node[below]{$g$};
\end{circuitikz}}''',
'driver': r'''\resizebox{\columnwidth}{!}{\begin{circuitikz}[american,font=\small]
\draw (0,4) node[left]{$V_{\mathrm{in}}$} to[D,l=1N4148] (3,4) node[circ,label=above:$boot$]{} -- (7.4,4);
\draw (7.4,4) to[C,l=$1\,\mu\mathrm{F}$] (7.4,2.4) node[right]{$sw$};
\draw (3,4) to[R,l=$1.2\,\mathrm{k}\Omega$] (3,2.3) -- (3,2);
\node[npn,anchor=C] (Q1) at (3,2) {$Q_1$};
\draw (Q1.E) -- ++(0,-.25) node[ground]{};
\draw (Q1.B) to[R,l_=$1\,\mathrm{k}\Omega$] ++(-2,0) node[left]{PWM};
\node[npn] (Q2) at (5.2,3.1) {$Q_2$};
\node[pnp] (Q3) at (5.2,.7) {$Q_3$};
\draw (Q2.C) |- (3,4);
\draw (Q3.C) -- ++(0,-.5) node[ground]{};
\draw (Q2.B) -- (3.7,3.1) -- (3.7,.7) -- (Q3.B);
\draw (3,2.3) -- (3.7,2.3) node[circ]{};
\draw (Q2.E) -- (6,1.9) -- (Q3.E);
\draw (6,1.9) -- (7,1.9) node[right]{$g$};
\end{circuitikz}}''',
'control': r'''\begin{tikzpicture}[font=\footnotesize,>=Stealth,
b/.style={draw,align=center,minimum height=7mm}]
\node[draw,circle,inner sep=1pt] (sum) at (0,0) {$\Sigma$};
\node[b] (pi) at (1.15,0) {PI};
\node[b] (inv) at (2.45,0) {$1-d$};
\node[b] (pwm) at (4.2,0) {PWM\\driver};
\node[b] (plant) at (6.05,0) {Buck};
\draw[->] (-.6,0) node[left]{$r$} -- (sum);
\draw[->] (sum) -- node[above]{$e$} (pi);
\draw[->] (pi) -- node[above]{$d$} (inv);
\draw[->] (inv) -- node[above]{$d^{\prime}$} (pwm);
\draw[->] (pwm) -- node[above]{$d$} (plant);
\draw[->] (plant) -- (6.85,0) node[right]{$v_o$};
\draw[->] (6.65,0) |- (3.4,-1) node[below]{sensor y promedio} -| node[pos=.97,left]{$-$} (sum);
\end{tikzpicture}''',
'timing': r'''\begin{tikzpicture}[font=\footnotesize,>=Stealth]
\draw[->] (0,0) -- (7.6,0) node[right]{$t$};
\foreach \x/\lab in {0/{k-1},2.4/k,4.8/{k+1},7.2/{k+2}} {
\draw (\x,-.1)--(\x,.1) node[above]{$\lab$};}
\draw[<->] (0,-.5)--node[below]{media $\bar v_{k-1}$}(2.4,-.5);
\node[align=center] at (2.4,-1.35) {cálculo\\$d_k^{\mathrm{cmd}}$};
\draw[->] (2.4,-1.8)--node[below]{precarga: $T_s$}(4.8,-1.8);
\draw[<->] (4.8,-.5)--node[below]{$d_k^{\mathrm{cmd}}$ aplicado}(7.2,-.5);
\end{tikzpicture}'''
}

def extrema_indices(values, bins=350):
    """Retain endpoints and each bin's extrema for display only."""
    if len(values) <= bins*2:
        return np.arange(len(values))
    keep={0,len(values)-1}
    for chunk in np.array_split(np.arange(len(values)),bins):
        keep.update([int(chunk[np.argmin(values[chunk])]),int(chunk[np.argmax(values[chunk])])])
    return np.array(sorted(keep))

def save_curve(path,t,v):
    idx=extrema_indices(v)
    np.savetxt(path,np.c_[t[idx]*1000,v[idx]],delimiter=',',header='t,v',comments='')

def data_assets(out,matlab,analysis,m,a):
    """Use original integration for means; only plotted traces are reduced."""
    provenance={}
    data=out/'data'; data.mkdir()
    for case in ['open_up','open_down','ref_up','ref_down','load_up','load_down']:
        mf=matlab/({'open_up':'open_1','open_down':'open_-1'}.get(case,case)+'.csv')
        model=np.genfromtxt(mf,delimiter=',',names=True)
        mask=model['time_s']>=.008
        save_curve(data/f'{case}_model.csv',model['time_s'][mask],model['voltage_V'][mask])
        pf=analysis/f'{case}_pwm.csv'
        pwm=np.genfromtxt(pf,delimiter=',',names=True)
        save_curve(data/f'{case}_pwm.csv',pwm['time_s'],pwm['voltage_cycle_mean_V'])
        rawfile=analysis/case/'waveform.txt'
        if not rawfile.exists():
            raise FileNotFoundError(f'Raw waveform needed for ripple figure: {rawfile}. Use the full saved simulation directory.')
        raw=np.loadtxt(rawfile,skiprows=1,usecols=(0,1))
        edges=np.arange(301)*m['parameters']['Ts']
        integ=cumulative_trapezoid(raw[:,1],raw[:,0],initial=0)
        means=np.diff(np.interp(edges,raw[:,0],integ))/m['parameters']['Ts']
        if not np.isclose(means[-50:].mean(),a['circuit'][case]['mean_final_V'],atol=1e-8,rtol=0):
            raise ValueError(f'Waveform and saved circuit metrics disagree: {case}')
        if not np.isclose(pwm['voltage_cycle_mean_V'][-50:].mean(),a['switched'][case]['mean_final_V'],atol=1e-8,rtol=0):
            raise ValueError(f'PWM data and saved metrics disagree: {case}')
        save_curve(data/f'{case}_circuit.csv',(edges[:-1]+edges[1:])/2,means)
        mask=(raw[:,0]>=.029)&(raw[:,0]<=.0295)
        save_curve(data/f'{case}_ripple.csv',raw[mask,0],raw[mask,1])
        provenance[case]={str(f.resolve()):hashlib.sha256(f.read_bytes()).hexdigest() for f in [mf,pf,rawfile]}
    p=m['parameters']; omega=np.logspace(1,5,500); s=1j*omega
    loop=(p['Kp']+p['Ki']/s)*p['Vin']/(p['L']*p['C']*s*s+p['L']/p['R']*s+1)
    np.savetxt(data/'bode.csv',np.c_[omega,20*np.log10(abs(loop)),np.angle(loop,deg=True)],delimiter=',',header='w,mag,phase',comments='')
    return provenance

def plot_tex(case):
    if case=='bode':
        return r'''\begin{tikzpicture}\begin{groupplot}[group style={group size=1 by 2,vertical sep=9mm},width=.96\columnwidth,height=3.6cm,scale only axis=false,xmode=log,xmin=10,xmax=100000,grid=major,tick label style={font=\scriptsize},label style={font=\footnotesize}]
\nextgroupplot[ylabel={Magnitud (dB)}]
\addplot[blue,thick] table[x=w,y=mag,col sep=comma]{data/bode.csv};
\addplot[gray,dashed] coordinates {(10,0)(100000,0)};
\draw[dashed,orange] (axis cs:1000,-50)--(axis cs:1000,45);
\nextgroupplot[ylabel={Fase ($^\circ$)},xlabel={$\omega$ ($\mathrm{rad/s}$)}]
\addplot[blue,thick] table[x=w,y=phase,col sep=comma]{data/bode.csv};
\addplot[gray,dashed] coordinates {(10,-180)(100000,-180)};
\draw[dashed,orange] (axis cs:1000,-180)--(axis cs:1000,-40);
\end{groupplot}\end{tikzpicture}'''
    target={'open_up':4.8,'open_down':7.2,'ref_up':7,'ref_down':5,'load_up':6,'load_down':6}[case]
    openloop=case.startswith('open')
    band=.12 if case.startswith('load') else .02
    curves=''
    for suffix,color,style in [('model','blue','solid'),('pwm','orange','dashed'),('circuit','black','densely dotted')]:
        curves+=fr'\addplot[{color},{style},thick] table[x=t,y=v,col sep=comma]{{data/{case}_{suffix}.csv}};'+'\n'
    curves+=r'\legend{Promediado,PWM digital,Circuito}' if not openloop else r'\legend{Modelo ideal,PWM ideal,Circuito}'
    if openloop:
        curves+=fr'\addplot[gray,dashdotted,forget plot] coordinates {{(10,{target})(30,{target})}};'
    else:
        for val in [target-band,target+band]:
            curves+=fr'\addplot[gray,dashdotted,forget plot] coordinates {{(10,{val})(30,{val})}};'
    return r'''\begin{tikzpicture}\begin{groupplot}[group style={group size=1 by 2,vertical sep=12mm},width=.96\columnwidth,height=3.8cm,grid=major,tick label style={font=\scriptsize},label style={font=\footnotesize}]
\nextgroupplot[xmin=8,xmax=24,xlabel={$t$ (ms)},ylabel={$\bar v_o$ (V)},legend style={font=\scriptsize,at={(.5,1.02)},anchor=south,legend columns=3,/tikz/every even column/.append style={column sep=2pt}}]
''' + curves + r'''
\nextgroupplot[xmin=29,xmax=29.5,xlabel={$t$ (ms)},ylabel={$v_o$ (V)},scaled x ticks=false,xtick={29,29.2,29.4}]
''' + fr'\addplot[black,thin] table[x=t,y=v,col sep=comma]{{data/{case}_ripple.csv}};' + r'\end{groupplot}\end{tikzpicture}'

def document(number,title,subtitle,abstract,blocks):
    authors=r'\IEEEauthorblockN{'+r', '.join(name for name,_ in AUTHORS[:2])+r'\\'+r', '.join(name for name,_ in AUTHORS[2:])+r'}'+'\n'
    authors+=r'\IEEEauthorblockA{Universidad Nacional de Colombia, Sede Manizales\\'+r'\texttt{'+AUTHORS[0][1]+r'}, \texttt{'+AUTHORS[1][1]+r'}\\\texttt{'+AUTHORS[2][1]+r'}, \texttt{'+AUTHORS[3][1]+r'}}'
    tex=PREAMBLE+fr'\title{{{title}}}\author{{{authors}}}'+'\n'
    tex+=r'\hypersetup{pdftitle={'+title+r'},pdfauthor={'+', '.join(x[0] for x in AUTHORS)+r'}}\maketitle'+'\n'
    tex+=fr'\begin{{center}}\small Entrega {number}: {subtitle}\end{{center}}'+'\n'+fr'\begin{{abstract}}{abstract}\end{{abstract}}'+'\n'
    md=[f'# {title}',f'Entrega {number}: {subtitle}',*[f'{n} — {e}' for n,e in AUTHORS],'Universidad Nacional de Colombia, Sede Manizales','## Resumen',abstract]
    appendix = False
    for block in blocks:
        if block.kind=='section':
            tex+=fr'\section{{{block.text}}}'+'\n'; md+=['## '+block.text]
        elif block.kind=='appendix':
            tex+=fr'\appendices\section{{{block.text}}}\begingroup\raggedright'+'\n'; md+=['## Apéndice: '+block.text]
            appendix = True
        elif block.kind=='paragraph':
            tex+=block.text+'\n\n'; md+=[block.text]
        elif block.kind=='equation':
            tex+=fr'\begin{{equation}}\label{{eq:{block.label}}}{block.text}\end{{equation}}'+'\n'
            md+=['$$\n'+block.text+'\n$$']
        elif block.kind=='table':
            cols=len(block.rows[0]); spec='L'+'Y'*(cols-1)
            tex+=fr'\begin{{table}}[H]\caption{{{block.text}}}\label{{tab:{block.label}}}\centering\footnotesize\setlength{{\tabcolsep}}{{2pt}}\renewcommand{{\arraystretch}}{{1.18}}\begin{{tabularx}}{{\columnwidth}}{{{spec}}}\toprule'+'\n'
            tex+=' & '.join(block.rows[0])+r'\\\midrule'+'\n'
            tex+='\n'.join(' & '.join(row)+r'\\' for row in block.rows[1:])
            tex+=r'\bottomrule\end{tabularx}\end{table}'+'\n'
            md += ['*'+block.text+'*','| '+' | '.join(block.rows[0])+' |','| '+' | '.join(['---']*cols)+' |',*['| '+' | '.join(row)+' |' for row in block.rows[1:]]]
        elif block.kind=='figure':
            wide=block.label=='pcb-power'
            width=r'\textwidth' if wide else r'\columnwidth'
            art=(fr'\includegraphics[width={width}]{{assets/{block.asset}}}'
                 if block.asset else DIAGRAMS.get(block.label) or plot_tex(block.label))
            if block.label in ['control','timing']:
                art=r'\resizebox{\columnwidth}{!}{'+art+'}'
            env='figure*' if wide else 'figure'
            placement='t' if wide else 'H'
            tex+=fr'\begin{{{env}}}[{placement}]\centering'+art+fr'\caption{{{block.text}}}\label{{fig:{block.label}}}\end{{{env}}}'+'\n'
            md += [f'*Figura ({block.label}): {block.text}*',
                   f'![{block.label}](assets/{block.asset})' if block.asset else
                   f'Fuente vectorial en entrega_{number}.tex; datos en data/.']
        else: raise ValueError(block.kind)
    if appendix:
        tex+='\\par\\endgroup\n'
    keys=list(dict.fromkeys(re.findall(r'\\cite\{([^}]+)\}',tex)))
    tex+=r'\begin{thebibliography}{9}'+'\n'
    md+=['## Referencias']
    for i,key in enumerate(keys,1):
        tex+=fr'\bibitem{{{key}}}{REFS[key]}'+'\n'; md+=[f'[{i}] {REFS[key]}']
    tex+=r'\end{thebibliography}\end{document}'+'\n'
    markdown='\n\n'.join(md)+'\n'
    # Resolve prose references in the companion; display math stays verbatim.
    label_numbers={}
    for kind,prefix in [('equation','eq'),('figure','fig'),('table','tab')]:
        for i,block in enumerate((b for b in blocks if b.kind==kind),1):
            label_numbers[f'{prefix}:{block.label}']=str(i)
    markdown=re.sub(r'\\cite\{([^}]+)\}',lambda x:f'[{keys.index(x[1])+1}]',markdown)
    markdown=re.sub(r'\\eqref\{([^}]+)\}',lambda x:'('+label_numbers[x[1]]+')',markdown)
    markdown=re.sub(r'\\ref\{([^}]+)\}',lambda x:label_numbers[x[1]],markdown)
    markdown=re.sub(r'\\texttt\{([^}]+)\}',lambda x:'`'+x[1].replace(r'\_','_')+'`',markdown)
    markdown=re.sub(r'\\emph\{([^}]+)\}',r'*\1*',markdown)
    markdown=re.sub(r'\\url\{([^}]+)\}',r'\1',markdown)
    return tex,markdown

def validate_numbers(m,a):
    p=m['parameters']
    for name in ['Vin','L','C','R','Ts','Kp','Ki']:
        if not np.isclose(p[name],a['parameters'][name],rtol=1e-12,atol=0):
            raise ValueError(f'Inconsistent source parameter: {name}')
    gain=abs(p['Vin']/(1-p['L']*p['C']*p['wc']**2+1j*p['L']/p['R']*p['wc']))
    assert np.isclose(p['Kp'],1/(gain*np.sqrt(1+(p['wz']/p['wc'])**2)))
    assert np.isclose(m['wn_rad_s'],1/np.sqrt(p['L']*p['C']))
    assert np.isclose(m['zeta'],np.sqrt(p['L']/p['C'])/(2*p['R']))
    assert len(a['circuit'])==6 and len(a['switched'])==6
    assert a['convergence_max_cycle_mean_V']<.005
    return {'plant_magnitude_at_crossover_V':gain,'Kp':p['Kp'],'Ki':p['Ki'],'status':'PASS'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ['matlab-results','analysis-results','output']:
        parser.add_argument('--'+flag,type=Path,required=True)
    parser.add_argument('--tectonic',default=os.environ.get('BUCK_TECTONIC',str(ROOT/'artifacts/buck-tools/tectonic/tectonic')))
    args=parser.parse_args()
    compiler=shutil.which(args.tectonic)
    if not compiler: parser.error('Tectonic missing: set BUCK_TECTONIC or --tectonic; see project/README.md')
    m=json.loads((args.matlab_results/'results.json').read_text())
    a=json.loads((args.analysis_results/'results.json').read_text())
    checks=validate_numbers(m,a)
    args.output.mkdir(parents=True,exist_ok=False)
    provenance=data_assets(args.output,args.matlab_results,args.analysis_results,m,a)
    assets=ROOT/'project/pcb/release/report-assets'
    shutil.copytree(assets,args.output/'assets')
    provenance['hardware_assets']={str(f.relative_to(assets)):hashlib.sha256(f.read_bytes()).hexdigest()
                                   for f in assets.rglob('*') if f.is_file()}
    for n,title,subtitle,abstract,blocks in reports(m,a):
        tex,md=document(n,title,subtitle,abstract,blocks)
        path=args.output/f'entrega_{n}.tex'; path.write_text(tex)
        path.with_suffix('.md').write_text(md)
        result=subprocess.run([compiler,'--keep-logs','--keep-intermediates',path.name],cwd=args.output,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (args.output/f'entrega_{n}.build.log').write_text(result.stdout)
        print(result.stdout,flush=True)
        if result.returncode: raise RuntimeError(f'LaTeX failed: {path}')
        log=path.with_suffix('.log').read_text(errors='replace')
        failures=re.findall(r'^.*(?:Overfull|Missing character|undefined references|undefined on input|Undefined control sequence).*$' ,log,re.M)
        if failures: raise RuntimeError('LaTeX validation failed:\n'+'\n'.join(failures))
    provenance['metrics']={str(f.resolve()):hashlib.sha256(f.read_bytes()).hexdigest() for f in [args.matlab_results/'results.json',args.analysis_results/'results.json']}
    manifest={'engine':subprocess.check_output([compiler,'--version'],text=True).strip(),'validation':checks,'source_sha256':provenance,
      'display_reduction':'Endpoints and bin extrema only; metrics unchanged; ripple detail 29--29.5 ms.',
      'reports':{'1':'simulation; original BJT circuit distinguished from PCB','2':'CAD prepared; laboratory measurements pending','3':'simulation; PCB estimate separately identified','4':'firmware compiled; physical integration and measurements pending'}}
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('PASS: four LaTeX PDFs, editable TeX/Markdown and vector plot data:',args.output)

if __name__=='__main__': main()
