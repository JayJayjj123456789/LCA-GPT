"""
Advanced Chart Generators for LCA-GPT

Additional Plotly visualizations for:
- Monte Carlo distribution histograms with confidence interval bands
- Tornado diagrams for sensitivity analysis
- TOPSIS radar charts for multi-criteria comparison
- Waterfall charts for cumulative emissions
- Convergence plots for Monte Carlo and non-linear iterations
- Linear vs Non-linear comparison charts
"""

from __future__ import annotations

from typing import Any

import numpy as np
import plotly.graph_objects as go

# ── Reuse design tokens from analytics.py ───────────────────────────────────
BG          = "rgba(0,0,0,0)"
SURFACE     = "#1c2116"
SURFACE_HI  = "#272c20"
SURFACE_TOP = "#31372a"
TEXT_PRI    = "#e0e5d3"
TEXT_SEC    = "#c4c8be"
TEXT_DIM    = "#8e9289"
PRIMARY     = "#b9ccb0"
TERTIARY    = "#bfcd8f"
ERROR       = "#c66b3d"
GRID_LINE   = "rgba(68,72,65,0.35)"
FONT_SANS   = "Plus Jakarta Sans, system-ui, sans-serif"
FONT_SERIF  = "Literata, Georgia, serif"

_BASE_LAYOUT = dict(
    paper_bgcolor=BG,
    plot_bgcolor=BG,
    font=dict(family=FONT_SANS, color=TEXT_SEC, size=12),
    title=dict(
        font=dict(family=FONT_SERIF, color=TEXT_PRI, size=15),
        x=0.0, xanchor="left",
        pad=dict(l=4, t=2),
    ),
    margin=dict(t=44, b=40, l=56, r=24),
    hoverlabel=dict(
        bgcolor=SURFACE_HI,
        bordercolor=SURFACE_TOP,
        font=dict(family=FONT_SANS, color=TEXT_PRI, size=12),
    ),
)

_AXIS_STYLE = dict(
    gridcolor=GRID_LINE,
    zerolinecolor=GRID_LINE,
    tickfont=dict(family=FONT_SANS, color=TEXT_DIM, size=11),
    linecolor=SURFACE_TOP,
    linewidth=1,
)

# ── Color palettes ──────────────────────────────────────────────────────────
PALETTE = [
    "#919e65", "#b9ccb0", "#bfcd8f", "#c66b3d",
    "#7c3307", "#6b8f5e", "#d4a574", "#8b9d83",
    "#a8c090", "#e8c87a",
]


def monte_carlo_histogram(
    distribution: list[float] | np.ndarray,
    mean: float,
    ci_95: tuple[float, float],
    title: str = "Monte Carlo Uncertainty Distribution",
) -> go.Figure:
    """Histogram of Monte Carlo simulation results with CI bands."""
    dist = np.asarray(distribution)

    fig = go.Figure()

    # Histogram
    fig.add_trace(go.Histogram(
        x=dist,
        nbinsx=50,
        marker=dict(
            color="rgba(145,158,101,0.65)",
            line=dict(color="rgba(145,158,101,0.9)", width=1),
        ),
        name="Simulations",
        hovertemplate="Range: %{x:.1f}<br>Count: %{y}<extra></extra>",
    ))

    # Mean line
    fig.add_vline(
        x=mean,
        line=dict(color=TEXT_PRI, width=2, dash="solid"),
        annotation_text=f"Mean: {mean:,.1f}",
        annotation_position="top",
        annotation_font=dict(color=TEXT_PRI, size=11),
    )

    # 95% CI bands
    fig.add_vrect(
        x0=ci_95[0], x1=ci_95[1],
        fillcolor="rgba(185,204,176,0.12)",
        line_width=0,
        annotation_text="95% CI",
        annotation_position="top left",
        annotation_font=dict(color=TEXT_DIM, size=10),
    )
    fig.add_vline(x=ci_95[0], line=dict(color=PRIMARY, width=1, dash="dash"))
    fig.add_vline(x=ci_95[1], line=dict(color=PRIMARY, width=1, dash="dash"))

    fig.update_layout(
        **_BASE_LAYOUT,
        title_text=title,
        height=380,
        xaxis=dict(
            **_AXIS_STYLE,
            title=dict(text="kg CO₂-eq", font=dict(color=TEXT_DIM, size=11)),
        ),
        yaxis=dict(
            **_AXIS_STYLE,
            title=dict(text="Frequency", font=dict(color=TEXT_DIM, size=11)),
        ),
        showlegend=False,
        bargap=0.05,
    )

    return fig


