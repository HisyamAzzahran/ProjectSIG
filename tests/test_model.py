"""Known-solution and orientation tests independent of supplied data."""
import numpy as np
import pytest
from src.garin_lowry_model import Parameters, allocation_matrices, equilibrium


def test_single_zone_known_solution():
    p,s,d,h=equilibrium([[3.0]],[100.0])
    np.testing.assert_allclose(p,[500.0]);np.testing.assert_allclose(s,[150.0])
    assert d['converged'] and d['residual_inf']<1e-10


def test_two_equal_cost_zones_known_solution():
    p,s,_,_=equilibrium(np.ones((2,2)),[100,0])
    np.testing.assert_allclose(p,[250,250]);np.testing.assert_allclose(s,[75,75])


def test_independent_allocation_with_unequal_exponents():
    # This catches reversed matrix products hidden by equal friction exponents.
    c=np.array([[1,2,4],[2,1,3],[4,3,2]],float)
    par=Parameters(residential_exponent=.5,service_exponent=2)
    G,T=allocation_matrices(c,par)
    assert not np.allclose(G@T,T@G)
    p,s,d,_=equilibrium(c,[1,3,2],par)
    np.testing.assert_allclose(p,G@([1,3,2]+s),atol=1e-10)
    np.testing.assert_allclose(s,T@p,atol=1e-10)
    np.testing.assert_allclose(G.sum(axis=0),2)
    np.testing.assert_allclose(T.sum(axis=0),.3)
    assert d['iterative_difference_inf']<1e-8


@pytest.mark.parametrize('cost',[[[0,1],[1,0]],[[1,-1],[-1,1]],[[1,np.nan],[1,1]],[[1,2]]])
def test_invalid_cost_is_rejected(cost):
    with pytest.raises(ValueError):equilibrium(cost,[1,1])


def test_unstable_feedback_is_rejected():
    with pytest.raises(ValueError):equilibrium([[1]],[1],Parameters(service_per_person=.5))


def test_negative_employment_is_rejected():
    with pytest.raises(ValueError):equilibrium([[1]],[-1])


def test_iteration_limit_is_enforced():
    with pytest.raises(RuntimeError,match='did not converge'):equilibrium([[1]],[100],max_iterations=1)


def test_zero_service_feedback():
    p,s,_,_=equilibrium([[1]],[10],Parameters(service_per_person=0))
    np.testing.assert_allclose(p,[20]);np.testing.assert_allclose(s,[0])
