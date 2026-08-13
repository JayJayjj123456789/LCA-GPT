"""
TOPSIS — Technique for Order of Preference by Similarity to Ideal Solution

Multi-Criteria Decision Analysis for ranking alternatives (suppliers, materials,
product designs) by environmental and economic criteria.

Algorithm Steps:
    1. Normalize:  r_ij = x_ij / √(Σ_i x_ij²)
    2. Weight:     v_ij = w_j · r_ij
    3. Ideal+:     v_j⁺ = max(v_ij) for benefit, min(v_ij) for cost
    4. Ideal−:     v_j⁻ = min(v_ij) for benefit, max(v_ij) for cost
    5. Distance+:  d_i⁺ = √(Σ_j (v_ij − v_j⁺)²)
    6. Distance−:  d_i⁻ = √(Σ_j (v_ij − v_j⁻)²)
    7. Closeness:  C_i  = d_i⁻ / (d_i⁺ + d_i⁻)

    C_i → 1 means closer to ideal solution (best alternative)

References:
    Hwang, C.L. & Yoon, K. (1981). Multiple Attribute Decision Making.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TOPSISResult:
    """Complete TOPSIS analysis result."""
    rankings: list[dict[str, Any]]
    normalized_matrix: np.ndarray
    weighted_matrix: np.ndarray
    ideal_best: np.ndarray
    ideal_worst: np.ndarray
    distance_best: np.ndarray
    distance_worst: np.ndarray
    closeness_coefficients: np.ndarray

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "rankings": self.rankings,
            "normalized_matrix": self.normalized_matrix.tolist(),
            "weighted_matrix": self.weighted_matrix.tolist(),
            "ideal_best": self.ideal_best.tolist(),
            "ideal_worst": self.ideal_worst.tolist(),
            "distance_best": self.distance_best.tolist(),
            "distance_worst": self.distance_worst.tolist(),
            "closeness_coefficients": self.closeness_coefficients.tolist(),
        }


class TOPSIS:
    """
    TOPSIS multi-criteria decision analysis.

    Usage::

        topsis = TOPSIS()
        result = topsis.rank(
            alternatives=["Supplier A", "Supplier B", "Supplier C"],
            criteria=["Carbon (kg CO₂-eq)", "Cost ($)", "Lead Time (days)", "Quality (1-10)"],
            decision_matrix=np.array([
                [100, 5000, 7, 8],    # Supplier A
                [150, 3000, 5, 9],    # Supplier B
                [80,  6000, 10, 7],   # Supplier C
            ]),
            weights=[0.4, 0.3, 0.2, 0.1],
            criteria_types=["cost", "cost", "cost", "benefit"],
        )
    """

    def rank(
        self,
        alternatives: list[str],
        criteria: list[str],
        decision_matrix: np.ndarray,
        weights: list[float],
        criteria_types: list[Literal["benefit", "cost"]],
    ) -> TOPSISResult:
        """
        Run full TOPSIS analysis.

        Args:
            alternatives: Names of alternatives (e.g., supplier names)
            criteria: Names of criteria
            decision_matrix: m×n matrix (m alternatives, n criteria)
            weights: Weight for each criterion (must sum to 1)
            criteria_types: "benefit" (higher=better) or "cost" (lower=better)

        Returns:
            TOPSISResult with rankings and all intermediate calculations
        """
        X = np.asarray(decision_matrix, dtype=np.float64)
        w = np.asarray(weights, dtype=np.float64)

        m, n = X.shape

        # Validate inputs
        if m != len(alternatives):
            raise ValueError(
                f"Number of alternatives ({len(alternatives)}) != matrix rows ({m})"
            )
        if n != len(criteria):
            raise ValueError(
                f"Number of criteria ({len(criteria)}) != matrix columns ({n})"
            )
        if n != len(weights):
            raise ValueError(
                f"Number of weights ({len(weights)}) != matrix columns ({n})"
            )
        if n != len(criteria_types):
            raise ValueError(
                f"Number of criteria_types ({len(criteria_types)}) != matrix columns ({n})"
            )

        # Normalize weights to sum to 1
        w = w / w.sum()

        # Step 1: Vector normalization  r_ij = x_ij / √(Σ_i x_ij²)
        col_norms = np.sqrt((X ** 2).sum(axis=0))
        col_norms[col_norms == 0] = 1  # Prevent division by zero
        R = X / col_norms

        # Step 2: Weighted normalized matrix  v_ij = w_j · r_ij
        V = R * w

        # Step 3: Ideal best and worst
        ideal_best = np.zeros(n)
        ideal_worst = np.zeros(n)
        for j in range(n):
            if criteria_types[j] == "benefit":
                ideal_best[j] = V[:, j].max()
                ideal_worst[j] = V[:, j].min()
            else:  # cost
                ideal_best[j] = V[:, j].min()
                ideal_worst[j] = V[:, j].max()

        # Step 4: Euclidean distances
        d_best = np.sqrt(((V - ideal_best) ** 2).sum(axis=1))
        d_worst = np.sqrt(((V - ideal_worst) ** 2).sum(axis=1))

        # Step 5: Relative closeness coefficient  C_i = d_i⁻ / (d_i⁺ + d_i⁻)
        denominator = d_best + d_worst
        denominator[denominator == 0] = 1  # Prevent division by zero
        C = d_worst / denominator

        # Build rankings
        sorted_indices = np.argsort(-C)  # Descending
        rankings = []
        for rank_pos, idx in enumerate(sorted_indices):
            rankings.append({
                "rank": rank_pos + 1,
                "alternative": alternatives[idx],
                "closeness_coefficient": round(float(C[idx]), 6),
                "distance_to_best": round(float(d_best[idx]), 6),
                "distance_to_worst": round(float(d_worst[idx]), 6),
                "scores": {
                    criteria[j]: round(float(X[idx, j]), 4)
                    for j in range(n)
                },
            })

        return TOPSISResult(
            rankings=rankings,
            normalized_matrix=R,
            weighted_matrix=V,
            ideal_best=ideal_best,
            ideal_worst=ideal_worst,
            distance_best=d_best,
            distance_worst=d_worst,
            closeness_coefficients=C,
        )

    def rank_suppliers(
        self,
        suppliers: list[dict[str, Any]],
        weights: list[float] | None = None,
    ) -> TOPSISResult:
        """
        Convenience method for supplier ranking.

        Args:
            suppliers: List of dicts with keys:
                name, carbon, cost, lead_time, quality
            weights: [carbon_w, cost_w, lead_time_w, quality_w]
                     Default: [0.4, 0.3, 0.2, 0.1]
        """
        if weights is None:
            weights = [0.4, 0.3, 0.2, 0.1]

        alternatives = [s["name"] for s in suppliers]
        criteria = [
            "Carbon Footprint (kg CO₂-eq)",
            "Cost ($)",
            "Lead Time (days)",
            "Quality Score",
        ]

        matrix = np.array([
            [s["carbon"], s["cost"], s["lead_time"], s["quality"]]
            for s in suppliers
        ], dtype=np.float64)

        return self.rank(
            alternatives=alternatives,
            criteria=criteria,
            decision_matrix=matrix,
            weights=weights,
            criteria_types=["cost", "cost", "cost", "benefit"],
        )

    def rank_materials(
        self,
        materials: list[dict[str, Any]],
        weights: list[float] | None = None,
    ) -> TOPSISResult:
        """
        Convenience method for material selection.

        Args:
            materials: List of dicts with keys:
                name, carbon_footprint, cost, recyclability, durability
            weights: Default [0.35, 0.25, 0.25, 0.15]
        """
        if weights is None:
            weights = [0.35, 0.25, 0.25, 0.15]

        alternatives = [m["name"] for m in materials]
        criteria = [
            "Carbon Footprint (kg CO₂-eq)",
            "Cost ($)",
            "Recyclability (%)",
            "Durability (years)",
        ]

        matrix = np.array([
            [
                m["carbon_footprint"],
                m["cost"],
                m["recyclability"],
                m["durability"],
            ]
            for m in materials
        ], dtype=np.float64)

        return self.rank(
            alternatives=alternatives,
            criteria=criteria,
            decision_matrix=matrix,
            weights=weights,
            criteria_types=["cost", "cost", "benefit", "benefit"],
        )