def tornado_chart(
    tornado_data: list[dict[str, Any]],
    title: str = "Sensitivity Analysis — Tornado Diagram",
) -> go.Figure:
    """Tornado diagram showing parameter sensitivity (±10% variation)."""
    if not tornado_data:
        return _empty("No sensitivity data available")

    # Sort by swing
    data = sorted(tornado_data, key=lambda x: x["swing"])

    labels = [d["parameter"] for d in data]
    base = data[0]["base_impact"] if data else 0
    low_vals = [d["low_impact"] - base for d in data]
    high_vals = [d["high_impact"] - base for d in data]

    fig = go.Figure()

    # Low bars (negative direction)
    fig.add_trace(go.Bar(
        y=labels,
        x=low_vals,
        orientation="h",
        name="−10%",
        marker_color="rgba(145,158,101,0.7)",
        hovertemplate="%{y}<br>−10%: %{customdata:.1f} kg CO₂-eq<extra></extra>",
        customdata=[d["low_impact"] for d in data],
    ))

    # High bars (positive direction)
    fig.add_trace(go.Bar(
        y=labels,
        x=high_vals,
        orientation="h",
        name="+10%",
        marker_color="rgba(198,107,61,0.7)",
        hovertemplate="%{y}<br>+10%: %{customdata:.1f} kg CO₂-eq<extra></extra>",
        customdata=[d["high_impact"] for d in data],
    ))

    fig.update_layout(
        **_BASE_LAYOUT,
        title_text=title,
        height=max(300, 50 + len(data) * 42),
        barmode="overlay",
        xaxis=dict(
            **_AXIS_STYLE,
            title=dict(
                text="Δ Impact (kg CO₂-eq)",
                font=dict(color=TEXT_DIM, size=11),
            ),
            zeroline=True,
        ),
        yaxis=dict(**_AXIS_STYLE, showgrid=False, automargin=True),
        legend=dict(
            font=dict(color=TEXT_SEC, size=11),
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="bottom", y=1.02,
        ),
    )

    return fig


def topsis_radar_chart(
    rankings: list[dict[str, Any]],
    criteria: list[str],
    title: str = "TOPSIS Multi-Criteria Comparison",
) -> go.Figure:
    """Radar chart comparing alternatives across criteria."""
    if not rankings:
        return _empty("No ranking data available")

    fig = go.Figure()

    for i, alt in enumerate(rankings[:6]):  # Max 6 alternatives
        scores = alt.get("scores", {})
        values = [scores.get(c, 0) for c in criteria]

        # Normalize to 0-1 range for radar
        max_vals = []
        for c in criteria:
            all_vals = [r["scores"].get(c, 0) for r in rankings]
            max_vals.append(max(all_vals) if all_vals else 1)

        normalized = [
            v / max(m, 1e-10) for v, m in zip(values, max_vals)
        ]
        # Close the polygon
        normalized.append(normalized[0])
        theta = criteria + [criteria[0]]

        fig.add_trace(go.Scatterpolar(
            r=normalized,
            theta=theta,
            fill="toself",
            fillcolor=f"rgba({','.join(str(int(c)) for c in _hex_to_rgb(PALETTE[i % len(PALETTE)]))},0.1)",
            line=dict(color=PALETTE[i % len(PALETTE)], width=2),
            name=f"#{alt['rank']} {alt['alternative']} (C={alt['closeness_coefficient']:.3f})",
            hovertemplate="%{theta}: %{r:.2f}<extra></extra>",
        ))

    fig.update_layout(
        **_BASE_LAYOUT,
        title_text=title,
        height=420,
        polar=dict(
            bgcolor=BG,
            radialaxis=dict(
                visible=True,
                range=[0, 1.1],
                gridcolor=GRID_LINE,
                tickfont=dict(color=TEXT_DIM, size=9),
            ),
            angularaxis=dict(
                tickfont=dict(color=TEXT_SEC, size=11),
                gridcolor=GRID_LINE,
            ),
        ),
        legend=dict(
            font=dict(color=TEXT_SEC, size=11),
            bgcolor="rgba(28,33,22,0.8)",
            bordercolor=SURFACE_TOP,
            borderwidth=1,
        ),
    )

    return fig


