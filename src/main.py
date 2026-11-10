"""Command line and KNIME extension entry point."""
import argparse
import json
from .data_loader import ROOT, audit, load_data
from .scenario_analysis import run_scenarios


def run(root=ROOT,plots=True):
    for d in ['docs','data/processed','data/matrices','data/scenarios','outputs/maps','outputs/charts','outputs/tables','outputs/logs']:
        (root/d).mkdir(parents=True,exist_ok=True)
    report=audit(root);zones,points,roads=load_data(root)
    zones.to_file(root/'data/processed/zones.gpkg',layer='zones',driver='GPKG')
    points.to_file(root/'data/processed/centroids.gpkg',layer='centroids',driver='GPKG')
    roads.to_file(root/'data/processed/roads.gpkg',layer='roads',driver='GPKG')
    results,summary,histories,matrices=run_scenarios(root,zones,points,roads)
    if plots:
        from .visualization import make_visualizations
        make_visualizations(root,zones,points,roads,results,summary,histories,matrices)
    return results,summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',nargs='?',choices=['all','audit','baseline','scenarios','validate'],default='all')
    parser.add_argument('--no-plots',action='store_true')
    args=parser.parse_args()
    if args.operation=='audit':
        print(json.dumps(audit(),indent=2));return
    if args.operation=='validate':
        import subprocess,sys
        raise SystemExit(subprocess.call([sys.executable,'-m','pytest','tests','-q'],cwd=ROOT))
    if args.operation=='baseline':
        from .distance_matrix import calculate_od,export_od
        from .garin_lowry_model import equilibrium
        from .validation import validate_original
        _,points,roads=load_data();d,t,c,s,_=calculate_od(roads,points)
        export_od(ROOT/'data/matrices',points.zone_id.to_numpy(),d,t,c,s)
        p,svc,diag,_=equilibrium(c,points.BEMP_Unif)
        print(json.dumps(dict(solver=diag,original_comparison=validate_original(points,t,p,svc,ROOT)),indent=2));return
    _,summary=run(plots=not args.no_plots)
    print(summary[['scenario','population_total','service_total','cbd_population','mean_population_radius_m']].to_string(index=False))


if __name__=='__main__':main()
