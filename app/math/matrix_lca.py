"""
Heijungs & Suh Technology Matrix Framework for Life Cycle Assessment

Implements the complete matrix-based LCA computation chain:

    A ∈ ℝ^{n×n}  — Technology matrix (inter-process dependencies)
    B ∈ ℝ^{m×n}  — Biosphere matrix (emissions per unit activity)
    Q ∈ ℝ^{p×m}  — Characterization matrix (emission → impact conversion)
    f ∈ ℝ^n      — Final demand vector

    Pipeline:
        s = A⁻¹·f          Scaling vector
        g = B·s             Raw emissions inventory (LCI result)
        h = Q·g = Q·B·A⁻¹·f Environmental impact indicators (e.g., kg CO₂-eq)

References:
    Heijungs, R. & Suh, S. (2002). The Computational Structure of Life Cycle Assessment.
    ISO 14040:2006 — Life cycle assessment — Principles and framework.
    ISO 14044:2006 — Life cycle assessment — Requirements and guidelines.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy.linalg import inv

logger = logging.getLogger(__name__)

# ── Default Characterization Factors (GWP-100, IPCC AR6) ────────────────────
# Maps common emissions to kg CO₂-eq per kg of substance
DEFAULT_GWP_FACTORS: dict[str, float] = {
    "CO2": 1.0,
    "CH4": 29.8,       # IPCC AR6 GWP-100
    "N2O": 273.0,      # IPCC AR6 GWP-100
    "SF6": 25200.0,
    "HFC-134a": 1530.0,
    "CF4": 7380.0,
    "C2F6": 12400.0,
    "NF3": 17400.0,
}


@dataclass
class ProcessInfo:
    """Metadata for a single process/activity in the technology system."""
    name: str
    unit: str = "unit"
    category: str = "general"


@dataclass
class EmissionInfo:
    """Metadata for a single elementary flow (emission)."""
    name: str
    compartment: str = "air"       # air, water, soil
    unit: str = "kg"


@dataclass
class ImpactCategory:
    """Metadata for an impact assessment category."""
    name: str
    unit: str = "kg CO₂-eq"
    method: str = "IPCC AR6 GWP-100"


@dataclass
class LCAResult:
    """Complete result of an LCA computation."""
    scaling_vector: np.ndarray
    inventory: np.ndarray                 # g = B·s
    impact_indicators: np.ndarray         # h = Q·g
    process_contributions: dict[str, float] = field(default_factory=dict)
    hotspots: list[dict[str, Any]] = field(default_factory=list)
    total_impact: float = 0.0

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "scaling_vector": self.scaling_vector.tolist(),
            "inventory": self.inventory.tolist(),
            "impact_indicators": self.impact_indicators.tolist(),
            "process_contributions": self.process_contributions,
            "hotspots": self.hotspots,
            "total_impact": self.total_impact,
        }


class TechnologyMatrix:
    """
    Full Heijungs & Suh matrix-based LCA engine.

    Usage::

        tm = TechnologyMatrix(n_processes=3, n_emissions=2, n_impacts=1)
        tm.set_technology_matrix(A)
        tm.set_biosphere_matrix(B)
        tm.set_characterization_matrix(Q)
        result = tm.compute_impact(demand_vector)
    """

    def __init__(
        self,
        n_processes: int,
        n_emissions: int,
        n_impacts: int = 1,
    ):
        self.n_processes = n_processes
        self.n_emissions = n_emissions
        self.n_impacts = n_impacts

        # Core matrices
        self.A: np.ndarray = np.eye(n_processes, dtype=np.float64)
        self.B: np.ndarray = np.zeros((n_emissions, n_processes), dtype=np.float64)
        self.Q: np.ndarray = np.zeros((n_impacts, n_emissions), dtype=np.float64)

        # Metadata
        self.processes: list[ProcessInfo] = [
            ProcessInfo(name=f"Process_{i}") for i in range(n_processes)
        ]
        self.emissions: list[EmissionInfo] = [
            EmissionInfo(name=f"Emission_{i}") for i in range(n_emissions)
        ]
        self.impact_categories: list[ImpactCategory] = [
            ImpactCategory(name=f"Impact_{i}") for i in range(n_impacts)
        ]

    # ── Matrix Setters ──────────────────────────────────────────────────────

    def set_technology_matrix(self, A: np.ndarray) -> None:
        """Set the technology matrix A ∈ ℝ^{n×n}."""
        A = np.asarray(A, dtype=np.float64)
        if A.shape != (self.n_processes, self.n_processes):
            raise ValueError(
                f"A must be ({self.n_processes}, {self.n_processes}), got {A.shape}"
            )
        if np.linalg.matrix_rank(A) < self.n_processes:
            logger.warning("Technology matrix A is singular or near-singular")
        self.A = A

    def set_biosphere_matrix(self, B: np.ndarray) -> None:
        """Set the biosphere matrix B ∈ ℝ^{m×n}."""
        B = np.asarray(B, dtype=np.float64)
        if B.shape != (self.n_emissions, self.n_processes):
            raise ValueError(
                f"B must be ({self.n_emissions}, {self.n_processes}), got {B.shape}"
            )
        self.B = B

    def set_characterization_matrix(self, Q: np.ndarray) -> None:
        """Set the characterization matrix Q ∈ ℝ^{p×m}."""
        Q = np.asarray(Q, dtype=np.float64)
        if Q.shape != (self.n_impacts, self.n_emissions):
            raise ValueError(
                f"Q must be ({self.n_impacts}, {self.n_emissions}), got {Q.shape}"
            )
        self.Q = Q

    def set_process_names(self, names: list[str]) -> None:
        """Set human-readable process names."""
        self.processes = [ProcessInfo(name=n) for n in names]

    def set_emission_names(self, names: list[str]) -> None:
        """Set human-readable emission names."""
        self.emissions = [EmissionInfo(name=n) for n in names]

    # ── Core Computations ───────────────────────────────────────────────────

    def compute_scaling_vector(self, demand: np.ndarray) -> np.ndarray:
        """
        s = A⁻¹ · f

        The scaling vector tells us how much each process must operate
        to satisfy the final demand.
        """
        demand = np.asarray(demand, dtype=np.float64)
        return inv(self.A) @ demand

    def compute_inventory(self, demand: np.ndarray) -> np.ndarray:
        """
        g = B · A⁻¹ · f  (Life Cycle Inventory result)

        Returns the total elementary flows (emissions) for the system.
        """
        s = self.compute_scaling_vector(demand)
        return self.B @ s

    def compute_impact(self, demand: np.ndarray) -> LCAResult:
        """
        h = Q · B · A⁻¹ · f  (Life Cycle Impact Assessment)

        Full computation pipeline with per-process contribution analysis.
        """
        demand = np.asarray(demand, dtype=np.float64)

        # Step 1: Scaling vector  s = A⁻¹·f
        s = self.compute_scaling_vector(demand)

        # Step 2: Inventory  g = B·s
        g = self.B @ s

        # Step 3: Impact  h = Q·g
        h = self.Q @ g

        # Per-process contribution breakdown
        contributions = self._compute_contributions(s)

        # Identify hotspots (top contributors)
        hotspots = self._identify_hotspots(s)

        total = float(np.sum(h))

        return LCAResult(
            scaling_vector=s,
            inventory=g,
            impact_indicators=h,
            process_contributions=contributions,
            hotspots=hotspots,
            total_impact=total,
        )

    # ── Analysis Helpers ────────────────────────────────────────────────────

    def _compute_contributions(self, scaling: np.ndarray) -> dict[str, float]:
        """Per-process contribution to total impact."""
        contributions: dict[str, float] = {}
        for j in range(self.n_processes):
            # Impact from process j = Q · B[:, j] · s[j]
            process_emissions = self.B[:, j] * scaling[j]
            process_impact = float(np.sum(self.Q @ process_emissions))
            name = self.processes[j].name if j < len(self.processes) else f"Process_{j}"
            contributions[name] = process_impact
        return contributions

    def _identify_hotspots(
        self, scaling: np.ndarray, top_n: int = 5
    ) -> list[dict[str, Any]]:
        """Rank processes by impact contribution, return top N."""
        contributions = self._compute_contributions(scaling)
        total = sum(abs(v) for v in contributions.values()) or 1.0

        ranked = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)
        return [
            {
                "process": name,
                "impact": round(impact, 4),
                "percentage": round(abs(impact) / total * 100, 2),
            }
            for name, impact in ranked[:top_n]
        ]

    # ── Builder from Supply Chain Data ──────────────────────────────────────

    @classmethod
    def from_supply_chain(cls, data: dict) -> "TechnologyMatrix":
        """
        Build TechnologyMatrix from LCA-GPT analysis JSON output.

        Constructs A, B, Q matrices from materials, energy, and transport data.
        """
        materials = data.get("materials", [])
        energies = data.get("energy", [])
        transports = data.get("transport", [])

        all_items = materials + energies + transports
        n = len(all_items)

        if n == 0:
            raise ValueError("No supply chain data to build matrices from")

        # Single impact category: Global Warming Potential (GWP)
        tm = cls(n_processes=n, n_emissions=n, n_impacts=1)

        # Technology matrix: identity (each process produces its own output)
        A = np.eye(n, dtype=np.float64)

        # MOCK/SIMULATION: If the project name contains "nonlinear" or "multi-tier",
        # let's introduce off-diagonal interdependencies to showcase the Non-Linear & Matrix LCA dynamics.
        project_name = data.get("project_info", {}).get("name", "").lower()
        if "nonlinear" in project_name or "multi-tier" in project_name or "dependency" in project_name:
            mat_count = len(materials)
            for j in range(mat_count):
                for i in range(mat_count, n):
                    # Let material j consume 0.15 units of input i per unit produced
                    A[i, j] = -0.15

        tm.A = A

        # Biosphere matrix: diagonal with emission factors
        B = np.zeros((n, n), dtype=np.float64)
        names: list[str] = []

        for i, item in enumerate(all_items):
            if "name" in item:
                # Material
                ef = item.get("emission_factor", 0)
                B[i, i] = ef
                names.append(item["name"])
            elif "type" in item:
                # Energy
                ef = item.get("emission_factor", 0)
                B[i, i] = ef
                names.append(item["type"])
            elif "method" in item:
                # Transport
                ef = item.get("emission_factor", 0)
                B[i, i] = ef
                names.append(item["method"])

        tm.B = B
        tm.set_process_names(names)
        tm.set_emission_names(names)

        # Characterization: all emissions are already in kg CO₂-eq
        tm.Q = np.ones((1, n), dtype=np.float64)
        tm.impact_categories = [
            ImpactCategory(name="Global Warming Potential", unit="kg CO₂-eq")
        ]

        # Demand vector: amounts from each item
        demand = np.zeros(n, dtype=np.float64)
        for i, item in enumerate(all_items):
            if "amount" in item:
                demand[i] = item["amount"]
            elif "usage" in item:
                demand[i] = item["usage"]
            elif "distance" in item:
                demand[i] = item["distance"]

        # Store demand for convenience
        tm._default_demand = demand

        return tm

    def compute_default(self) -> LCAResult:
        """Compute impact using the stored default demand vector."""
        if not hasattr(self, "_default_demand"):
            raise RuntimeError("No default demand vector. Use from_supply_chain().")
        return self.compute_impact(self._default_demand)
