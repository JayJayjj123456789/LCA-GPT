import pytest
import numpy as np
from app.math.matrix_lca import TechnologyMatrix, ProcessInfo, EmissionInfo, ImpactCategory
from app.math.leontief import LeontiefModel
from app.math.topsis import TOPSIS
from app.math.uncertainty import MonteCarloSimulation, ParameterDistribution
from app.math.sensitivity import SensitivityAnalysis
from app.math.nonlinear_lca import NonLinearLCA, power_law, logistic, piecewise_linear

def test_technology_matrix_basic():
    # 2 processes, 2 emissions, 1 impact
    tm = TechnologyMatrix(n_processes=2, n_emissions=2, n_impacts=1)
    
    # A = [[1, -0.2], [-0.1, 1]]
    A = np.array([[1.0, -0.2], [-0.1, 1.0]])
    # B = [[2.5, 0.5], [0.1, 1.2]]
    B = np.array([[2.5, 0.5], [0.1, 1.2]])
    # Q = [[1.0, 2.0]]
    Q = np.array([[1.0, 2.0]])
    
    tm.set_technology_matrix(A)
    tm.set_biosphere_matrix(B)
    tm.set_characterization_matrix(Q)
    
    demand = np.array([100.0, 50.0])
    
    s = tm.compute_scaling_vector(demand)
    g = tm.compute_inventory(demand)
    res = tm.compute_impact(demand)
    
    # Mathematical checks:
    # s = A^-1 @ f
    # det(A) = 1*1 - (-0.2)*(-0.1) = 1 - 0.02 = 0.98
    # A^-1 = 1/0.98 * [[1, 0.2], [0.1, 1]]
    # s = 1/0.98 * [[100 + 10], [10 + 50]] = 1/0.98 * [110, 60] = [112.24, 61.22]
    expected_s = np.linalg.inv(A) @ demand
    assert np.allclose(s, expected_s)
    
    expected_g = B @ expected_s
    assert np.allclose(g, expected_g)
    
    expected_h = Q @ expected_g
    assert np.allclose(res.impact_indicators, expected_h)
    assert res.total_impact == float(np.sum(expected_h))
    
    # Check hotspot logic
    assert len(res.hotspots) > 0
    assert "process" in res.hotspots[0]
    assert "percentage" in res.hotspots[0]

def test_technology_matrix_from_supply_chain(sample_analysis_result):
    tm = TechnologyMatrix.from_supply_chain(sample_analysis_result)
    assert tm.n_processes == 4  # Steel, Aluminum, Electricity, Truck
    res = tm.compute_default()
    assert res.total_impact > 0
    assert np.allclose(res.total_impact, sample_analysis_result["total_estimated_co2"])

def test_leontief_model():
    model = LeontiefModel(n_sectors=3, n_env_indicators=1)
    
    # Direct requirements matrix A (column sums < 1)
    A = np.array([
        [0.1, 0.2, 0.1],
        [0.2, 0.1, 0.3],
        [0.0, 0.2, 0.1]
    ])
    F = np.array([[1.5, 0.8, 2.0]])
    
    model.set_direct_requirements(A)
    model.set_environmental_intensity(F)
    
    demand = np.array([100, 200, 150])
    res = model.compute_impact(demand)
    
    # Hawkins-Simon condition / determinant check
    det = np.linalg.det(np.eye(3) - A)
    assert det > 0
    
    assert res.total_output.shape == (3,)
    assert res.environmental_impact.shape == (1,)
    assert res.total_impact == float(res.environmental_impact[0])
    
    # Power series approximation
    approx = model.power_series_approximation(demand, order=15)
    assert len(approx["rounds"]) == 15
    assert np.allclose(approx["total_impact"], res.total_impact, rtol=1e-2)

def test_leontief_from_supply_chain(sample_analysis_result):
    model = LeontiefModel.from_supply_chain(sample_analysis_result)
    assert model.n_sectors == 4
    res = model.compute_impact([50, 20, 100, 500])
    assert res.total_impact > 0

def test_topsis_rank():
    topsis = TOPSIS()
    
    alternatives = ["Supplier A", "Supplier B", "Supplier C"]
    criteria = ["Carbon", "Cost", "Quality"]
    
    # row = alternative, col = criteria
    # Carbon (cost), Cost (cost), Quality (benefit)
    matrix = np.array([
        [100.0, 500.0, 8.0],
        [150.0, 300.0, 9.0],
        [80.0,  600.0, 7.0]
    ])
    
    weights = [0.5, 0.3, 0.2]
    criteria_types = ["cost", "cost", "benefit"]
    
    res = topsis.rank(alternatives, criteria, matrix, weights, criteria_types)
    
    assert len(res.rankings) == 3
    assert res.rankings[0]["rank"] == 1
    assert "alternative" in res.rankings[0]
    assert "closeness_coefficient" in res.rankings[0]
    
    # Check bounds
    for coef in res.closeness_coefficients:
        assert 0.0 <= coef <= 1.0

def test_topsis_convenience_methods():
    topsis = TOPSIS()
    
    suppliers = [
        {"name": "S1", "carbon": 100, "cost": 10, "lead_time": 5, "quality": 8},
        {"name": "S2", "carbon": 120, "cost": 8, "lead_time": 4, "quality": 9},
    ]
    res_suppliers = topsis.rank_suppliers(suppliers)
    assert len(res_suppliers.rankings) == 2
    
    materials = [
        {"name": "M1", "carbon_footprint": 1.5, "cost": 5, "recyclability": 80, "durability": 10},
        {"name": "M2", "carbon_footprint": 2.5, "cost": 3, "recyclability": 90, "durability": 8},
    ]
    res_materials = topsis.rank_materials(materials)
    assert len(res_materials.rankings) == 2

