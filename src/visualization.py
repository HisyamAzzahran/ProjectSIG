"""Academic maps using supplied polygons, with an offline Cartesian HTML explorer."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, TwoSlopeNorm
from matplotlib.cm import ScalarMappable
import plotly.graph_objects as go
from plotly.colors import sample_colorscale

LABELS={'baseline_uniform':'Baseline: uniform jobs','cbd_employment':'Jobs concentrated in CBD',
        'low_friction':'Lower friction (0.5)','high_friction':'Higher friction (2)',
        'beltway':'Ring 7 at 75 mph','cbd_high_friction':'CBD jobs + friction 2','cbd_beltway':'CBD jobs + beltway'}


def make_visualizations(root,zones,points,roads,results,summary,histories,matrices):
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,
                         'figure.facecolor':'white','axes.titlesize':13,'font.size':10})
    maps=root/'outputs/maps';charts=root/'outputs/charts'
    cbd=points.loc[points.BEMP_CBD.idxmax(),'geometry']
    def finish(ax,title):
        ax.set_title(title,loc='left',pad=14,fontweight='bold');ax.set_aspect('equal')
        ax.set_axis_off()
    fig,ax=plt.subplots(figsize=(10,9))
    zones.plot(ax=ax,color='#e7eef5',edgecolor='#8298aa',linewidth=.4)
    roads.plot(ax=ax,color='#35556c',linewidth=.6)
    ax.scatter([cbd.x],[cbd.y],c='#f08c46',s=65,label='CBD: zone 71',zorder=4)
    ax.legend(loc='upper right');finish(ax,'Hypothetical city | 136 zones and 330 road features')
    fig.text(.13,.06,'Supplied EPSG:3857 geometry; projected metre units; no real-world basemap.',fontsize=9,color='#546675')
    fig.savefig(maps/'01_city_structure.png',dpi=180,bbox_inches='tight');plt.close(fig)
    base=results['baseline_uniform']
    for filename,column,title in [('02_basic_employment','basic_employment','Basic employment | saved uniform baseline'),
                                  ('03_baseline_population','population','Residential population | baseline'),
                                  ('04_baseline_services','service_employment','Service employment | baseline')]:
        frame=zones.merge(base,on='zone_id');fig,ax=plt.subplots(figsize=(9,8))
        frame.plot(column=column,cmap='YlGnBu',legend=True,edgecolor='white',linewidth=.3,ax=ax,
                   legend_kwds={'label':'Model persons' if column=='population' else 'Model jobs','shrink':.7})
        finish(ax,title);fig.savefig(maps/(filename+'.png'),dpi=180,bbox_inches='tight');plt.close(fig)
    names=list(results);vmin=min(r.population.min() for r in results.values());vmax=max(r.population.max() for r in results.values())
    fig,axes=plt.subplots(2,4,figsize=(18,9))
    for ax,name in zip(axes.flat,names):
        frame=zones.merge(results[name],on='zone_id')
        frame.plot(column='population',cmap='YlGnBu',vmin=vmin,vmax=vmax,edgecolor='white',linewidth=.2,ax=ax)
        finish(ax,LABELS[name])
    axes.flat[-1].axis('off')
    fig.colorbar(ScalarMappable(norm=Normalize(vmin,vmax),cmap='YlGnBu'),ax=list(axes.flat),shrink=.6,label='Model persons per zone')
    fig.savefig(maps/'05_scenario_population.png',dpi=180,bbox_inches='tight');plt.close(fig)
    bound=max(abs(r.population_change).max() for r in results.values())
    fig,axes=plt.subplots(2,3,figsize=(15,10))
    for ax,name in zip(axes.flat,names[1:]):
        frame=zones.merge(results[name],on='zone_id')
        frame.plot(column='population_change',cmap='RdBu_r',vmin=-bound,vmax=bound,edgecolor='white',linewidth=.2,ax=ax)
        finish(ax,LABELS[name])
    fig.colorbar(ScalarMappable(norm=Normalize(-bound,bound),cmap='RdBu_r'),ax=list(axes.flat),shrink=.6,label='Population change from saved uniform baseline')
    fig.savefig(maps/'06_population_change.png',dpi=180,bbox_inches='tight');plt.close(fig)
    # Beltway effects have a smaller scale; provide an explicitly separate scale.
    belt=zones.merge(results['beltway'],on='zone_id');limit=float(abs(belt.population_change).max())
    fig,ax=plt.subplots(figsize=(9,8));belt.plot(column='population_change',cmap='RdBu_r',vmin=-limit,vmax=limit,legend=True,ax=ax,
                                             legend_kwds={'label':'Model persons gained/lost','shrink':.7})
    roads.loc[roads.TYPE=='r7'].plot(ax=ax,color='#303640',linewidth=1.4)
    finish(ax,'Beltway effect | separate symmetric colour scale')
    fig.savefig(maps/'07_beltway_change.png',dpi=180,bbox_inches='tight');plt.close(fig)
    for name,values,unit in [('od_distance_heatmap',matrices[0]/1000,'Projected kilometres'),
                             ('model_cost_heatmap',matrices[2],'Model travel minutes')]:
        fig,ax=plt.subplots(figsize=(9,7));im=ax.imshow(values,cmap='magma',origin='lower',extent=[.5,136.5,.5,136.5])
        ax.set(xlabel='Destination zone ID',ylabel='Origin zone ID',title=name.replace('_',' ').title());fig.colorbar(im,label=unit)
        fig.savefig(charts/(name+'.png'),dpi=180,bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(14,5))
    axes[0].barh([LABELS[n] for n in summary.scenario],summary.mean_population_radius_m/1000,color='#246a81')
    axes[0].set_xlabel('Population-weighted radius (projected km)')
    axes[1].barh([LABELS[n] for n in summary.scenario],summary.cbd_population_share*100,color='#d68b3d')
    axes[1].set_xlabel('CBD share of population (%)');fig.tight_layout()
    fig.savefig(charts/'scenario_comparison.png',dpi=180,bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,6))
    for name,frame in results.items():
        profile=frame.groupby('ring').population.mean();ax.plot(profile.index,profile.values,marker='o',label=LABELS[name])
    ax.set(xlabel='Ring (0 = CBD)',ylabel='Mean model persons per zone',title='Population profile by ring');ax.legend(fontsize=8)
    fig.savefig(charts/'population_profiles.png',dpi=180,bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,5))
    for name,h in histories.items():ax.semilogy(range(1,len(h)+1),h,label=LABELS[name])
    ax.axhline(1e-11,color='#999999',linestyle='--');ax.set(xlabel='Fixed-point iteration',ylabel='Maximum population update',title='Independent convergence check');ax.legend(fontsize=7)
    fig.savefig(charts/'convergence.png',dpi=180,bbox_inches='tight');plt.close(fig)
    interactive_map(root,zones,results)


def interactive_map(root,zones,results):
    fig=go.Figure(); maximum=max(r.population.max() for r in results.values());buttons=[]
    for row,value in zip(zones.itertuples(),results['baseline_uniform'].population):
        x,y=row.geometry.exterior.xy
        color=sample_colorscale('YlGnBu',[float(value/maximum)])[0]
        fig.add_trace(go.Scatter(x=list(x),y=list(y),mode='lines',fill='toself',fillcolor=color,
                                line=dict(color='#728694',width=.5),name=f'Zone {row.zone_id}',showlegend=False,
                                text=f'Zone {row.zone_id}<br>Population: {value:.6f}',hoverinfo='text'))
    for name,frame in results.items():
        colors=sample_colorscale('YlGnBu',(frame.population/maximum).to_list())
        texts=[f'Zone {i}<br>Population: {p:.6f}<br>Service jobs: {s:.6f}<br>Change: {d:+.6f}'
               for i,p,s,d in zip(frame.zone_id,frame.population,frame.service_employment,frame.population_change)]
        buttons.append(dict(label=LABELS[name],method='update',args=[{'fillcolor':colors,'text':texts},{'title':LABELS[name]}]))
    fig.update_layout(title='Baseline: uniform jobs',template='plotly_white',height=800,
                      updatemenus=[dict(buttons=buttons,x=0,y=1.12)],margin=dict(t=130),
                      xaxis=dict(title='Easting (projected m)',showgrid=False),
                      yaxis=dict(title='Northing (projected m)',scaleanchor='x',scaleratio=1,showgrid=False),
                      annotations=[dict(text=f'Common population colour scale: 0 to {maximum:.3f} model persons/zone. Hypothetical city, no basemap.',
                                        x=0,y=-.1,xref='paper',yref='paper',showarrow=False)])
    fig.write_html(root/'outputs/maps/interactive_scenarios.html',include_plotlyjs=True,full_html=True)
