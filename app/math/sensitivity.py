"""
Perturbation-Based Sensitivity Analysis for LCA

Computes analytical partial derivatives of impact h with respect to
each element of A and B matrices using matrix perturbation theory.

    ∂(A⁻¹)/∂A_ij = −A⁻¹ · E_ij · A⁻¹
    ∂h/∂A_ij     = Q · B · (−A⁻¹ · E_ij · A⁻¹) · f
    ∂h/∂B_kl     = Q · E_kl · A⁻¹ · f

    Sensitivity Ratio:
    SR_ij = (∂h/∂p_ij) · (p_ij / h)

    Where E_ij is the elementary matrix with 1 at position (i,j) and 0 elsewhere.

References:
    Heijungs, R. & Suh, S. (2002). The Computational Structure of Life Cycle Assessment.
    ISO 14044:2006 — Sensitivity analysis requirements.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy.linalg import inv

logger = logging.getLogger(__name__)


@dataclass
class SensitivityResult:
    """Complete sensitivity analysis result."""
    # Sensitivity of each A element
    sensitivity_A: dict[str, float] = field(default_factory=dict)
    # Sensitivity of each B element
    sensitivity_B: dict[str, float] = field(default_factory=dict)
    # Sensitivity ratios (normalized)
    sensitivity_ratios: dict[str, float] = field(default_factory=dict)
    # Tornado chart data (top parameters)
    tornado_data: list[dict[str, Any]] = field(default_factory=list)
    # Contribution analysis
    contributions: list[dict[str, Any]] = field(default_factory=list)
    # Perturbation results (±variation)
    perturbation_results: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "sensitivity_A": self.sensitivity_A,
            "sensitivity_B": self.sensitivity_B,
            "sensitivity_ratios": self.sensitivity_ratios,
            "tornado_data": self.tornado_data,
            "contributions": self.contributions,
            "perturbation_results": self.perturbation_results,
        }


class SensitivityAnalysis:
    """
    Matrix perturbation-based sensitivity analysis for LCA.

    Usage::

        from app.math.matrix_lca import TechnologyMatrix
        tm = TechnologyMatrix.from_supply_chain(data)

        sa = SensitivityAnalysis()
        result = sa.analyze(tm.A, tm.B, tm.Q, demand_vector, tm.processes)
    """

    def compute_sensitivity_A(
        self,
        A: np.ndarray,
        B: np.ndarray,
        Q: np.ndarray,
        f: np.ndarray,
    ) -> dict[tuple[int, int], float]:
        """
        Compute ∂h/∂A_ij for all (i,j) in the technology matrix.

        Uses: ∂(A⁻¹)/∂A_ij = −A⁻¹ · E_ij · A⁻¹
        So:   ∂h/∂A_ij = Q · B · (−A⁻¹ · E_ij · A⁻¹) · f
        """
        n = A.shape[0]
        A_inv = inv(A)
        s = A_inv @ f  # scaling vector

        sensitivities: dict[tuple[int, int], float] = {}

        for i in range(n):
            for j in range(n):
                # Elementary matrix E_ij
                E = np.zeros_like(A)
                E[i, j] = 1.0

                # ∂(A⁻¹)/∂A_ij = -A⁻¹ · E_ij · A⁻¹
                dA_inv = -A_inv @ E @ A_inv

                # ∂h/∂A_ij = Q · B · dA_inv · f
                dh = Q @ B @ dA_inv @ f
                sensitivities[(i, j)] = float(np.sum(dh))

        return sensitivities

    def compute_sensitivity_B(
        self,
        A: np.ndarray,
        B: np.ndarray,
        Q: np.ndarray,
        f: np.ndarray,
    ) -> dict[tuple[int, int], float]:
        """
        Compute ∂h/∂B_kl for all (k,l) in the biosphere matrix.

        Direct: ∂h/∂B_kl = Q · E_kl · A⁻¹ · f
        """
        m, n = B.shape
        A_inv = inv(A)
        s = A_inv @ f

        sensitivities: dict[tuple[int, int], float] = {}

        for k in range(m):
            for l in range(n):
                # ∂h/∂B_kl = Q · E_kl · s
                # Which simplifies to: Q[:, k] * s[l]
                dh = Q[:, k] * s[l]
                sensitivities[(k, l)] = float(np.sum(dh))

        return sensitivities

    def compute_sensitivity_ratios(
        self,
        A: np.ndarray,
        B: np.ndarray,
        Q: np.ndarray,
        f: np.ndarray,
    ) -> dict[str, float]:
        """
        Compute dimensionless sensitivity ratios for all parameters.

        SR_ij = (∂h/∂p_ij) · (p_ij / h)

        A ratio > 1 means the output is more sensitive than the input change.
        """
        # Compute total impact h
        s = inv(A) @ f
        g = B @ s
        h = float(np.sum(Q @ g))

        if abs(h) < 1e-15:
            logger.warning("Total impact is near zero; sensitivity ratios undefined")
            return {}

        ratios: dict[str, float] = {}

        # A sensitivities
        sens_A = self.compute_sensitivity_A(A, B, Q, f)
        for (i, j), dh in sens_A.items():
            p = A[i, j]
            if abs(p) > 1e-15:
                sr = dh * (p / h)
                ratios[f"A[{i},{j}]"] = round(sr, 6)

        # B sensitivities
        sens_B = self.compute_sensitivity_B(A, B, Q, f)
        for (k, l), dh in sens_B.items():
            p = B[k, l]
            if abs(p) > 1e-15:
                sr = dh * (p / h)
                ratios[f"B[{k},{l}]"] = round(sr, 6)

        return ratios

    def tornado_chart_data(
        self,
        A: np.ndarray,
        B: np.ndarray,
        Q: np.ndarray,
        f: np.ndarray,
        process_names: list[str] | None = None,
        variation: float = 0.10,
        top_n: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Generate data for tornado diagram.

        For each parameter, compute impact with ±variation (default ±10%)
        and measure the swing in total impact.
        """
        n_proc = A.shape[0]
        m_emis = B.shape[0]

        # Baseline impact
        s = inv(A) @ f
        h_base = float(np.sum(Q @ B @ s))

        tornado: list[dict[str, Any]] = []

        # Test B diagonal elements (emission factors) — usually most impactful
        for k in range(m_emis):
            for l in range(n_proc):
                if abs(B[k, l]) < 1e-15:
                    continue

                original = B[k, l]

                # Low scenario
                B_low = B.copy()
                B_low[k, l] = original * (1 - variation)
                h_low = float(np.sum(Q @ B_low @ s))

                # High scenario
                B_high = B.copy()
                B_high[k, l] = original * (1 + variation)
                h_high = float(np.sum(Q @ B_high @ s))

                swing = abs(h_high - h_low)
                name = (
                    process_names[l] if process_names and l < len(process_names)
                    else f"Process_{l}"
                )

                tornado.append({
                    "parameter": f"EF: {name}",
                    "param_key": f"B[{k},{l}]",
                    "base_value": round(original, 4),
                    "low_impact": round(h_low, 4),
                    "high_impact": round(h_high, 4),
                    "base_impact": round(h_base, 4),
                    "swing": round(swing, 4),
                    "swing_percent": round(swing / max(abs(h_base), 1e-10) * 100, 2),
                })

        # Sort by swing (descending) and take top N
        tornado.sort(key=lambda x: x["swing"], reverse=True)
        return tornado[:top_n]

    def contribution_analysis(
        self,
        A: np.ndarray,
        B: np.ndarray,
        Q: np.ndarray,
        f: np.ndarray,
        process_names: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Identify which process contributes most to total impact.
        Returns ranked list of processes by contribution percentage.
        """
        n = A.shape[0]
        s = inv(A) @ f

        contributions = []
        total = 0.0

        for j in range(n):
            proc_emissions = B[:, j] * s[j]
            proc_impact = float(np.sum(Q @ proc_emissions))
            total += abs(proc_impact)
            name = (
                process_names[j] if process_names and j < len(process_names)
                else f"Process_{j}"
            )
            contributions.append({
                "process": name,
                "impact": round(proc_impact, 4),
                "amount": round(float(f[j]), 4) if j < len(f) else 0,
            })

        # Add percentages
        for c in contributions:
            c["percentage"] = round(abs(c["impact"]) / max(total, 1e-10) * 100, 2)

        # Sort by absolute impact
        contributions.sort(key=lambda x: abs(x["impact"]), reverse=True)
        return contributions

    def analyze(
        self,
        A: np.ndarray,
        B: np.ndarray,
        Q: np.ndarray,
        f: np.ndarray,
        process_names: list[str] | None = None,
        variation: float = 0.10,
        top_n: int = 10,
    ) -> SensitivityResult:
        """Run complete sensitivity analysis."""
        sens_A = {
            f"A[{i},{j}]": v
            for (i, j), v in self.compute_sensitivity_A(A, B, Q, f).items()
        }
        sens_B = {
            f"B[{k},{l}]": v
            for (k, l), v in self.compute_sensitivity_B(A, B, Q, f).items()
        }
        ratios = self.compute_sensitivity_ratios(A, B, Q, f)
        tornado = self.tornado_chart_data(A, B, Q, f, process_names, variation, top_n)
        contribs = self.contribution_analysis(A, B, Q, f, process_names)

        return SensitivityResult(
            sensitivity_A=sens_A,
            sensitivity_B=sens_B,
            sensitivity_ratios=ratios,
            tornado_data=tornado,
            contributions=contribs,
        )
