"""
Non-Linear Dynamic LCA Models

Extends beyond static linear models to handle real-world industrial processes
with scale-dependent and non-linear relationships.

    Instead of fixed A matrix:
    A_ij(x) = a_ij · f_ij(x_j)

    Where f_ij is a scale-dependent function:
    - Power law:    f(x) = x^α          (0 < α < 1 for economies of scale)
    - Logistic:     f(x) = K / (1 + e^(-r(x - x₀)))
    - Piecewise:    different coefficients at different production scales

    Equilibrium: solve A(s)·s = f iteratively
    s_{k+1} = A(s_k)⁻¹ · f
    Converge when ‖s_{k+1} − s_k‖ < ε

Motivation:
    - Economies of scale in material extraction
    - Non-linear chemical reaction yields
    - Diminishing returns in energy recovery
    - Threshold effects in waste treatment

References:
    Heijungs, R. (1994). A generic method for the identification of options
    for cleaner products. Ecological Economics, 10(1), 69-81.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
from scipy.linalg import inv

logger = logging.getLogger(__name__)


# ── Scale Functions ─────────────────────────────────────────────────────────

def power_law(x: float, alpha: float = 0.8, scale: float = 1.0) -> float:
    """
    Power law scaling: f(x) = scale · |x|^α

    α < 1: economies of scale (sublinear growth)
    α = 1: linear (no scale effect)
    α > 1: diseconomies of scale (superlinear growth)
    """
    return scale * (abs(x) ** alpha) if x != 0 else 0.0


def logistic(
    x: float, K: float = 1.0, r: float = 1.0, x0: float = 0.0
) -> float:
    """
    Logistic function: f(x) = K / (1 + e^(-r(x - x₀)))

    Models saturation effects — coefficient plateaus at high production.
    K: maximum capacity
    r: growth rate
    x0: midpoint
    """
    return K / (1 + np.exp(-r * (x - x0)))


def piecewise_linear(
    x: float,
    breakpoints: list[float] | None = None,
    slopes: list[float] | None = None,
) -> float:
    """
    Piecewise linear function with different coefficients at different scales.

    breakpoints: [100, 500, 1000]  — production thresholds
    slopes: [1.0, 0.8, 0.6, 0.5]  — coefficient at each interval
    """
    if breakpoints is None:
        breakpoints = [100, 500, 1000]
    if slopes is None:
        slopes = [1.0, 0.85, 0.7, 0.6]

    for i, bp in enumerate(breakpoints):
        if x <= bp:
            return slopes[i]
    return slopes[-1]


SCALE_FUNCTIONS: dict[str, Callable] = {
    "power": power_law,
    "logistic": logistic,
    "piecewise": piecewise_linear,
}


@dataclass
class NonLinearResult:
    """Result of non-linear LCA computation."""
    scaling_vector: np.ndarray
    linear_impact: float
    nonlinear_impact: float
    deviation_percent: float
    convergence_history: list[dict[str, Any]]
    iterations: int
    converged: bool
    scale_adjusted_A: np.ndarray

    def to_dict(self) -> dict:
        return {
            "scaling_vector": self.scaling_vector.tolist(),
            "linear_impact": round(self.linear_impact, 4),
            "nonlinear_impact": round(self.nonlinear_impact, 4),
            "deviation_percent": round(self.deviation_percent, 4),
            "convergence_history": self.convergence_history,
            "iterations": self.iterations,
            "converged": self.converged,
        }


class NonLinearLCA:
    """
    Non-linear dynamic LCA with scale-dependent technology matrix.

    Usage::

        nl = NonLinearLCA(n_processes=3)
        nl.set_base_matrix(A_base)
        nl.set_scale_function(0, 1, "power", alpha=0.8)
        result = nl.solve_equilibrium(B, Q, demand_vector)
    """

    def __init__(self, n_processes: int):
        self.n = n_processes
        self.base_A: np.ndarray = np.eye(n_processes, dtype=np.float64)
        self.scale_functions: dict[tuple[int, int], tuple[str, dict[str, Any]]] = {}
        self.process_names: list[str] = [f"Process_{i}" for i in range(n_processes)]

    def set_base_matrix(self, A: np.ndarray) -> None:
        """Set the base technology matrix A."""
        self.base_A = np.asarray(A, dtype=np.float64)

    def set_process_names(self, names: list[str]) -> None:
        """Set process names."""
        self.process_names = names

    def set_scale_function(
        self,
        i: int,
        j: int,
        func_type: str,
        **params: Any,
    ) -> None:
        """
        Define scale-dependent coefficient for A_ij.

        func_type: "power", "logistic", "piecewise"
        params: function-specific parameters
        """
        if func_type not in SCALE_FUNCTIONS:
            raise ValueError(
                f"Unknown function type '{func_type}'. "
                f"Available: {list(SCALE_FUNCTIONS.keys())}"
            )
        self.scale_functions[(i, j)] = (func_type, params)

    def set_auto_economies_of_scale(self, alpha: float = 0.85) -> None:
        """
        Auto-assign power law economies of scale to all off-diagonal
        elements of the technology matrix.
        """
        for i in range(self.n):
            for j in range(self.n):
                if i != j and abs(self.base_A[i, j]) > 1e-15:
                    self.scale_functions[(i, j)] = ("power", {"alpha": alpha})

    def build_A_at_scale(self, scaling_vector: np.ndarray) -> np.ndarray:
        """
        Build A(s) with scale-dependent coefficients.

        A_ij(s) = a_ij_base · f_ij(s_j)
        """
        A = self.base_A.copy()

        for (i, j), (func_type, params) in self.scale_functions.items():
            base_val = self.base_A[i, j]
            scale_input = scaling_vector[j]

            func = SCALE_FUNCTIONS[func_type]
            scale_factor = func(scale_input, **params)

            A[i, j] = base_val * scale_factor

        return A

    def solve_equilibrium(
        self,
        B: np.ndarray,
        Q: np.ndarray,
        demand_vector: np.ndarray,
        tol: float = 1e-8,
        max_iter: int = 100,
    ) -> NonLinearResult:
        """
        Find equilibrium scaling vector using iterative fixed-point method.

        Algorithm:
        1. Initialize s₀ = A_base⁻¹ · f (linear approximation)
        2. For k = 1, 2, ...:
             A_k = A(s_k)  — rebuild matrix at current scale
             s_{k+1} = A_k⁻¹ · f
        3. Stop when ‖s_{k+1} − s_k‖ < tol
        """
        f = np.asarray(demand_vector, dtype=np.float64)
        B = np.asarray(B, dtype=np.float64)
        Q = np.asarray(Q, dtype=np.float64)

        # Linear baseline
        s_linear = inv(self.base_A) @ f
        h_linear = float(np.sum(Q @ B @ s_linear))

        # Initialize with linear solution
        s = s_linear.copy()
        convergence: list[dict[str, Any]] = []
        converged = False

        for k in range(max_iter):
            # Build A at current scale
            A_k = self.build_A_at_scale(s)

            # Check for singularity
            try:
                s_new = inv(A_k) @ f
            except np.linalg.LinAlgError:
                logger.warning(f"Singular matrix at iteration {k}")
                break

            # Compute change
            delta = float(np.linalg.norm(s_new - s))
            h_current = float(np.sum(Q @ B @ s_new))

            convergence.append({
                "iteration": k,
                "delta": round(delta, 10),
                "impact": round(h_current, 4),
                "scaling_norm": round(float(np.linalg.norm(s_new)), 4),
            })

            s = s_new

            if delta < tol:
                converged = True
                logger.info(f"Converged after {k + 1} iterations (δ={delta:.2e})")
                break

        # Final impact
        A_final = self.build_A_at_scale(s)
        h_nonlinear = float(np.sum(Q @ B @ s))

        # Deviation from linear model
        deviation = (
            (h_nonlinear - h_linear) / abs(h_linear) * 100
            if abs(h_linear) > 1e-15
            else 0.0
        )

        return NonLinearResult(
            scaling_vector=s,
            linear_impact=h_linear,
            nonlinear_impact=h_nonlinear,
            deviation_percent=deviation,
            convergence_history=convergence,
            iterations=len(convergence),
            converged=converged,
            scale_adjusted_A=A_final,
        )

    def compare_linear_vs_nonlinear(
        self,
        B: np.ndarray,
        Q: np.ndarray,
        demand_vector: np.ndarray,
    ) -> dict[str, Any]:
        """
        Side-by-side comparison of linear and non-linear results.
        Useful for visualization and demonstrating why non-linear matters.
        """
        f = np.asarray(demand_vector, dtype=np.float64)

        # Linear
        s_linear = inv(self.base_A) @ f
        h_linear = float(np.sum(Q @ B @ s_linear))

        # Non-linear
        nl_result = self.solve_equilibrium(B, Q, f)

        # Per-process comparison
        process_comparison = []
        for j in range(self.n):
            name = self.process_names[j] if j < len(self.process_names) else f"Process_{j}"
            lin_contrib = float(np.sum(Q @ (B[:, j] * s_linear[j])))
            nl_contrib = float(np.sum(Q @ (B[:, j] * nl_result.scaling_vector[j])))
            process_comparison.append({
                "process": name,
                "linear_impact": round(lin_contrib, 4),
                "nonlinear_impact": round(nl_contrib, 4),
                "change_percent": round(
                    (nl_contrib - lin_contrib) / max(abs(lin_contrib), 1e-10) * 100, 2
                ),
            })

        return {
            "linear_total": round(h_linear, 4),
            "nonlinear_total": round(nl_result.nonlinear_impact, 4),
            "deviation_percent": round(nl_result.deviation_percent, 2),
            "iterations": nl_result.iterations,
            "converged": nl_result.converged,
            "process_comparison": process_comparison,
            "convergence_history": nl_result.convergence_history,
        }

    @classmethod
    def from_technology_matrix(cls, tm: Any) -> "NonLinearLCA":
        """
        Build NonLinearLCA from an existing TechnologyMatrix instance.
        Automatically applies power-law economies of scale.
        """
        nl = cls(n_processes=tm.n_processes)
        nl.set_base_matrix(tm.A)
        if hasattr(tm, "processes"):
            nl.set_process_names([p.name for p in tm.processes])
        nl.set_auto_economies_of_scale(alpha=0.85)
        return nl
