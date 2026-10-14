# Biểu đồ cột của trang admin bằng plotly, màu phẳng kiểu ấn phẩm (mực trên giấy, không gradient). plotly chưa cài thì trả None.
from typing import Optional, Sequence

TEXT, BODY, MUTED, RULE, TINT = "#14130F", "#36342B", "#77736A", "#CFC9B8", "#CFC9B8"
MONO = "IBM Plex Mono, ui-monospace, monospace"


def _base_layout(height: int) -> dict:
    return dict(
        height=height,
        margin=dict(l=0, r=0, t=28, b=28),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=MONO, size=11, color=BODY),
        showlegend=False,
        bargap=0.5,
    )


def daily_bar_figure(labels: Sequence[str], values: Sequence[int]) -> Optional[object]:
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None
    peak = max(range(len(values)), key=lambda i: values[i]) if values else 0
    colors = [TEXT if i == peak else TINT for i in range(len(values))]  # mực đậm cho ngày cao nhất, các ngày còn lại nhạt
    fig = go.Figure(
        go.Bar(
            x=list(labels), y=list(values), marker=dict(color=colors, line=dict(width=0)),
            text=[f"{v:,}" for v in values], textposition="outside", textfont=dict(family=MONO, color=TEXT, size=11), cliponaxis=False,
            hovertemplate="%{x}: %{y:,} lượt<extra></extra>",
        )
    )
    fig.update_layout(**_base_layout(260))
    fig.update_yaxes(showgrid=False, zeroline=False, showline=False, showticklabels=False, range=[0, max(values) * 1.2])
    fig.update_xaxes(showline=True, linecolor=TEXT, linewidth=1, ticks="", tickfont=dict(family=MONO, color=MUTED, size=11))
    return fig
