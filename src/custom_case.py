"""Original project-designed study: CBD 40%, western/eastern satellites 30% each.

This is a new hypothetical employment policy, not a workbook parameter claim.
The original seven scenarios and their files are retained unchanged.
"""
from pathlib import Path
from dataclasses import asdict
import json
import numpy as np
import pandas as pd
from .data_loader import ROOT, load_data
from .garin_lowry_model import Parameters, equilibrium
from .validation import validate_result

NAME = 'polycentric_centers'


def design_employment(points):
    """Choose real supplied zones nearest to the two declared policy targets."""
    total = float(points.BEMP_Unif.sum())
    cbd_index = int(np.argmax(points.BEMP_CBD.to_numpy()))
    cbd = points.geometry.iloc[cbd_index]
    xy = np.array([[p.x, p.y] for p in points.geometry])
    indices = [cbd_index]
    for offset in [-3800.0, 3800.0]:
        target = np.array([cbd.x + offset, cbd.y])
        indices.append(int(np.linalg.norm(xy-target, axis=1).argmin()))
    if len(set(indices)) != 3:
        raise ValueError('The satellite targets must identify three different supplied zones')
    basic = np.zeros(len(points), dtype=float)
    weights = [0.4, 0.3, 0.3]
    centers = []
    for i, weight, role in zip(indices, weights, ['CBD', 'Satelit Barat', 'Satelit Timur']):
        basic[i] = total*weight
        centers.append(dict(zone_id=int(points.zone_id.iloc[i]),role=role,share=weight,
                            basic_employment=float(basic[i]),x=float(xy[i,0]),y=float(xy[i,1]),
                            distance_to_cbd_m=float(np.linalg.norm(xy[i]-xy[cbd_index]))))
    return basic, centers


