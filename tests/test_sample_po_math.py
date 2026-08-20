"""Verify the mathematical deep-dive claims against the real sample_purchase_order
data. These values were independently recomputed (see the math deep-dive document)
and lock in the correctness of every model in app/math with the PO-2024-001 sample.

Sample PO data (data/sample_purchase_order.txt), EFs = deep web-researched
fallback (app/search.py, updated Aug 2026):
    Steel 500 kg @ 2.40, Aluminum 200 kg @ 14.8, HDPE 150 kg @ 1.90,
    Copper 75 kg @ 4.0, Electricity 2500 kWh @ 0.4857, Truck 450 km @ 0.87
"""
import numpy as np
import pytest

from app.math.matrix_lca import TechnologyMatrix
from app.math.leontief import LeontiefModel
from app.math.topsis import TOPSIS
from app.math.uncertainty import MonteCarloSimulation
from app.math.sensitivity import SensitivityAnalysis
from app.math.nonlinear_lca import NonLinearLCA, power_law
from app.search import search_emission_factor

TOTAL_BASIC = 6_350.75  # sum(amount * EF) — doc §9.2
TOTAL_LEONTIEF = 6_389.31  # F·(I−A)⁻¹·y — doc §9.4


@pytest.fixture
def po_audit():
    """Audit JSON with the enriched EFs from sample_purchase_order (PO-2024-001)."""
    return {
        "project_info": {
            "name": "Purchase Order PO-2024-001",
            "supplier": "Green Materials Co., Ltd.",
        },
        "materials": [
            {"name": "Steel Sheets (Grade 304)", "amount": 500, "unit": "kg",
             "emission_factor": 2.40, "note": "Source: worldsteel 2022 LCI — https://worldsteel.org/"},
            {"name": "Aluminum Rods (6061-T6)", "amount": 200, "unit": "kg",
             "emission_factor": 14.8, "note": "Source: IAI 2023 — https://international-aluminium.org/"},
            {"name": "Plastic Pellets (HDPE)", "amount": 150, "unit": "kg",
             "emission_factor": 1.90, "note": "Source: PlasticsEurope — https://plasticseurope.org/"},
            {"name": "Copper Wire (99.9%)", "amount": 75, "unit": "kg",
             "emission_factor": 4.0, "note": "Source: ICA 2019 — https://internationalcopper.org/"},
        ],
        "energy": [
            {"type": "Electricity (manufacturing)", "usage": 2500, "unit": "kWh",
             "emission_factor": 0.4857, "note": "Source: TGO Thailand Grid — https://ghgreduction.tgo.or.th/"},
        ],
        "transport": [
            {"method": "Truck transport", "distance": 450, "unit": "km",
             "emission_factor": 0.87, "note": "Source: DEFRA 2024 — https://www.gov.uk/"},
        ],
    }


def test_ef_fuzzy_matching(monkeypatch):
    """The PO's compound item names must resolve to the fallback DB, NOT Serper.

    This was the bug that produced 8.61 t in production: exact-name matching missed
    "Steel Sheets", "Aluminum Rods", "Plastic Pellets (HDPE)", "Copper Wire" and
    "Road Freight", so Serper returned wrong factors (or the LLM's hallucinated
    HDPE 33.0 survived). The expected EFs below reproduce the verified 4,443.50 kg.
    """
    monkeypatch.setattr("app.search.SERPER_API_KEY", "")  # keep tests hermetic
    cases = {
        "Steel Sheets (Grade 304)":             2.40,
        "Aluminum Rods (6061-T6)":              14.8,
        "Plastic Pellets (HDPE)":               1.90,   # paren keyword wins over generic 'plastic'
        "Copper Wire (99.9% pure)":             4.0,
        "Electricity (estimated operational use)": 0.4857,
        "Road Freight (estimated delivery)":    0.87,   # alias → truck
        "Truck":                                0.87,
        "Natural gas pipeline":                 2.05,   # multi-word key substring
        "Cardboard packaging":                  1.20,   # whole-token match
        "Carbon fiber composite":               24.0,   # multi-word key substring
    }
    for name, expected in cases.items():
        res = search_emission_factor(name)
        assert res is not None, f"No EF resolved for '{name}'"
        assert res.value == pytest.approx(expected), f"'{name}' → {res.value}, expected {expected}"

    # False-positive guards: short keys must not leak into unrelated words
    assert search_emission_factor("Office chair") is None      # 'air' must NOT match 'chair'
    assert search_emission_factor("Cardboard only") is not None  # still 0.94 (not 'car')


