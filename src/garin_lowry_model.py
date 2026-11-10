"""Column-vector Garin–Lowry equilibrium with independent fixed-point validation."""
from dataclasses import dataclass
import numpy as np
from scipy.linalg import solve


@dataclass(frozen=True)
class Parameters:
    population_per_worker: float = 2.0
    service_per_person: float = 0.3
    residential_exponent: float = 1.0
    service_exponent: float = 1.0


def allocation_matrices(cost, parameters=Parameters()):
    c = np.asarray(cost, dtype=float)
    if c.ndim != 2 or c.shape[0] != c.shape[1] or not np.isfinite(c).all() or (c <= 0).any():
        raise ValueError('Cost matrix must be square, finite and strictly positive')
    a, b = parameters.population_per_worker, parameters.service_per_person
    if not (a > 0 and b >= 0 and a*b < 1):
        raise ValueError('A finite nonnegative equilibrium requires alpha > 0, beta >= 0, alpha*beta < 1')
    if min(parameters.residential_exponent, parameters.service_exponent) < 0:
        raise ValueError('Friction exponents must be nonnegative')
    # Rows are receiving zones; columns are producing zones.
    f = c ** (-parameters.residential_exponent)
    h = c ** (-parameters.service_exponent)
    G = a * f / f.sum(axis=0, keepdims=True)
    T = b * h / h.sum(axis=0, keepdims=True)
    return G, T


def equilibrium(cost, basic, parameters=Parameters(), tolerance=1e-11, max_iterations=1000):
    G, T = allocation_matrices(cost, parameters)
    basic = np.asarray(basic, dtype=float)
    if basic.shape != (len(G),) or not np.isfinite(basic).all() or (basic < 0).any():
        raise ValueError('Basic employment must be a finite nonnegative zone vector')
    rhs = G @ basic
    system = np.eye(len(G)) - G @ T
    population = solve(system, rhs)
    service = T @ population
    iterate = np.zeros_like(population)
    history = []
    for k in range(max_iterations):
        next_value = G @ (basic + T @ iterate)
        error = float(np.max(np.abs(next_value - iterate)))
        history.append(error)
        iterate = next_value
        if not np.isfinite(iterate).all():
            raise RuntimeError('Divergent iteration')
        if error <= tolerance:
            break
    else:
        raise RuntimeError(f'Iteration did not converge within {max_iterations} iterations')
    if not np.isfinite(population).all() or min(population.min(), service.min()) < -1e-10:
        raise RuntimeError('Invalid equilibrium values')
    diagnostics = dict(residual_inf=float(np.max(np.abs(system @ population-rhs))),
                       balance_residual_inf=float(np.max(np.abs(population-G@(basic+service)))),
                       iterative_difference_inf=float(np.max(np.abs(iterate-population))),
                       iterations=k+1, converged=True,
                       spectral_radius=float(max(abs(np.linalg.eigvals(G@T)))),
                       condition_number=float(np.linalg.cond(system)),
                       basic_total=float(basic.sum()), population_total=float(population.sum()),
                       service_total=float(service.sum()), total_employment=float((basic+service).sum()))
    if diagnostics['iterative_difference_inf'] > 1e-8:
        raise RuntimeError('Analytical and iterative solutions disagree')
    return population, service, diagnostics, history
