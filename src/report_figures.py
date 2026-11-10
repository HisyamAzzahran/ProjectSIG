"""Readable report figures derived from actual supplied geometry and computed CSVs."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from .data_loader import ROOT,load_data


def make_report_figures(root=ROOT):
    root=Path(root);folder=root/'outputs/reports/figures';folder.mkdir(parents=True,exist_ok=True)
    zones,points,roads=load_data(root)
    plt.rcParams.update({'font.family':'Times New Roman','font.size':14,'axes.titlesize':17,
                         'text.color':'black','axes.labelcolor':'black','xtick.color':'black',
                         'ytick.color':'black','axes.titlecolor':'black','figure.facecolor':'white'})
    def save(fig,name):
        fig.savefig(folder/name,dpi=190,bbox_inches='tight',facecolor='white');plt.close(fig)
    def map_result(frame,column,name,title,cmap='YlGnBu',symmetric=False,highlight=False):
        fig,ax=plt.subplots(figsize=(7.3,6.5));j=zones.merge(frame,on='zone_id',suffixes=('_source',''))
        kws={}
        if symmetric:
            limit=float(abs(j[column]).max());kws={'vmin':-limit,'vmax':limit}
        j.plot(column=column,ax=ax,cmap=cmap,edgecolor='#999999',linewidth=.3,legend=True,
               legend_kwds={'label':'Satuan model per zona','shrink':.7},**kws)
        if highlight:roads.loc[roads.TYPE=='r7'].plot(ax=ax,color='black',linewidth=1.1)
        ax.set_title(title,pad=12,fontweight='bold');ax.set_axis_off();save(fig,name)
    frames={n:pd.read_csv(root/'outputs/tables'/f'{n}.csv') for n in pd.read_csv(root/'outputs/tables/scenario_comparison_extended.csv').scenario}
    fig,ax=plt.subplots(figsize=(7.5,6.5));zones.plot(ax=ax,color='#edf0f2',edgecolor='#6d747a',linewidth=.5);roads.plot(ax=ax,color='#303b43',linewidth=.55)
    cbd=points.loc[points.BEMP_CBD.idxmax(),'geometry'];ax.plot(cbd.x,cbd.y,'*',color='black',markersize=12);ax.annotate('CBD: zona 71',(cbd.x,cbd.y),xytext=(10,18),textcoords='offset points',fontsize=14,bbox=dict(facecolor='white',edgecolor='black',alpha=.9))
    xmin,ymin,xmax,ymax=zones.total_bounds;x0=xmin+500;y0=ymin+450;ax.plot([x0,x0+2000],[y0,y0],color='black',linewidth=3);ax.text(x0+1000,y0+120,'2 km proyeksi',ha='center',fontsize=13)
    ax.set_title('Struktur kota hipotetis: 136 zona',fontweight='bold',pad=12);ax.axis('off');save(fig,'01_city.png')
    fig,ax=plt.subplots(figsize=(8,3.8));ax.set(xlim=(0,10),ylim=(0,5));ax.axis('off')
    boxes=[(.2,2.8,2.8,1.2,'Pekerjaan dasar (B)\nditetapkan dari luar'),(3.6,2.8,2.8,1.2,'Penduduk (P)\nmengikuti akses kerja'),(7,2.8,2.8,1.2,'Pekerjaan jasa (S)\nmemenuhi kebutuhan')]
    for x,y,w,h,text in boxes:
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.10',facecolor='white',edgecolor='black',linewidth=1.4));ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=14)
    for a,b in [((3.05,3.4),(3.5,3.4)),((6.5,3.4),(6.9,3.4))]:ax.add_patch(FancyArrowPatch(a,b,arrowstyle='->',mutation_scale=18,color='black'))
    ax.add_patch(FancyArrowPatch((8.4,2.65),(5.0,2.65),connectionstyle='arc3,rad=-.65',arrowstyle='->',mutation_scale=18,color='black'))
    ax.text(6.7,1.20,'Pekerjaan jasa juga mendukung penduduk',ha='center',fontsize=14)
    ax.text(5,.3,'Jaringan jalan menentukan biaya perjalanan dan pembagian antarzona.',ha='center',fontsize=14)
    save(fig,'02_model_logic.png')
    map_result(frames['baseline_uniform'],'population','03_baseline_population.png','Penduduk baseline: pekerjaan dasar merata')
    map_result(frames['baseline_uniform'],'service_employment','04_baseline_services.png','Pekerjaan jasa baseline')
    duration=pd.read_csv(root/'data/matrices/od_duration_matrix.csv',index_col=0).to_numpy()
    fig,ax=plt.subplots(figsize=(7.5,5.8));im=ax.imshow(duration,cmap='magma',origin='lower',extent=[.5,136.5,.5,136.5]);fig.colorbar(im,ax=ax,label='Durasi jaringan (menit model)');ax.set(xlabel='ID zona tujuan',ylabel='ID zona asal',title='Matriks OD: 18.496 pasangan zona');save(fig,'05_od_heatmap.png')
    names=['baseline_uniform','cbd_employment','low_friction','high_friction','beltway','cbd_high_friction','cbd_beltway','polycentric_centers']
    labels=['Uniform (arsip)','CBD tunggal','Friction 0,5','Friction 2','Beltway','CBD + friction 2','CBD + beltway','Tiga pusat (mandiri)']
    summary=pd.read_csv(root/'outputs/tables/scenario_comparison_extended.csv').set_index('scenario').loc[names]
    fig,ax=plt.subplots(figsize=(7.8,5.5));ax.barh(labels,summary.mean_population_radius_m/1000,color=['#788c9b']*7+['#bb8d49']);ax.invert_yaxis();ax.set_xlabel('Radius rata-rata berbobot penduduk (km proyeksi)');ax.set_title('Perbandingan delapan skenario',fontweight='bold');ax.grid(axis='x',alpha=.2);save(fig,'06_scenario_radius.png')
    fig,ax=plt.subplots(figsize=(7.5,5.5))
    for name,label,style in [('low_friction','Friction 0,5','--'),('baseline_uniform','Friction 1','-'),('high_friction','Friction 2',':')]:
        f=frames[name].groupby('ring').population.mean();ax.plot(f.index,f.values,linestyle=style,marker='o',label=label)
    ax.set(xlabel='Cincin (0 = CBD)',ylabel='Penduduk rata-rata per zona',title='Sensitivitas hambatan perjalanan');ax.legend();ax.grid(alpha=.2);save(fig,'07_friction_profile.png')
    map_result(frames['beltway'],'population_change','08_beltway_change.png','Dampak beltway terhadap baseline','RdBu_r',True,True)
    history=json.loads((root/'outputs/logs/convergence_history.json').read_text())['baseline_uniform']
    fig,ax=plt.subplots(figsize=(7.4,4.8));ax.semilogy(np.arange(1,len(history)+1),history,color='black');ax.axhline(1e-11,color='#777777',linestyle='--');ax.set(xlabel='Iterasi numerik (bukan tahun)',ylabel='Perubahan maksimum penduduk',title='Konvergensi pemeriksaan independen');ax.grid(alpha=.2);save(fig,'09_convergence.png')
    custom=frames['polycentric_centers'];centers=pd.read_csv(root/'outputs/tables/custom_centers.csv')
    fig,ax=plt.subplots(figsize=(7.3,6.5));zones.merge(custom,on='zone_id').plot(column='basic_employment',cmap='YlOrBr',ax=ax,edgecolor='#999999',linewidth=.4,legend=True,legend_kwds={'label':'Pekerjaan dasar (satuan model)','shrink':.7})
    for c in centers.itertuples():
        ax.plot(c.x,c.y,marker='*',color='black',markersize=10);ax.annotate(f'{c.role}\nZona {c.zone_id}: {100*c.share:.0f}%',(c.x,c.y),xytext=(0,22),textcoords='offset points',ha='center',fontsize=14,bbox=dict(facecolor='white',edgecolor='#777777',alpha=.9))
    ax.set_title('Rancangan mandiri: CBD 40% dan satelit 30%–30%',fontweight='bold',pad=12);ax.axis('off');save(fig,'10_custom_jobs.png')
    map_result(custom,'population','11_custom_population.png','Penduduk pada kota tiga pusat')
    change=pd.read_csv(root/'outputs/tables/custom_change_vs_cbd.csv');map_result(change,'population_change_vs_cbd','12_custom_delta.png','Tiga pusat dikurangi CBD tunggal','RdBu_r',True)
    fig,ax=plt.subplots(figsize=(7.8,5));x=np.arange(3);ids=centers.zone_id.tolist();cbd=frames['cbd_employment'].set_index('zone_id');new=custom.set_index('zone_id')
    ax.bar(x-.19,cbd.loc[ids,'population'],.38,label='CBD tunggal',color='#788c9b');ax.bar(x+.19,new.loc[ids,'population'],.38,label='Tiga pusat',color='#bb8d49');ax.set_xticks(x,[f'{c.role}\nZona {c.zone_id}' for c in centers.itertuples()]);ax.set_ylabel('Penduduk (satuan model)');ax.set_title('Apa yang berubah di tiga pusat?');ax.legend();save(fig,'13_custom_centers.png')
    return folder


if __name__=='__main__':print(make_report_figures())
