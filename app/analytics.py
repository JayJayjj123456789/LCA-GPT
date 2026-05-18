import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Biophilic Enterprise Design Tokens ───────────────────────────────────────
BG          = "rgba(0,0,0,0)"          # transparent — card provides background
SURFACE     = "#1c2116"
SURFACE_HI  = "#272c20"
SURFACE_TOP = "#31372a"
TEXT_PRI    = "#e0e5d3"
TEXT_SEC    = "#c4c8be"
TEXT_DIM    = "#8e9289"
PRIMARY     = "#b9ccb0"                # sage green
TERTIARY    = "#bfcd8f"                # ochre
ERROR       = "#c66b3d"                # deep terracotta
GRID_LINE   = "rgba(68,72,65,0.35)"
FONT_SANS   = "Plus Jakarta Sans, system-ui, sans-serif"
FONT_SERIF  = "Literata, Georgia, serif"

_BASE_LAYOUT = dict(
    paper_bgcolor=BG,
    plot_bgcolor=BG,
    font=dict(family=FONT_SANS, color=TEXT_SEC, size=12),
    title=dict(
        font=dict(family=FONT_SERIF, color=TEXT_PRI, size=15),
        x=0.0,
        xanchor="left",
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


def carbon_hotspot_chart(materials: list[dict]) -> go.Figure:
    """Horizontal bar chart — material-level carbon hotspots, Biophilic style."""
    if not materials:
        return empty_chart("No material data available")

    df = pd.DataFrame(materials)
    df["subtotal"] = df["amount"] * df["emission_factor"]
    df = df.sort_values("subtotal", ascending=True)
    df["label"] = df["name"].str.slice(0, 38).str.strip()

    max_val = df["subtotal"].max() or 1

    # Gradient: low=sage, high=terracotta
    def make_color(ratio: float) -> str:
        if ratio < 0.5:
            r = int(139 + ratio * 2 * (185 - 139))
            g = int(157 + ratio * 2 * (107 - 157))
            b = int(131 + ratio * 2 * (61 - 131))
        else:
            r = int(185 + (ratio - 0.5) * 2 * (198 - 185))
            g = int(107 - (ratio - 0.5) * 2 * 60)
            b = int(61  - (ratio - 0.5) * 2 * 30)
        return f"rgba({r},{g},{b},0.88)"

    bar_colors = [make_color(v / max_val) for v in df["subtotal"].tolist()]

    fig = go.Figure(
        go.Bar(
            x=df["subtotal"],
            y=df["label"],
            orientation="h",
            marker=dict(
                color=bar_colors,
                line=dict(width=0),
            ),
            text=df["subtotal"].apply(lambda v: f"{v:,.1f}"),
            textposition="outside",
            textfont=dict(family=FONT_SANS, color=TEXT_DIM, size=11),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Carbon: <b>%{x:,.2f} kgCO\u2082e</b><extra></extra>"
            ),
        )
    )

    fig.update_layout(
        **_BASE_LAYOUT,
        title_text="Carbon Hotspots by Material",
        height=max(300, 60 + len(df) * 48),
        xaxis=dict(
            **_AXIS_STYLE,
            showline=True,
            title=dict(text="kgCO\u2082e", font=dict(color=TEXT_DIM, size=11)),
            tickformat=",.0f",
        ),
        yaxis=dict(
            **_AXIS_STYLE,
            showgrid=False,
            zeroline=False,
            showline=False,
            automargin=True,
        ),
        bargap=0.30,
        transition=dict(duration=700, easing='cubic-in-out'),
    )

    fig.add_annotation(
        text="Material-level emissions intensity",
        xref="paper", yref="paper",
        x=1, y=-0.09,
        showarrow=False,
        font=dict(family=FONT_SANS, color=TEXT_DIM, size=10),
        xanchor="right",
    )
    return fig


def carbon_breakdown_pie(data: dict) -> go.Figure:
    """Premium donut chart — carbon breakdown by lifecycle phase."""
    materials_co2 = sum(
        m["amount"] * m.get("emission_factor", 0) for m in data.get("materials", [])
    )
    energy_co2 = sum(
        e["usage"] * e.get("emission_factor", 0) for e in data.get("energy", [])
    )
    transport_co2 = sum(
        t["distance"] * t.get("emission_factor", 0) for t in data.get("transport", [])
    )

    labels = ["Materials", "Energy", "Transport"]
    values = [materials_co2, energy_co2, transport_co2]

    if all(v == 0 for v in values):
        return empty_chart("No carbon data available")

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.60,
            marker=dict(
                colors=["#919e65", "#c66b3d", "#7c3307"],
                line=dict(color=SURFACE, width=3),
            ),
            textinfo="percent",
            textfont=dict(family=FONT_SANS, color=TEXT_PRI, size=12),
            hovertemplate=(
                "<b>%{label}</b><br>"
                "%{value:,.2f} kgCO\u2082e<br>"
                "<b>%{percent}</b><extra></extra>"
            ),
            direction="clockwise",
            sort=True,
            pull=[0.04, 0.02, 0],
        )
    )

    total = sum(v for v in values if v > 0)
    fig.add_annotation(
        text=f"<b>{total:,.0f}</b><br>kgCO\u2082e",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(family=FONT_SERIF, color=TEXT_PRI, size=15),
        align="center",
    )

    fig.update_layout(
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(family=FONT_SANS, color=TEXT_SEC, size=12),
        title=dict(
            text="Carbon Breakdown by Category",
            font=dict(family=FONT_SERIF, color=TEXT_PRI, size=15),
            x=0.0, xanchor="left",
        ),
        height=340,
        margin=dict(t=44, b=16, l=16, r=16),
        hoverlabel=dict(
            bgcolor=SURFACE_HI,
            bordercolor=SURFACE_TOP,
            font=dict(family=FONT_SANS, color=TEXT_PRI, size=12),
        ),
        legend=dict(
            bgcolor="rgba(28,33,22,0.8)",
            bordercolor=SURFACE_TOP,
            borderwidth=1,
            font=dict(family=FONT_SANS, color=TEXT_SEC, size=12),
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
        ),
        transition=dict(duration=800, easing='cubic-in-out'),
    )
    return fig