def test_basic_sum(po_audit):
    """doc §9.2 — E = Σ Activity × EF = 4,443.50 kg CO₂e."""
    total = 0.0
    for m in po_audit["materials"]:
        total += m["amount"] * m["emission_factor"]
    for e in po_audit["energy"]:
        total += e["usage"] * e["emission_factor"]
    for t in po_audit["transport"]:
        total += t["distance"] * t["emission_factor"]
    assert total == pytest.approx(TOTAL_BASIC)

    # backend._recalculate_total_co2 must produce the same value
    from backend.main import _recalculate_total_co2
    import copy
    data = copy.deepcopy(po_audit)
    _recalculate_total_co2(data)
    assert data["total_estimated_co2"] == pytest.approx(TOTAL_BASIC)


def test_matrix_lca(po_audit):
    """doc §9.3 — h = Q·B·A⁻¹·f with A=I ⇒ h = Σ EF·amount = 4,443.5."""
    tm = TechnologyMatrix.from_supply_chain(po_audit)
    res = tm.compute_default()
    assert res.total_impact == pytest.approx(TOTAL_BASIC)

    # A must be identity for a plain Purchase Order (no nonlinear/multi-tier keyword)
    assert np.array_equal(tm.A, np.eye(6))

    # Contributions match the doc's table
    c = res.process_contributions
    assert c["Aluminum Rods (6061-T6)"] == pytest.approx(2960.00)
    assert c["Electricity (manufacturing)"] == pytest.approx(1214.25)
    assert c["Steel Sheets (Grade 304)"] == pytest.approx(1200.00)
    assert c["Copper Wire (99.9%)"] == pytest.approx(300.00)
    assert c["Plastic Pellets (HDPE)"] == pytest.approx(285.00)
    assert c["Truck transport"] == pytest.approx(391.50)

    # Hotspots are the top-5 (HDPE, the smallest, is excluded)
    assert len(res.hotspots) == 5
    assert res.hotspots[0]["process"] == "Aluminum Rods (6061-T6)"
    assert res.hotspots[0]["percentage"] == pytest.approx(46.61, rel=1e-3)


def test_leontief_eeio(po_audit):
    """doc §9.4 — e = F·(I−A)⁻¹·y = 6,389.31; indirect round-1 = 38.56."""
    model = LeontiefModel.from_supply_chain(po_audit)
    items = po_audit["materials"] + po_audit["energy"] + po_audit["transport"]
    demand = np.array([it.get("amount", 0) or it.get("usage", 0) or it.get("distance", 0)
                       for it in items])

    res = model.compute_impact(demand)
    assert res.total_impact == pytest.approx(TOTAL_LEONTIEF, rel=1e-4)
    assert res.total_output[4] == pytest.approx(2546.25)   # energy output
    assert res.total_output[5] == pytest.approx(468.50)    # transport output

    # A² = 0 ⇒ L = I + A (exact), and Hawkins-Simon holds
    assert np.max(np.abs(model.A @ model.A)) == 0.0
    assert np.linalg.det(np.eye(6) - model.A) == pytest.approx(1.0)

    # Indirect impact = total − direct = 38.56 (round 1 of the power series)
    assert res.total_impact - TOTAL_BASIC == pytest.approx(38.56, rel=1e-3)

    # Multiplier for a material sector = 1 + 0.05 + 0.02 = 1.07
    mults = model._compute_multipliers(model.compute_leontief_inverse())
    assert mults["Steel Sheets (Grade 304)"] == pytest.approx(1.07)

    # Power series rounds: direct 6350.75, round1 38.56, round2+ 0
    ps = model.power_series_approximation(demand, order=8)
    assert ps["rounds"][0]["impact"] == pytest.approx(TOTAL_BASIC)
    assert ps["rounds"][1]["impact"] == pytest.approx(38.56, rel=1e-3)
    assert ps["rounds"][2]["impact"] == 0.0
    assert ps["total_impact"] == pytest.approx(TOTAL_LEONTIEF, rel=1e-4)


def test_monte_carlo_sigma(po_audit):
    """doc §9.5 — analytic σ_h = 0.15·√(Σ(fᵢ·EFᵢ)²) ≈ 519.63; simulation ≈ it."""
    f = np.array([500, 200, 150, 75, 2500, 450])
    efs = np.array([2.40, 14.8, 1.90, 4.0, 0.4857, 0.87])
    analytic_sigma = 0.15 * np.sqrt(np.sum((f * efs) ** 2))
    assert analytic_sigma == pytest.approx(519.63, rel=1e-3)

    tm = TechnologyMatrix.from_supply_chain(po_audit)
    mc = MonteCarloSimulation(tm)
    mc.set_auto_uncertainty(cv=0.15)
    res = mc.simulate(tm._default_demand, n_sim=5000, seed=42)

    assert res.n_simulations == 5000
    assert res.mean == pytest.approx(TOTAL_BASIC, rel=5e-2)
    assert res.std == pytest.approx(analytic_sigma, rel=5e-2)
    assert res.ci_95[0] < res.mean < res.ci_95[1]
    assert len(res.convergence) > 0