def convergence_plot(
    convergence_data: list[dict[str, Any]],
    x_key: str = "n",
    y_key: str = "mean",
    ci_low_key: str = "ci_95_low",
    ci_high_key: str = "ci_95_high",
    title: str = "Monte Carlo Convergence",
    x_label: str = "Simulations",
    y_label: str = "Mean Impact (kg CO₂-eq)",
) -> go.Figure:
    """Convergence plot showing stability over iterations."""
    if not convergence_data:
        return _empty("No convergence data")

    x = [d[x_key] for d in convergence_data]
    y = [d[y_key] for d in convergence_data]

    fig = go.Figure()

    # CI band (if available)
    if ci_low_key in convergence_data[0] and ci_high_key in convergence_data[0]:
        ci_low = [d[ci_low_key] for d in convergence_data]
        ci_high = [d[ci_high_key] for d in convergence_data]

        fig.add_trace(go.Scatter(
            x=x + x[::-1],
            y=ci_high + ci_low[::-1],
            fill="toself",
            fillcolor="rgba(185,204,176,0.12)",
            line=dict(color="rgba(0,0,0,0)"),
            name="95% CI",
            hoverinfo="skip",
        ))

    # Mean line
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="lines+markers",
        line=dict(color=PRIMARY, width=2),
        marker=dict(size=5, color=PRIMARY),
        name="Mean",
        hovertemplate=f"{x_label}: %{{x}}<br>Mean: %{{y:,.2f}}<extra></extra>",
    ))

    fig.update_layout(
        **_BASE_LAYOUT,
        title_text=title,
        height=350,
        xaxis=dict(
            **_AXIS_STYLE,
            title=dict(text=x_label, font=dict(color=TEXT_DIM, size=11)),
        ),
        yaxis=dict(
            **_AXIS_STYLE,
            title=dict(text=y_label, font=dict(color=TEXT_DIM, size=11)),
        ),
        legend=dict(
            font=dict(color=TEXT_SEC, size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
    )

    return fig


def waterfall_chart(
    contributions: list[dict[str, Any]],
    title: str = "Cumulative Emissions by Process",
) -> go.Figure:
    """Waterfall chart showing each process's contribution to total impact."""
    if not contributions:
        return _empty("No contribution data")

    names = [c["process"] for c in contributions]
    values = [c["impact"] for c in contributions]
    total = sum(values)

    # Build measure types for waterfall
    measures = ["relative"] * len(names) + ["total"]
    names.append("Total")
    values.append(total)

    fig = go.Figure(go.Waterfall(
        name="Impact",
        orientation="v",
        measure=measures,
        x=names,
        y=values,
        connector=dict(line=dict(color=GRID_LINE, width=1)),
        increasing=dict(marker=dict(color="rgba(198,107,61,0.75)")),
        decreasing=dict(marker=dict(color="rgba(145,158,101,0.75)")),
        totals=dict(marker=dict(color="rgba(185,204,176,0.8)")),
        textposition="outside",
        text=[f"{v:,.1f}" for v in values],
        textfont=dict(family=FONT_SANS, color=TEXT_DIM, size=10),
        hovertemplate="%{x}<br>%{y:,.2f} kg CO₂-eq<extra></extra>",
    ))

    fig.update_layout(
        **_BASE_LAYOUT,
        title_text=title,
        height=400,
        xaxis=dict(**_AXIS_STYLE, tickangle=-30, automargin=True),
        yaxis=dict(
            **_AXIS_STYLE,
            title=dict(text="kg CO₂-eq", font=dict(color=TEXT_DIM, size=11)),
        ),
        showlegend=False,
    )

    return fig


def linear_vs_nonlinear_chart(
    comparison: dict[str, Any],
    title: str = "Linear vs Non-Linear LCA Comparison",
) -> go.Figure:
    """Grouped bar chart comparing linear and non-linear per-process impacts."""
    processes = comparison.get("process_comparison", [])
    if not processes:
        return _empty("No comparison data")

    names = [p["process"][:25] for p in processes]
    linear = [p["linear_impact"] for p in processes]
    nonlinear = [p["nonlinear_impact"] for p in processes]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=names, y=linear,
        name="Linear Model",
        marker_color="rgba(185,204,176,0.7)",
        hovertemplate="%{x}<br>Linear: %{y:,.2f}<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        x=names, y=nonlinear,
        name="Non-Linear Model",
        marker_color="rgba(198,107,61,0.7)",
        hovertemplate="%{x}<br>Non-Linear: %{y:,.2f}<extra></extra>",
    ))

    fig.update_layout(
        **_BASE_LAYOUT,
        title_text=title,
        height=400,
        barmode="group",
        xaxis=dict(**_AXIS_STYLE, tickangle=-30, automargin=True),
        yaxis=dict(
            **_AXIS_STYLE,
            title=dict(text="kg CO₂-eq", font=dict(color=TEXT_DIM, size=11)),
        ),
        legend=dict(
            font=dict(color=TEXT_SEC, size=11),
            bgcolor="rgba(28,33,22,0.8)",
            bordercolor=SURFACE_TOP,
            borderwidth=1,
            orientation="h",
            yanchor="bottom", y=1.02,
        ),
    )

    # Add deviation annotation
    dev = comparison.get("deviation_percent", 0)
    fig.add_annotation(
        text=f"Total deviation: {dev:+.1f}%",
        xref="paper", yref="paper",
        x=1, y=-0.15,
        showarrow=False,
        font=dict(family=FONT_SANS, color=TERTIARY, size=11),
        xanchor="right",
    )

    return fig