def run_custom_case(root=ROOT, plots=True):
    root = Path(root)
    if not (root/'outputs/tables/scenario_comparison.csv').is_file():
        from .main import run
        run(root, plots=plots)
    zones, points, roads = load_data(root)
    baseline = pd.read_csv(root/'outputs/tables/baseline_uniform.csv')
    monocentric = pd.read_csv(root/'outputs/tables/cbd_employment.csv')
    ids = points.zone_id.to_numpy()
    if not np.array_equal(baseline.zone_id, ids):
        raise ValueError('Baseline ordering differs from the unique supplied zone IDs')
    cost = pd.read_csv(root/'data/matrices/model_cost_matrix.csv',index_col=0)
    cost = cost.loc[ids, [str(i) for i in ids]].to_numpy(dtype=float)
    basic, centers = design_employment(points)
    params = Parameters()
    population, service, diagnostics, history = equilibrium(cost, basic, params)
    frame = baseline[['zone_id','TRACT0_ID','ring','radius_m']].copy()
    frame['basic_employment'] = basic
    frame['population'] = population
    frame['service_employment'] = service
    frame['total_employment'] = basic+service
    frame['population_change'] = population-baseline.population.to_numpy()
    frame['service_change'] = service-baseline.service_employment.to_numpy()
    frame['population_change_pct'] = 100*frame.population_change/baseline.population
    frame['scenario'] = NAME
    validate_result(frame,params)
    folder=root/'data/scenarios'/NAME;folder.mkdir(parents=True,exist_ok=True)
    inputs=dict(scenario=NAME,label='Kota Tiga Pusat: CBD 40% dan Dua Satelit 30%–30%',
                origin='Designed specifically for this project; not an original workbook scenario',
                parameters=asdict(params),speed_column='speed',centers=centers,
                satellite_target_offsets_projected_m=[[-3800.0,0.0],[3800.0,0.0]],
                selection='Nearest existing supplied centroid to each target; unique real zone IDs',
                reference_for_causal_comparison='cbd_employment',
                common_reference_in_extended_tables='baseline_uniform',
                control='Same total basic employment, 30 mph roads, unchanged OD, h=2, e=0.3, a=b=1')
    (folder/'parameters.json').write_text(json.dumps(inputs,indent=2,ensure_ascii=False),encoding='utf8')
    (folder/'solver_diagnostics.json').write_text(json.dumps(diagnostics,indent=2),encoding='utf8')
    frame[['zone_id','basic_employment']].to_csv(folder/'basic_employment.csv',index=False)
    frame.to_csv(root/'outputs/tables'/f'{NAME}.csv',index=False)
    pd.DataFrame(centers).to_csv(root/'outputs/tables/custom_centers.csv',index=False)
    changes = frame[['zone_id','population','service_employment']].copy()
    changes['population_change_vs_cbd'] = population-monocentric.population
    changes['service_change_vs_cbd'] = service-monocentric.service_employment
    changes['population_change_pct_vs_cbd'] = 100*changes.population_change_vs_cbd/monocentric.population
    changes.to_csv(root/'outputs/tables/custom_change_vs_cbd.csv',index=False)
    joined = zones.merge(frame,on='zone_id',validate='one_to_one',suffixes=('_source',''))
    joined = joined.merge(changes[['zone_id','population_change_vs_cbd','service_change_vs_cbd']],on='zone_id',validate='one_to_one')
    joined.to_file(root/'outputs/maps'/f'{NAME}.gpkg',layer='zone_results',driver='GPKG')
    cbd_index=int(np.argmax(points.BEMP_CBD.to_numpy()))
    row=dict(scenario=NAME,**diagnostics,cbd_population=float(population[cbd_index]),
             cbd_population_share=float(population[cbd_index]/population.sum()),
             mean_population_radius_m=float(population@frame.radius_m.to_numpy()/population.sum()),
             population_hhi=float(np.sum((population/population.sum())**2)),
             population_min=float(population.min()),population_max=float(population.max()),
             population_redistributed=float(abs(frame.population_change).sum()/2),
             mean_network_duration_min=float(pd.read_csv(root/'data/matrices/od_duration_matrix.csv',index_col=0).to_numpy().mean()))
    original_summary=pd.read_csv(root/'outputs/tables/scenario_comparison.csv')
    extended_summary=pd.concat([original_summary,pd.DataFrame([row])],ignore_index=True)
    extended_summary.to_csv(root/'outputs/tables/scenario_comparison_extended.csv',index=False)
    original_frames=[pd.read_csv(root/'outputs/tables'/f'{n}.csv') for n in original_summary.scenario]
    all_frames=pd.concat([*original_frames,frame],ignore_index=True)
    all_frames.to_csv(root/'outputs/tables/all_scenarios_extended.csv',index=False)
    reference = original_summary.set_index('scenario').loc['cbd_employment']
    effects=dict(scenario=NAME,comparison='cbd_employment',
                 cbd_population_change=float(population[cbd_index]-reference.cbd_population),
                 cbd_population_change_pct=float(100*(population[cbd_index]/reference.cbd_population-1)),
                 weighted_radius_change_m=float(row['mean_population_radius_m']-reference.mean_population_radius_m),
                 hhi_change_pct=float(100*(row['population_hhi']/reference.population_hhi-1)),
                 population_redistributed_vs_cbd=float(abs(changes.population_change_vs_cbd).sum()/2),
                 highest_population_zone_id=int(frame.loc[frame.population.idxmax(),'zone_id']),
                 highest_service_zone_id=int(frame.loc[frame.service_employment.idxmax(),'zone_id']),
                 expected_extended_rows=8*136,centers=centers,diagnostics=diagnostics,
                 convergence_history=history)
    (root/'outputs/logs/custom_case_results.json').write_text(json.dumps(effects,indent=2,ensure_ascii=False),encoding='utf8')
    if plots:custom_figures(root,zones,roads,frame,baseline,monocentric,changes,centers)
    return frame,extended_summary,effects


