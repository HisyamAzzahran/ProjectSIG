"""Compare against original cached outputs and enforce model conservation laws."""
import numpy as np
from .data_loader import cached_table
from .garin_lowry_model import equilibrium
from .distance_matrix import model_cost


def validate_original(points, duration, population, service, root):
    ids=points.zone_id.to_numpy()
    cached=cached_table('Road Network Distance Matrix (#4)',root)
    original_duration=cached.pivot(index='Origin ID',columns='Destination ID',values='Duration').loc[ids,ids].to_numpy()
    cache_p=cached_table('Python Script (#21)',root)['0'].to_numpy()
    cache_s=cached_table('Python Script (#22)',root)['0'].to_numpy()
    replay_p,replay_s,diagnostics,_=equilibrium(model_cost(original_duration,points.PERIMETER),points.BEMP_Unif)
    report=dict(cached_baseline_population_max_error=float(np.max(abs(replay_p-cache_p))),
                cached_baseline_service_max_error=float(np.max(abs(replay_s-cache_s))),
                rebuilt_network_duration_max_error_min=float(np.max(abs(duration-original_duration))),
                rebuilt_population_vs_original_max_error=float(np.max(abs(population-cache_p))),
                rebuilt_service_vs_original_max_error=float(np.max(abs(service-cache_s))),
                cached_replay_diagnostics=diagnostics)
    if max(report['cached_baseline_population_max_error'],report['cached_baseline_service_max_error']) > 1e-9:
        raise AssertionError('Original mathematical baseline not reproduced')
    if report['rebuilt_network_duration_max_error_min'] > 1e-5:
        raise AssertionError('Rebuilt road network differs materially from original OD')
    return report


def validate_result(frame, parameters):
    numeric=frame[['basic_employment','population','service_employment','total_employment']].to_numpy()
    assert len(frame)==136 and frame.zone_id.is_unique
    assert np.isfinite(numeric).all() and (numeric>=-1e-10).all()
    b=frame.basic_employment.sum(); a=parameters.population_per_worker; beta=parameters.service_per_person
    assert np.isclose(frame.population.sum(),a*b/(1-a*beta),rtol=1e-10)
    assert np.isclose(frame.service_employment.sum(),beta*frame.population.sum(),rtol=1e-10)
    assert np.allclose(frame.total_employment,frame.basic_employment+frame.service_employment)
    return True