def test_parameter_distribution():
    rng = np.random.default_rng(42)
    
    # Normal
    dist_norm = ParameterDistribution(dist_type="normal", mean=10.0, std=1.0)
    samples = dist_norm.sample(rng, 100)
    assert len(samples) == 100
    assert 5.0 < np.mean(samples) < 15.0
    
    # Lognormal
    dist_log = ParameterDistribution(dist_type="lognormal", mean=5.0, std=0.5)
    samples = dist_log.sample(rng, 100)
    assert np.all(samples > 0)
    
    # Uniform
    dist_uni = ParameterDistribution(dist_type="uniform", mean=5.0, low=2.0, high=8.0)
    samples = dist_uni.sample(rng, 100)
    assert np.all(samples >= 2.0) and np.all(samples <= 8.0)
    
    # Triangular
    dist_tri = ParameterDistribution(dist_type="triangular", mean=5.0, low=1.0, mode=4.0, high=10.0)
    samples = dist_tri.sample(rng, 100)
    assert np.all(samples >= 1.0) and np.all(samples <= 10.0)

def test_monte_carlo_simulation():
    # 2 processes
    tm = TechnologyMatrix(n_processes=2, n_emissions=2, n_impacts=1)
    tm.set_technology_matrix(np.eye(2))
    tm.set_biosphere_matrix(np.array([[1.5, 0.0], [0.0, 2.5]]))
    tm.set_characterization_matrix(np.array([[1.0, 1.0]]))
    
    mc = MonteCarloSimulation(tm)
    mc.set_auto_uncertainty(cv=0.10)
    
    # Verify setter methods
    mc.set_technology_uncertainty(0, 0, dist_type="normal", mean=1.0, std=0.05)
    mc.set_emission_factor_uncertainty(0, dist_type="lognormal", mean=1.5, std=0.1)
    
    demand = np.array([10.0, 20.0])
    res = mc.simulate(demand, n_sim=100, seed=42)
    
    assert res.n_simulations == 100
    assert len(res.distribution) == 100
    assert res.mean > 0
    assert res.std > 0
    assert res.ci_95[0] < res.mean < res.ci_95[1]
    assert len(res.convergence) > 0

def test_sensitivity_analysis():
    # A = identity, B = diag(EFs), Q = ones
    tm = TechnologyMatrix(n_processes=3, n_emissions=3, n_impacts=1)
    tm.A = np.eye(3)
    tm.B = np.diag([2.0, 1.5, 3.0])
    tm.Q = np.ones((1, 3))
    
    sa = SensitivityAnalysis()
    demand = np.array([10.0, 20.0, 30.0])
    
    res = sa.analyze(tm.A, tm.B, tm.Q, demand, process_names=["P1", "P2", "P3"])
    
    # Check partial derivatives
    # ∂h/∂B_kl = Q_k * s_l
    # For diagonal: ∂h/∂B_ii = 1.0 * s_i = demand_i
    assert np.allclose(list(res.sensitivity_B.values())[:3], [10.0, 20.0, 30.0])
    
    # Contribution analysis
    assert len(res.contributions) == 3
    assert res.contributions[0]["process"] == "P3"  # highest impact: 3.0 * 30 = 90
    
    # Tornado data
    assert len(res.tornado_data) > 0
    assert res.tornado_data[0]["parameter"].endswith("P3")
 
def test_nonlinear_functions():
    # Test scale functions
    assert power_law(10.0, alpha=0.5, scale=2.0) == 2.0 * np.sqrt(10.0)
    assert power_law(0.0) == 0.0
    
    val_log = logistic(0.0, K=10.0, r=1.0, x0=0.0)
    assert np.isclose(val_log, 5.0)  # midpoint value should be K/2
    
    assert piecewise_linear(50, breakpoints=[100, 200], slopes=[1.0, 0.8, 0.5]) == 1.0
    assert piecewise_linear(150, breakpoints=[100, 200], slopes=[1.0, 0.8, 0.5]) == 0.8
    assert piecewise_linear(250, breakpoints=[100, 200], slopes=[1.0, 0.8, 0.5]) == 0.5

def test_nonlinear_lca_solve():
    nl = NonLinearLCA(n_processes=2)
    # base A = [[1, -0.2], [-0.1, 1]]
    nl.set_base_matrix(np.array([[1.0, -0.2], [-0.1, 1.0]]))
    
    # Add scale function for off-diagonal interaction
    nl.set_scale_function(0, 1, "power", alpha=-0.05)
    nl.set_process_names(["P1", "P2"])
    
    B = np.array([[1.0, 0.5], [0.2, 2.0]])
    Q = np.array([[1.0, 1.0]])
    demand = np.array([100.0, 50.0])
    
    res = nl.solve_equilibrium(B, Q, demand)
    assert res.converged
    assert res.iterations > 0
    assert res.nonlinear_impact > 0
    assert len(res.convergence_history) == res.iterations
    
    # Verify building NonLinearLCA from TechnologyMatrix
    tm = TechnologyMatrix(n_processes=2, n_emissions=2, n_impacts=1)
    tm.set_technology_matrix(np.array([[1.0, -0.2], [-0.1, 1.0]]))
    tm.set_process_names(["ProcA", "ProcB"])
    
    nl_from_tm = NonLinearLCA.from_technology_matrix(tm)
    assert nl_from_tm.n == 2
    assert (0, 1) in nl_from_tm.scale_functions
    
    comp = nl_from_tm.compare_linear_vs_nonlinear(B, Q, demand)
    assert "linear_total" in comp
    assert "nonlinear_total" in comp
    assert len(comp["process_comparison"]) == 2