def custom_figures(root,zones,roads,frame,baseline,monocentric,changes,centers):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    from matplotlib.cm import ScalarMappable
    plt.rcParams.update({'font.family':'Times New Roman','font.size':12,'text.color':'black',
                         'axes.labelcolor':'black','xtick.color':'black','ytick.color':'black'})
    maps=root/'outputs/maps';charts=root/'outputs/charts'
    def finish(ax,title):
        ax.set_title(title,fontweight='bold',pad=12);ax.set_aspect('equal');ax.set_axis_off()
    fig,ax=plt.subplots(figsize=(8,7))
    joined=zones.merge(frame,on='zone_id',suffixes=('_source',''))
    joined.plot(column='basic_employment',ax=ax,cmap='YlOrBr',vmin=0,vmax=frame.basic_employment.max(),
                edgecolor='#909090',linewidth=.4,legend=True,legend_kwds={'label':'Pekerjaan dasar (satuan model)','shrink':.65})
    for center in centers:
        ax.plot(center['x'],center['y'],marker='*',color='black',markersize=9)
        ax.annotate(f"{center['role']}\nZona {center['zone_id']} ({center['share']:.0%})",
                    (center['x'],center['y']),xytext=(0,20),textcoords='offset points',ha='center',fontsize=11,
                    bbox=dict(facecolor='white',edgecolor='#888888',alpha=.85,pad=3))
    finish(ax,'Rancangan mandiri: tiga pusat pekerjaan dasar')
    fig.savefig(maps/'08_custom_basic_employment.png',dpi=190,bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(14,5))
    frames=[baseline,monocentric,frame];titles=['Pekerjaan dasar merata','Seluruh pekerjaan dasar di CBD','Tiga pusat: 40%–30%–30%']
    vmin=min(f.population.min() for f in frames);vmax=max(f.population.max() for f in frames)
    for ax,f,title in zip(axes,frames,titles):
        zones.merge(f,on='zone_id').plot(column='population',ax=ax,cmap='YlGnBu',vmin=vmin,vmax=vmax,edgecolor='white',linewidth=.3)
        finish(ax,title)
    fig.colorbar(ScalarMappable(norm=Normalize(vmin,vmax),cmap='YlGnBu'),ax=list(axes),shrink=.6,label='Penduduk per zona (satuan model)')
    fig.savefig(maps/'09_custom_population_comparison.png',dpi=190,bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,7));j=zones.merge(changes,on='zone_id');limit=abs(j.population_change_vs_cbd).max()
    j.plot(column='population_change_vs_cbd',ax=ax,cmap='RdBu_r',vmin=-limit,vmax=limit,edgecolor='white',linewidth=.3,
           legend=True,legend_kwds={'label':'Perubahan penduduk terhadap CBD tunggal','shrink':.65})
    for center in centers:ax.annotate(str(center['zone_id']),(center['x'],center['y']),ha='center',fontsize=11,color='black')
    finish(ax,'Perubahan spasial: tiga pusat dikurangi CBD tunggal')
    fig.savefig(maps/'10_custom_change_vs_cbd.png',dpi=190,bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,5))
    locations=[c['zone_id'] for c in centers];labels=[f"{c['role']}\n(zona {c['zone_id']})" for c in centers]
    for ax,column,title in zip(axes,['population','service_employment'],['Penduduk','Pekerjaan jasa']):
        x=np.arange(3);left=monocentric.set_index('zone_id').loc[locations,column];right=frame.set_index('zone_id').loc[locations,column]
        ax.bar(x-.18,left,.36,label='CBD tunggal',color='#5b7d9a');ax.bar(x+.18,right,.36,label='Tiga pusat',color='#c28a44')
        ax.set_xticks(x,labels);ax.set_title(title);ax.set_ylabel('Satuan model');ax.legend(fontsize=10)
    fig.tight_layout();fig.savefig(charts/'custom_centers_comparison.png',dpi=190,bbox_inches='tight');plt.close(fig)


if __name__=='__main__':
    frame,summary,effects=run_custom_case()
    print(summary[['scenario','cbd_population','mean_population_radius_m','population_hhi']].to_string(index=False))
    print(json.dumps(effects,indent=2,ensure_ascii=True))
