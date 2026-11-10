"""Controlled experiments, including the lab manual's CBD and beltway cases."""
from dataclasses import asdict
import json
import numpy as np
import pandas as pd
from .garin_lowry_model import Parameters, equilibrium
from .distance_matrix import calculate_od, export_od
from .validation import validate_result, validate_original


def run_scenarios(root, zones, points, roads):
    ids=points.zone_id.to_numpy()
    distance,duration,cost,snaps,network=calculate_od(roads,points)
    export_od(root/'data/matrices',ids,distance,duration,cost,snaps)
    baseline_basic=points.BEMP_Unif.to_numpy()
    pop,svc,_,_=equilibrium(cost,baseline_basic)
    original_validation=validate_original(points,duration,pop,svc,root)
    (root/'docs/baseline_validation.json').write_text(json.dumps(original_validation,indent=2),encoding='utf8')
    cbd=points.BEMP_CBD.to_numpy().copy()
    cbd *= baseline_basic.sum()/cbd.sum()
    cbd_point=points.loc[points.BEMP_CBD.idxmax(),'geometry']
    radii=points.geometry.distance(cbd_point).to_numpy()
    # The first nine 15-zone area groups plus the CBD are ten model rings.
    ring_order=zones.geometry.area.rank(method='dense')
    # Use radius bins for readable grouping; supplied width is about 604 projected m.
    ring=np.clip(np.rint(radii/604.0).astype(int),0,9)
    belt_d,belt_t,belt_cost,belt_snaps,belt_network=calculate_od(roads,points,'speed1')
    export_od(root/'data/scenarios/beltway/matrices',ids,belt_d,belt_t,belt_cost,belt_snaps)
    modified=roads.copy(); modified['speed']=modified['speed1']
    modified.to_file(root/'data/scenarios/beltway/roads.gpkg',layer='beltway_roads',driver='GPKG')
    experiments=[('baseline_uniform',baseline_basic,Parameters(),cost,'speed'),
                 ('cbd_employment',cbd,Parameters(),cost,'speed'),
                 ('low_friction',baseline_basic,Parameters(residential_exponent=.5,service_exponent=.5),cost,'speed'),
                 ('high_friction',baseline_basic,Parameters(residential_exponent=2,service_exponent=2),cost,'speed'),
                 ('beltway',baseline_basic,Parameters(),belt_cost,'speed1'),
                 ('cbd_high_friction',cbd,Parameters(residential_exponent=2,service_exponent=2),cost,'speed'),
                 ('cbd_beltway',cbd,Parameters(),belt_cost,'speed1')]
    results={}; summaries=[]; histories={}; diagnostics={}
    for name,basic,parameters,scenario_cost,speed in experiments:
        p,s,diag,history=equilibrium(scenario_cost,basic,parameters)
        frame=pd.DataFrame(dict(zone_id=ids,TRACT0_ID=points.TRACT0_ID,ring=ring,radius_m=radii,
                                basic_employment=basic,population=p,service_employment=s,total_employment=basic+s))
        validate_result(frame,parameters)
        reference=results.get('baseline_uniform',frame)
        frame['population_change']=p-reference.population.to_numpy()
        frame['service_change']=s-reference.service_employment.to_numpy()
        frame['population_change_pct']=100*frame.population_change/reference.population.to_numpy()
        frame['scenario']=name
        results[name]=frame; histories[name]=history; diagnostics[name]=diag
        folder=root/'data/scenarios'/name;folder.mkdir(parents=True,exist_ok=True)
        frame[['zone_id','basic_employment']].to_csv(folder/'basic_employment.csv',index=False)
        frame.to_csv(root/'outputs/tables'/f'{name}.csv',index=False)
        inputs=dict(scenario=name,parameters=asdict(parameters),speed_column=speed,
                    reference='baseline_uniform',basic_total=float(basic.sum()),
                    origin='original cached workflow; CBD normalized to preserve saved BEMP_Unif total')
        (folder/'parameters.json').write_text(json.dumps(inputs,indent=2),encoding='utf8')
        (folder/'solver_diagnostics.json').write_text(json.dumps(diag,indent=2),encoding='utf8')
        joined=zones.merge(frame,on='zone_id',validate='one_to_one',suffixes=('_source',''))
        assert len(joined)==136 and joined.population.notna().all()
        joined.to_file(root/'outputs/maps'/f'{name}.gpkg',layer='zone_results',driver='GPKG')
        cbd_idx=int(np.argmax(points.BEMP_CBD.to_numpy()))
        summaries.append(dict(scenario=name,**diag,cbd_population=float(p[cbd_idx]),
                              cbd_population_share=float(p[cbd_idx]/p.sum()),
                              mean_population_radius_m=float(np.dot(p,radii)/p.sum()),
                              population_hhi=float(np.sum((p/p.sum())**2)),
                              population_min=float(p.min()),population_max=float(p.max()),
                              population_redistributed=float(abs(frame.population_change).sum()/2),
                              mean_network_duration_min=float((belt_t if speed=='speed1' else duration).mean())))
    summary=pd.DataFrame(summaries);summary.to_csv(root/'outputs/tables/scenario_comparison.csv',index=False)
    pd.concat(results.values(),ignore_index=True).to_csv(root/'outputs/tables/all_scenarios.csv',index=False)
    (root/'outputs/logs/network_diagnostics.json').write_text(json.dumps({'baseline':network,'beltway':belt_network},indent=2),encoding='utf8')
    (root/'outputs/logs/convergence_history.json').write_text(json.dumps(histories,indent=2),encoding='utf8')
    return results,summary,histories,(distance,duration,cost)