def test_sensitivity(po_audit):
    """doc §9.6 — ∂h/∂Bᵢᵢ = fᵢ, SR = fᵢ·EFᵢ/h, tornado swings = 0.2·impact."""
    tm = TechnologyMatrix.from_supply_chain(po_audit)
    sa = SensitivityAnalysis()
    res = sa.analyze(tm.A, tm.B, tm.Q, tm._default_demand,
                     process_names=[p.name for p in tm.processes])

    # ∂h/∂B_ii = f_i
    assert res.sensitivity_B["B[0,0]"] == pytest.approx(500.0)
    assert res.sensitivity_B["B[1,1]"] == pytest.approx(200.0)
    assert res.sensitivity_B["B[4,4]"] == pytest.approx(2500.0)
    assert res.sensitivity_B["B[5,5]"] == pytest.approx(450.0)

    # Sensitivity ratios: aluminum is the most sensitive EF
    assert res.sensitivity_ratios["B[1,1]"] == pytest.approx(0.4661, rel=1e-3)
    assert res.sensitivity_ratios["B[5,5]"] == pytest.approx(0.0616, abs=5e-5)

    # Tornado: swing = 0.2 × process impact
    tornado = {t["parameter"]: t for t in res.tornado_data}
    assert tornado["EF: Aluminum Rods (6061-T6)"]["swing"] == pytest.approx(592.00, rel=1e-2)
    assert tornado["EF: Electricity (manufacturing)"]["swing"] == pytest.approx(242.85, rel=1e-2)
    assert tornado["EF: Steel Sheets (Grade 304)"]["swing"] == pytest.approx(240.00, rel=1e-2)
    assert res.tornado_data[0]["parameter"] == "EF: Aluminum Rods (6061-T6)"


def test_nonlinear_multi_tier(po_audit):
    """doc §9.7 — multi-tier mode adds A[i,j] = −0.15 ⇒ linear h = 6,538.85;
    non-linear power-law (α=0.85) converges away from it."""
    mt = dict(po_audit)
    mt["project_info"] = {"name": "multi-tier demo", "supplier": "x"}
    tm = TechnologyMatrix.from_supply_chain(mt)
    res = tm.compute_default()
    assert res.total_impact == pytest.approx(6_538.85, rel=1e-3)

    nl = NonLinearLCA.from_technology_matrix(tm)
    comp = nl.compare_linear_vs_nonlinear(tm.B, tm.Q, tm._default_demand)
    assert comp["linear_total"] == pytest.approx(6_538.85, rel=1e-3)
    assert comp["converged"] is True
    # Linear deviation vs the A=I baseline is +2.96%
    assert (6_538.85 - TOTAL_BASIC) / TOTAL_BASIC * 100 == pytest.approx(2.962, rel=1e-2)
    # Power law at the material scale: 925^0.85 ≈ 332.06 (doc's 314.8 is an error)
    assert power_law(925, alpha=0.85) == pytest.approx(332.06, rel=1e-3)


def test_topsis_example():
    """doc §9.8 — standard TOPSIS on the 3-supplier example.

    NOTE: the doc claims S2 is #1 (C=1.000) because it wrongly assumes the ideal
    point equals S2's row. Per-criterion ideals are mixed across alternatives, so
    the correct ranking is S1 > S2 > S3 with C = 0.538, 0.508, 0.492.
    """
    suppliers = [
        {"name": "S1", "carbon": 100, "cost": 10, "lead_time": 5, "quality": 8},
        {"name": "S2", "carbon": 120, "cost": 8, "lead_time": 4, "quality": 9},
        {"name": "S3", "carbon": 80, "cost": 12, "lead_time": 7, "quality": 7},
    ]
    tres = TOPSIS().rank_suppliers(suppliers, weights=[0.4, 0.3, 0.2, 0.1])

    C = tres.closeness_coefficients
    assert C[0] == pytest.approx(0.538, abs=1e-2)
    assert C[1] == pytest.approx(0.508, abs=1e-2)
    assert C[2] == pytest.approx(0.492, abs=1e-2)

    ranks = {r["alternative"]: r["rank"] for r in tres.rankings}
    assert ranks == {"S1": 1, "S2": 2, "S3": 3}

    # Sanity: ideal best is NOT a single alternative's row (per-criterion min/max)
    assert tres.ideal_best[0] == pytest.approx(0.1823, abs=1e-3)  # min carbon (S3)
    assert tres.ideal_best[1] == pytest.approx(0.1368, abs=1e-3)  # min cost (S2)