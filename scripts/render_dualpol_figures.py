#!/usr/bin/env python3
"""Export scientific figures from reviewed rows using isolated Matplotlib; no app dependency."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,Normalize
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

def run(destination):
    if destination.exists():raise FileExistsError('Choose a new figure output directory')
    destination.mkdir(parents=True)
    config=json.loads((ROOT/'config.dualpol.json').read_text());palette=np.asarray(json.loads((ROOT/'data/palettes/v1/cividis.json').read_text()));vik=ListedColormap(json.loads((ROOT/'data/palettes/v1/vik.json').read_text()))
    plt.rcParams.update({'font.size':14,'axes.titlesize':17,'axes.labelsize':14,'figure.facecolor':'#10202d','axes.facecolor':'#10202d','text.color':'#e6eff7','axes.labelcolor':'#cadbe8','xtick.color':'#cadbe8','ytick.color':'#cadbe8','axes.edgecolor':'#9cafc0','savefig.facecolor':'#10202d','svg.fonttype':'none'})
    fig,axes=plt.subplots(2,2,figsize=(18,12),layout='constrained')
    for ax,case in zip(axes.flat,config['source_cases']):
        directory=ROOT/f'web/public/cases/{case}/dualpol-v1';m=json.loads((directory/'manifest.json').read_text());s=json.loads((directory/'sensitivity.json').read_text());offsets=s['offsets_db']
        for i,o in enumerate(s['observations']):
            area=np.asarray(o['candidate_area_km2']);y=np.diag(area)
            ax.plot(offsets,y,label=o['timestamp'][:10],color=palette[round((.25+.7*i/max(1,len(s['observations'])-1))*255)],marker=['o','s','^','D','v','P'][i],linestyle=['-','--','-.',':','--','-.'][i],linewidth=2)
        ax.axvline(0,color='#d9c792',linestyle=':',linewidth=1.5);ax.set_ylim(bottom=0);ax.set_xticks(offsets);ax.set_xlabel('Offset to both HH and HV cutoffs (dB)');ax.set_ylabel('Radar-dark candidate area (km²)');ax.set_title(case.replace('_',' ').title()+' · fixed common-valid footprint',loc='left',pad=12)
        ax.grid(axis='y',alpha=.15);ax.legend(fontsize=11,ncol=2,frameon=False,labelcolor='#d8e7f0')
    fig.suptitle('Threshold sensitivity · illustrative HH ≤ −17, HV ≤ −24 dB\nNo threshold tuning or classification accuracy inferred',fontsize=23)
    fig.savefig(destination/'threshold_sensitivity.png',dpi=150);fig.savefig(destination/'threshold_sensitivity.svg');plt.close(fig)
    fig,axes=plt.subplots(4,3,figsize=(16,19),layout='constrained')
    for row,case in zip(axes,config['source_cases']):
        directory=ROOT/f'web/public/cases/{case}/dualpol-v1';m=json.loads((directory/'manifest.json').read_text());first=m['observations'][0];last=m['observations'][-1]
        for ax,o,title in [(row[0],first,'First visit · fixed RGB'),(row[1],last,'Last visit · fixed RGB')]:
            ax.imshow(Image.open(directory/o['layers']['composite']));ax.set_title(title+'\n'+o['timestamp'][:10],fontsize=15);ax.set_xticks([]);ax.set_yticks([])
        row[0].set_ylabel(case.replace('_',' ').title(),fontsize=16)
        row[2].imshow(Image.open(directory/last['layers']['cpr_baseline']));row[2].set_title('ΔCPR from first visit · −8 to +8 dB\nVik centred at 0; no physical cause assigned',fontsize=13);row[2].set_xticks([]);row[2].set_yticks([])
    fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(-8,8),cmap=vik),ax=axes[:,2],shrink=.6,label='ΔCPR · dB')
    fig.suptitle('TerraPulse · diagonal-only evidence\nR = HH [−30, 0] · G = HV [−40, −5] · B = HH−HV [0, 20] dB',fontsize=21)
    fig.savefig(destination/'dualpol_atlas.png',dpi=120);plt.close(fig)
    (destination/'README.md').write_text('Static scientific figure QA only. Native values, masks and common support are verified by src.compute.validate_dualpol. RGB is descriptive and is not perceptually uniform scalar data. Browser UI remains unverified. Source rows: web/public/cases/*/dualpol-v1/sensitivity.json and manifest.json. Matplotlib '+matplotlib.__version__+'.\n')
    print(destination)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'reports/phase2_2026_11_02/figures');args=parser.parse_args();run(args.output)
