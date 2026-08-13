"""
Leontief Input-Output Model for Economy-Wide Environmental Analysis (EEIO-LCA)

Extends product-level LCA to economy-wide Environmental Extended Input-Output analysis.

    A ∈ ℝ^{n×n}  — Direct requirements matrix (inter-industry coefficients)
    I ∈ ℝ^{n×n}  — Identity matrix
    y ∈ ℝ^n      — Final demand vector (market demand)

    L = (I − A)⁻¹    Leontief inverse (total requirements matrix)
    x = L·y           Total output vector (economy-wide production)

    Environmental extension:
    F ∈ ℝ^{m×n}  — Environmental intensity matrix (emissions per $ output)
    e = F·L·y         Total environmental impact

References:
    Leontief, W. (1970). Environmental repercussions and the economic structure.
    US EPA USEEIO v2.0 — Environmentally Extended Input-Output model.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy.linalg import inv

logger = logging.getLogger(__name__)


@dataclass
class SectorInfo:
    """Metadata for an economic sector."""
    name: str
    code: str = ""
    description: str = ""


@dataclass
class EEIOResult:
    """Result of an EEIO-LCA computation."""
    total_output: np.ndarray          # x = L·y
    leontief_inverse: np.ndarray      # L = (I-A)⁻¹
    environmental_impact: np.ndarray  # e = F·L·y
    sector_contributions: dict[str, float] = field(default_factory=dict)
    multiplier_effects: dict[str, float] = field(default_factory=dict)
    total_impact: float = 0.0

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "total_output": self.total_output.tolist(),
            "environmental_impact": self.environmental_impact.tolist(),
            "sector_contributions": self.sector_contributions,
            "multiplier_effects": self.multiplier_effects,
            "total_impact": self.total_impact,
        }


class LeontiefModel:
    """
    Economic Input-Output LCA (EEIO-LCA) based on Leontief Inverse.

    Usage::

        model = LeontiefModel(n_sectors=5)
        model.set_direct_requirements(A)
        model.set_environmental_intensity(F)
        result = model.compute_impact(final_demand)
    """

    def __init__(self, n_sectors: int, n_env_indicators: int = 1):
        self.n_sectors = n_sectors
        self.n_env = n_env_indicators

        # Direct requirements matrix A
        self.A: np.ndarray = np.zeros((n_sectors, n_sectors), dtype=np.float64)

        # Environmental intensity matrix F (emissions per $ output)
        self.F: np.ndarray = np.zeros((n_env_indicators, n_sectors), dtype=np.float64)

        # Sector metadata
        self.sectors: list[SectorInfo] = [
            SectorInfo(name=f"Sector_{i}") for i in range(n_sectors)
        ]

    def set_direct_requirements(self, A: np.ndarray) -> None:
        """
        Set the direct requirements matrix A.

        A_ij = amount of sector i's output required to produce
               one unit of sector j's output.

        Constraint: Column sums should be < 1 for productive economy.
        """
        A = np.asarray(A, dtype=np.float64)
        if A.shape != (self.n_sectors, self.n_sectors):
            raise ValueError(
                f"A must be ({self.n_sectors}, {self.n_sectors}), got {A.shape}"
            )
        # Check Hawkins-Simon condition: (I-A) must have positive determinant
        det = np.linalg.det(np.eye(self.n_sectors) - A)
        if det <= 0:
            logger.warning(
                f"Hawkins-Simon condition may be violated: det(I-A) = {det:.6f}"
            )
        self.A = A

    def set_environmental_intensity(self, F: np.ndarray) -> None:
        """Set the environmental intensity matrix F ∈ ℝ^{m×n}."""
        F = np.asarray(F, dtype=np.float64)
        if F.shape != (self.n_env, self.n_sectors):
            raise ValueError(
                f"F must be ({self.n_env}, {self.n_sectors}), got {F.shape}"
            )
        self.F = F

    def set_sector_names(self, names: list[str]) -> None:
        """Set human-readable sector names."""
        self.sectors = [SectorInfo(name=n) for n in names]

    # ── Core Computations ───────────────────────────────────────────────────

    def compute_leontief_inverse(self) -> np.ndarray:
        """
        L = (I − A)⁻¹

        The Leontief inverse captures both direct and indirect
        requirements throughout the entire economy.
        """
        I = np.eye(self.n_sectors, dtype=np.float64)
        return inv(I - self.A)

    def compute_total_output(self, final_demand: np.ndarray) -> np.ndarray:
        """
        x = (I − A)⁻¹ · y = L · y

        Total output required across all sectors to meet final demand.
        """
        final_demand = np.asarray(final_demand, dtype=np.float64)
        L = self.compute_leontief_inverse()
        return L @ final_demand

    def compute_impact(self, final_demand: np.ndarray) -> EEIOResult:
        """
        e = F · (I − A)⁻¹ · y = F · L · y

        Full EEIO-LCA computation with sector contribution analysis.
        """
        final_demand = np.asarray(final_demand, dtype=np.float64)
        L = self.compute_leontief_inverse()
        x = L @ final_demand

        # Environmental impact
        e = self.F @ x

        # Sector contributions
        contributions = self._compute_sector_contributions(x)

        # Multiplier effects (how much total output per unit final demand)
        multipliers = self._compute_multipliers(L)

        total = float(np.sum(e))

        return EEIOResult(
            total_output=x,
            leontief_inverse=L,
            environmental_impact=e,
            sector_contributions=contributions,
            multiplier_effects=multipliers,
            total_impact=total,
        )

    # ── Analysis ────────────────────────────────────────────────────────────

    def _compute_sector_contributions(
        self, total_output: np.ndarray
    ) -> dict[str, float]:
        """Per-sector environmental impact contribution."""
        contributions: dict[str, float] = {}
        for j in range(self.n_sectors):
            sector_impact = float(np.sum(self.F[:, j] * total_output[j]))
            name = self.sectors[j].name if j < len(self.sectors) else f"Sector_{j}"
            contributions[name] = round(sector_impact, 4)
        return contributions

    def _compute_multipliers(self, L: np.ndarray) -> dict[str, float]:
        """
        Output multiplier for each sector.

        Multiplier_j = sum of column j of L
        = total economy-wide output generated per unit final demand in sector j
        """
        multipliers: dict[str, float] = {}
        col_sums = L.sum(axis=0)
        for j in range(self.n_sectors):
            name = self.sectors[j].name if j < len(self.sectors) else f"Sector_{j}"
            multipliers[name] = round(float(col_sums[j]), 4)
        return multipliers

    def power_series_approximation(
        self, final_demand: np.ndarray, order: int = 10
    ) -> dict[str, Any]:
        """
        Approximate L·y using the power series expansion:
        L = I + A + A² + A³ + ...

        Useful for educational purposes — shows how indirect effects
        propagate through rounds of production.

        Returns the contribution at each round for visualization.
        """
        final_demand = np.asarray(final_demand, dtype=np.float64)
        n = self.n_sectors

        rounds: list[dict[str, Any]] = []
        cumulative = np.zeros(n, dtype=np.float64)
        A_power = np.eye(n, dtype=np.float64)

        for k in range(order):
            round_output = A_power @ final_demand
            cumulative += round_output
            round_impact = float(np.sum(self.F @ round_output))

            rounds.append({
                "round": k,
                "label": f"Round {k}" if k > 0 else "Direct",
                "output": round_output.tolist(),
                "impact": round(round_impact, 4),
                "cumulative_impact": round(float(np.sum(self.F @ cumulative)), 4),
            })

            A_power = A_power @ self.A  # A^(k+1)

        return {
            "rounds": rounds,
            "converged_output": cumulative.tolist(),
            "total_impact": round(float(np.sum(self.F @ cumulative)), 4),
        }

    @classmethod
    def from_supply_chain(cls, data: dict) -> "LeontiefModel":
        """
        Build a simplified EEIO model from LCA-GPT analysis JSON.

        Maps supply chain items to economic sectors with
        inter-sector dependencies derived from the supply chain graph.
        """
        materials = data.get("materials", [])
        energies = data.get("energy", [])
        transports = data.get("transport", [])

        all_items = materials + energies + transports
        n = len(all_items)

        if n == 0:
            raise ValueError("No supply chain data to build model from")

        model = cls(n_sectors=n, n_env_indicators=1)

        # Build A: simple dependency structure
        # Materials depend on energy and transport
        A = np.zeros((n, n), dtype=np.float64)
        n_mat = len(materials)
        n_en = len(energies)

        for i in range(n_mat):
            for j in range(n_mat, n_mat + n_en):
                # Each material process requires some energy
                A[j, i] = 0.05  # 5% energy dependency
            for j in range(n_mat + n_en, n):
                # Each material process requires some transport
                A[j, i] = 0.02  # 2% transport dependency

        model.set_direct_requirements(A)

        # Environmental intensity: emission factors normalized by amount
        F = np.zeros((1, n), dtype=np.float64)
        names: list[str] = []

        for i, item in enumerate(all_items):
            ef = item.get("emission_factor", 0)
            F[0, i] = ef
            name = item.get("name") or item.get("type") or item.get("method", f"Item_{i}")
            names.append(name)

        model.set_environmental_intensity(F)
        model.set_sector_names(names)

        return model