def carbon_sankey_diagram(data: dict) -> go.Figure:
    """Full supply chain Sankey flow — Biophilic Enterprise style."""
    supplier  = data.get("project_info", {}).get("supplier", "Supplier")
    project   = data.get("project_info", {}).get("name", "Project")
    materials = data.get("materials", [])
    energies  = data.get("energy", [])
    transport = data.get("transport", [])

    if not (materials or energies or transport):
        return empty_chart("No supply chain data available")

    labels, colors = [supplier, project], [PRIMARY, "#8b9d83"]
    sources, targets, values, link_colors = [], [], [], []

    total_all = (
        sum(m["amount"]   * m.get("emission_factor", 0) for m in materials) +
        sum(e["usage"]    * e.get("emission_factor", 0) for e in energies)  +
        sum(t["distance"] * t.get("emission_factor", 0) for t in transport)
    )
    sources.append(0); targets.append(1)
    values.append(total_all or 1)
    link_colors.append("rgba(185,204,176,0.12)")

    offset = 2

    for i, mat in enumerate(materials):
        co2 = mat["amount"] * mat.get("emission_factor", 0)
        labels.append(mat["name"][:32])
        colors.append("#919e65")
        sources.append(1); targets.append(offset + i)
        values.append(co2 or 0.01)
        link_colors.append("rgba(145,158,101,0.22)")
    offset += len(materials)

    for i, en in enumerate(energies):
        co2 = en["usage"] * en.get("emission_factor", 0)
        labels.append(en["type"][:32])
        colors.append("#c66b3d")
        sources.append(1); targets.append(offset + i)
        values.append(co2 or 0.01)
        link_colors.append("rgba(198,107,61,0.22)")
    offset += len(energies)

    for i, tr in enumerate(transport):
        co2 = tr["distance"] * tr.get("emission_factor", 0)
        labels.append(tr["method"][:32])
        colors.append("#7c3307")
        sources.append(1); targets.append(offset + i)
        values.append(co2 or 0.01)
        link_colors.append("rgba(124,51,7,0.22)")

    fig = go.Figure(
        go.Sankey(
            arrangement="snap",
            node=dict(
                pad=20,
                thickness=20,
                line=dict(color=SURFACE, width=1.5),
                label=labels,
                color=colors,
                hovertemplate="<b>%{label}</b><br>%{value:,.2f} kgCO\u2082e<extra></extra>",
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=link_colors,
                hovertemplate=(
                    "%{source.label} \u2192 %{target.label}<br>"
                    "<b>%{value:,.2f} kgCO\u2082e</b><extra></extra>"
                ),
            ),
            textfont=dict(family=FONT_SANS, color=TEXT_SEC, size=11),
        )
    )

    fig.update_layout(
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(family=FONT_SANS, color=TEXT_SEC, size=12),
        title=dict(
            text="Supply Chain Carbon Flow",
            font=dict(family=FONT_SERIF, color=TEXT_PRI, size=15),
            x=0.0, xanchor="left",
        ),
        hoverlabel=dict(
            bgcolor=SURFACE_HI,
            bordercolor=SURFACE_TOP,
            font=dict(family=FONT_SANS, color=TEXT_PRI, size=12),
        ),
        height=460,
        margin=dict(t=44, b=16, l=16, r=16),
        transition=dict(duration=700, easing='cubic-in-out'),
    )
    return fig


def empty_chart(message: str) -> go.Figure:
    """Branded empty state."""
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
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        height=320,
        margin=dict(t=16, b=16, l=16, r=16),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig
