# Biểu đồ admin bằng plotly, màu phẳng theo bảng màu (không đen, không gradient). plotly chưa cài thì trả None.
from typing import Dict, Optional, Sequence

from ui import i18n_vi as T
from ui.render import EMOTION_COLORS

TEXT, BODY, MUTED, BORDER, PRIMARY = "#2F3E63", "#4A5878", "#7A88A6", "#DCE2F0", "#4361D8"


def _base_layout(go, height: int) -> dict:
    return dict(
        height=height,
        margin=dict(l=40, r=16, t=16, b=32),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Inter, sans-serif", size=12, color=BODY),
        showlegend=False,
    )


def daily_bar_figure(labels: Sequence[str], values: Sequence[int]) -> Optional[object]:
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None
    fig = go.Figure(go.Bar(x=list(labels), y=list(values), marker=dict(color=PRIMARY, line=dict(width=0)), text=[f"{v:,}" for v in values], textposition="outside", textfont=dict(color=TEXT, size=11)))
    fig.update_layout(**_base_layout(go, 260))
    fig.update_yaxes(gridcolor=BORDER, zeroline=False, linecolor=BORDER, tickfont=dict(color=MUTED))
    fig.update_xaxes(linecolor=BORDER, tickfont=dict(color=MUTED))
    return fig


def emotion_donut_figure(distribution: Dict[str, float]) -> Optional[object]:
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None
    keys = list(distribution)
    fig = go.Figure(
        go.Pie(
            labels=[T.EMOTION_VI[k] for k in keys],
            values=[distribution[k] for k in keys],
            hole=0.62,
            sort=False,
            marker=dict(colors=[EMOTION_COLORS[k] for k in keys], line=dict(color="#FFFFFF", width=2)),
            textinfo="percent",
            textfont=dict(color=TEXT, size=11),
        )
    )
    fig.update_layout(**_base_layout(go, 260), showlegend=True, legend=dict(font=dict(color=BODY, size=11)))
    fig.update_layout(margin=dict(l=8, r=8, t=8, b=8))
    return fig