def contribution_treemap(
    contributions: list[dict[str, Any]],
    title: str = "Emission Contribution Breakdown",
) -> go.Figure:
    """Treemap showing hierarchical emission breakdown."""
    if not contributions:
        return _empty("No contribution data")

    labels = [c["process"] for c in contributions]
    values = [abs(c["impact"]) for c in contributions]
    percentages = [c.get("percentage", 0) for c in contributions]

    colors = []
    max_val = max(values) if values else 1
    for v in values:
        ratio = v / max_val
        r = int(145 + ratio * (198 - 145))
        g = int(158 - ratio * (158 - 107))
        b = int(101 - ratio * (101 - 61))
        colors.append(f"rgba({r},{g},{b},0.8)")

    fig = go.Figure(go.Treemap(
        labels=labels,
        values=values,
        parents=[""] * len(labels),
        marker=dict(colors=colors, line=dict(color=SURFACE, width=2)),
        texttemplate="<b>%{label}</b><br>%{value:,.1f} kg CO₂-eq<br>%{percentParent:.1%}",
        textfont=dict(family=FONT_SANS, color=TEXT_PRI, size=12),
        hovertemplate="%{label}<br>%{value:,.2f} kg CO₂-eq<br>%{percentParent:.1%}<extra></extra>",
    ))

    fig.update_layout(
        **_BASE_LAYOUT,
        title_text=title,
        height=400,
        margin=dict(t=44, b=8, l=8, r=8),
    )

    return fig


# ── Utilities ───────────────────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _empty(message: str) -> go.Figure:
    """Branded empty state chart."""
    fig = go.Figure()
    fig.add_annotation(
        text=f"\U0001f331<br><br>{message}",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(family=FONT_SANS, color=TEXT_DIM, size=13),
        align="center",
    )
    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG,
        height=320,
        margin=dict(t=16, b=16, l=16, r=16),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig
