"""
Monte Carlo Simulation for Full-Chain LCA Uncertainty Propagation

Propagates parameter uncertainty through the complete matrix chain:

    h = Q · B · A⁻¹ · f

For each simulation run k = 1..N:
    1. Sample B_k from distribution of emission factors
    2. Sample A_k from distribution of technology coefficients
    3. Compute h_k = Q · B_k · A_k⁻¹ · f

Output:
    μ_h  = (1/N) Σ h_k                       Mean impact
    σ_h  = √((1/N) Σ (h_k − μ_h)²)          Standard deviation
    CI_95 = [μ_h − 1.96σ_h, μ_h + 1.96σ_h]  95% confidence interval

Supports: Normal, Lognormal, Uniform, Triangular distributions

References:
    ISO 14044:2006 — Uncertainty analysis in LCA
    Heijungs, R. & Suh, S. (2002). The Computational Structure of Life Cycle Assessment.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
from scipy import stats
from scipy.linalg import inv

logger = logging.getLogger(__name__)

DistType = Literal["normal", "lognormal", "uniform", "triangular"]


@dataclass
class ParameterDistribution:
    """Distribution specification for a single parameter."""
    dist_type: DistType
    mean: float
    std: float = 0.0
    low: float = 0.0
    high: float = 0.0
    mode: float = 0.0   # For triangular

    def sample(self, rng: np.random.Generator, n: int = 1) -> np.ndarray:
        """Draw n samples from this distribution."""
        if self.dist_type == "normal":
            return rng.normal(self.mean, max(self.std, 1e-10), size=n)
        elif self.dist_type == "lognormal":
            # Lognormal requires a positive mean; zero/negative values are undefined.
            if self.mean <= 0:
                raise ValueError(
                    f"Lognormal distribution requires mean > 0, got mean={self.mean}"
                )
            # Convert mean/std to lognormal parameters
            variance = max(self.std ** 2, 1e-20)
            mu_ln = np.log(self.mean ** 2 / np.sqrt(variance + self.mean ** 2))
            sigma_ln = np.sqrt(np.log(1 + variance / self.mean ** 2))
            return rng.lognormal(mu_ln, sigma_ln, size=n)
        elif self.dist_type == "uniform":
            return rng.uniform(self.low, self.high, size=n)
        elif self.dist_type == "triangular":
            return rng.triangular(self.low, self.mode, self.high, size=n)
        else:
            raise ValueError(f"Unknown distribution type: {self.dist_type}")


@dataclass
class UncertaintyResult:
    """Complete Monte Carlo simulation result."""
    mean: float
    std: float
    ci_95: tuple[float, float]
    ci_99: tuple[float, float]
    median: float
    n_simulations: int
    distribution: np.ndarray
    percentiles: dict[str, float]
    convergence: list[dict[str, float]]
    per_process_uncertainty: dict[str, dict[str, float]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "mean": round(self.mean, 4),
            "std": round(self.std, 4),
            "ci_95": [round(self.ci_95[0], 4), round(self.ci_95[1], 4)],
            "ci_99": [round(self.ci_99[0], 4), round(self.ci_99[1], 4)],
            "median": round(self.median, 4),
            "n_simulations": self.n_simulations,
            "distribution": self.distribution.tolist(),
            "percentiles": {
                k: round(v, 4) for k, v in self.percentiles.items()
            },
            "convergence": self.convergence,
            "per_process_uncertainty": self.per_process_uncertainty,
        }


class MonteCarloSimulation:
    """
    Full-chain Monte Carlo uncertainty propagation for LCA.

    Usage::

        from app.math.matrix_lca import TechnologyMatrix
        tm = TechnologyMatrix.from_supply_chain(data)

        mc = MonteCarloSimulation(tm)
        mc.set_emission_factor_uncertainty(
            process_idx=0, dist_type="normal", mean=2.5, std=0.3
        )
        result = mc.simulate(demand_vector, n_sim=10000)
    """

    def __init__(self, technology_matrix: Any):
        """
        Args:
            technology_matrix: TechnologyMatrix instance with A, B, Q set
        """
        self.model = technology_matrix
        self.A_distributions: dict[tuple[int, int], ParameterDistribution] = {}
        self.B_distributions: dict[tuple[int, int], ParameterDistribution] = {}

    def set_technology_uncertainty(
        self,
        i: int, j: int,
        dist_type: DistType = "normal",
        **kwargs: Any,
    ) -> None:
        """Set uncertainty distribution for A[i,j]."""
        if "mean" not in kwargs:
            kwargs["mean"] = float(self.model.A[i, j])
        self.A_distributions[(i, j)] = ParameterDistribution(
            dist_type=dist_type, **kwargs
        )

    def set_emission_factor_uncertainty(
        self,
        process_idx: int,
        dist_type: DistType = "normal",
        **kwargs: Any,
    ) -> None:
        """
        Set uncertainty for the emission factor of a process.
        Maps to B[process_idx, process_idx] in the diagonal biosphere matrix.
        """
        i = process_idx
        if "mean" not in kwargs:
            kwargs["mean"] = float(self.model.B[i, i])
        self.B_distributions[(i, i)] = ParameterDistribution(
            dist_type=dist_type, **kwargs
        )

    def set_auto_uncertainty(self, cv: float = 0.15) -> None:
        """
        Automatically assign normal distributions to all non-zero
        emission factors with a coefficient of variation (CV).

        Default CV = 15% (common for emission factor uncertainty).
        """
        B = self.model.B
        m, n = B.shape
        for i in range(m):
            for j in range(n):
                if B[i, j] != 0:
                    mean_val = float(B[i, j])
                    std_val = abs(mean_val * cv)
                    self.B_distributions[(i, j)] = ParameterDistribution(
                        dist_type="normal",
                        mean=mean_val,
                        std=std_val,
                    )

    def simulate(
        self,
        demand_vector: np.ndarray,
        n_sim: int = 10000,
        seed: int | None = None,
        convergence_checkpoints: int = 20,
    ) -> UncertaintyResult:
        """
        Run full-chain Monte Carlo simulation.

        h_k = Q · B_k · A_k⁻¹ · f  for k = 1..n_sim
        """
        rng = np.random.default_rng(seed)
        demand = np.asarray(demand_vector, dtype=np.float64)

        A_base = self.model.A.copy()
        B_base = self.model.B.copy()
        Q = self.model.Q

        results = np.zeros(n_sim, dtype=np.float64)
        convergence: list[dict[str, float]] = []
        checkpoint_interval = max(1, n_sim // convergence_checkpoints)

        # Per-process results for breakdown
        n_processes = self.model.n_processes
        process_results = np.zeros((n_sim, n_processes), dtype=np.float64)

        for k in range(n_sim):
            # Sample A
            A_k = A_base.copy()
            for (i, j), dist in self.A_distributions.items():
                A_k[i, j] = dist.sample(rng, 1)[0]

            # Sample B
            B_k = B_base.copy()
            for (i, j), dist in self.B_distributions.items():
                sampled = dist.sample(rng, 1)[0]
                B_k[i, j] = max(0, sampled)  # Emission factors can't be negative

            # Compute h_k = Q · B_k · A_k⁻¹ · f
            try:
                s_k = inv(A_k) @ demand
                g_k = B_k @ s_k
                h_k = Q @ g_k
                results[k] = float(np.sum(h_k))

                # Per-process contributions
                for j in range(n_processes):
                    process_emissions = B_k[:, j] * s_k[j]
                    process_results[k, j] = float(np.sum(Q @ process_emissions))
            except np.linalg.LinAlgError:
                # Singular matrix — use previous result or NaN
                results[k] = results[k - 1] if k > 0 else np.nan
                logger.warning(f"Singular matrix at simulation {k}")

            # Convergence checkpoint
            if (k + 1) % checkpoint_interval == 0:
                running_mean = float(np.nanmean(results[:k+1]))
                running_std = float(np.nanstd(results[:k+1]))
                convergence.append({
                    "n": k + 1,
                    "mean": round(running_mean, 4),
                    "std": round(running_std, 4),
                    "ci_95_low": round(running_mean - 1.96 * running_std, 4),
                    "ci_95_high": round(running_mean + 1.96 * running_std, 4),
                })

        # Filter out NaN
        valid = results[~np.isnan(results)]
        if len(valid) == 0:
            raise RuntimeError("All simulations failed")

        mean_h = float(np.mean(valid))
        std_h = float(np.std(valid))
        median_h = float(np.median(valid))

        ci_95 = (
            float(np.percentile(valid, 2.5)),
            float(np.percentile(valid, 97.5)),
        )
        ci_99 = (
            float(np.percentile(valid, 0.5)),
            float(np.percentile(valid, 99.5)),
        )

        percentiles = {
            "p5": float(np.percentile(valid, 5)),
            "p10": float(np.percentile(valid, 10)),
            "p25": float(np.percentile(valid, 25)),
            "p50": float(np.percentile(valid, 50)),
            "p75": float(np.percentile(valid, 75)),
            "p90": float(np.percentile(valid, 90)),
            "p95": float(np.percentile(valid, 95)),
        }

        # Per-process uncertainty
        per_process: dict[str, dict[str, float]] = {}
        for j in range(n_processes):
            col = process_results[:, j]
            col_valid = col[~np.isnan(col)]
            name = (
                self.model.processes[j].name
                if j < len(self.model.processes)
                else f"Process_{j}"
            )
            per_process[name] = {
                "mean": round(float(np.mean(col_valid)), 4),
                "std": round(float(np.std(col_valid)), 4),
                "cv": round(float(np.std(col_valid) / max(abs(np.mean(col_valid)), 1e-10)), 4),
            }

        return UncertaintyResult(
            mean=mean_h,
            std=std_h,
            ci_95=ci_95,
            ci_99=ci_99,
            median=median_h,
            n_simulations=len(valid),
            distribution=valid,
            percentiles=percentiles,
            convergence=convergence,
            per_process_uncertainty=per_process,
        )
