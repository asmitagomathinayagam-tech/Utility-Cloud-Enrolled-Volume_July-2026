"""
Customer Volume Dashboard (Streamlit)

Rebuilds the original Power BI dashboard with:
  - Live Providers Volume panel REMOVED
  - Account Status panel REMOVED
  - All figures filtered to live_or_test == "Live" only

Monthly Volume definition (confirmed with data owner):
    Volume = sum of the `subscribed` column across all rows where
    live_or_test == "Live" (i.e. total enrolled volume as of that
    report date).

Upload the monthly AccountRpt_*.xlsx export (Pivot_Customer_Volume tab)
to populate everything. Prior months (Jan'26-Jun'26) are baked in below
since they came from the original dashboard; Jul'26+ is computed live
from whatever file is uploaded.

New in this version: dark, indigo/violet themed layout (replacing the
original light teal Power BI look).
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Customer Volume Dashboard", layout="wide")

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

BG = "#0F1220"
CARD_BG = "#1A1F36"
BORDER = "#2E3555"
TEXT = "#E7E9F5"
SUBTEXT = "#9AA3C7"

# KPI cards — each metric gets its own subtle accent color
KPI_ACCENTS = ["#8B85C4", "#5FA8A0"]   # muted violet, muted teal

# Top 10 Customer Volume (pie) — subtle muted sunset palette
TOP10_SEQUENCE = ["#C97B8E", "#C99B76", "#C9A85B", "#D0C084", "#B87A8A",
                   "#B06C82", "#C48E77", "#CBA37E", "#D3BE8F", "#DFD2A3"]

# Customer Type (bar) — subtle muted ocean-blue palette
CTYPE_SEQUENCE = ["#6C90C4", "#6FB3C0", "#7599C9", "#7E92C2", "#5FA0AC"]

# Monthly Volume Trend — muted violet/teal pairing
ACCENT_1 = "#8B85C4"   # muted violet
ACCENT_2 = "#5FA8A0"   # muted teal

PLOTLY_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=TEXT, family="Segoe UI, sans-serif"),
        xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
        yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
        legend=dict(font=dict(color=TEXT)),
    )
)

st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {BG};
        }}
        section[data-testid="stSidebar"] {{
            background-color: {CARD_BG};
        }}
        h1, h2, h3, h4, h5, p, label, span, div {{
            color: {TEXT};
        }}
        .panel {{
            background-color: {CARD_BG};
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 18px 20px 8px 20px;
            margin-bottom: 18px;
        }}
        .panel-title {{
            color: {SUBTEXT};
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 10px;
        }}
        .kpi-value {{
            font-size: 2.4rem;
            font-weight: 700;
            color: {TEXT};
        }}
        .kpi-bar {{
            height: 4px;
            border-radius: 2px;
            margin-top: 12px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Prior months carried over from the existing dashboard, newest first (descending).
BASE_TREND = [
    ("Jun'26", 883075),
    ("May'26", 809347),
    ("Apr'26", 646921),
    ("Mar'26", 625548),
    ("Feb'26", 623391),
    ("Jan'26", 567225),
]


@st.cache_data(show_spinner=False)
def read_pivot_sheet(file) -> pd.DataFrame:
    return pd.read_excel(file, sheet_name="Pivot_Customer_Volume")


def filter_live(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["live_or_test"] == "Live"].copy()


def kpi_card(title: str, value: str, accent: str):
    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-bar" style="background:{accent};"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

st.sidebar.header("Load monthly report")
uploaded = st.sidebar.file_uploader("Upload AccountRpt_*.xlsx", type=["xlsx"])
report_label = st.sidebar.text_input("Label for this month's bar", value="Jul'26")

live_df = None
current_volume = None

if uploaded is not None:
    raw = read_pivot_sheet(uploaded)
    live_df = filter_live(raw)
    current_volume = int(live_df["subscribed"].sum())

st.title("Customer Volume Dashboard")

# ---------------------------------------------------------------------------
# KPIs (Live Providers Volume + Account Status intentionally omitted)
# ---------------------------------------------------------------------------

col1, col2 = st.columns(2)

with col1:
    val = f"{int(live_df['subscribed'].sum()):,}" if live_df is not None else "—"
    kpi_card("Live Customer Accounts", val, KPI_ACCENTS[0])

with col2:
    # unique/distinct customers only — nunique() dedupes organization_name
    val = f"{live_df['organization_name'].nunique():,}" if live_df is not None else "—"
    kpi_card("Live Customer Volume", val, KPI_ACCENTS[1])

# ---------------------------------------------------------------------------
# Top 10 Customer Volume (pie) + Customer Type (bar)
# ---------------------------------------------------------------------------

left, right = st.columns(2)

with left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Top 10 Customer Volume</div>', unsafe_allow_html=True)
    if live_df is not None:
        top10 = live_df.groupby("organization_name")["subscribed"].sum().sort_values(ascending=False)
        top = top10.head(10)
        others = top10.iloc[10:].sum()
        pie_df = pd.concat([top, pd.Series({"Others": others})]).reset_index()
        pie_df.columns = ["organization_name", "subscribed"]
        fig = px.pie(pie_df, names="organization_name", values="subscribed",
                     color_discrete_sequence=TOP10_SEQUENCE, hole=0.35)
        fig.update_traces(sort=False)  # keep "Others" last, not re-sorted by value
        fig.update_layout(template=PLOTLY_TEMPLATE, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Upload a report to populate this chart.")
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Customer Type</div>', unsafe_allow_html=True)
    if live_df is not None and "Direct/ Indirect" in live_df.columns:
        ctype = live_df.groupby("Direct/ Indirect")["subscribed"].sum().reset_index(name="Volume")
        ctype = ctype.sort_values("Volume", ascending=False)
        bar_colors = CTYPE_SEQUENCE[: len(ctype)]
        fig = go.Figure(go.Bar(x=ctype["Direct/ Indirect"], y=ctype["Volume"],
                                marker_color=bar_colors,
                                text=ctype["Volume"].map(lambda v: f"{v:,}"), textposition="outside"))
        fig.update_layout(template=PLOTLY_TEMPLATE, showlegend=False, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Upload a report to populate this chart.")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Monthly Volume Trend
# ---------------------------------------------------------------------------

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-title">Monthly Volume Trend</div>', unsafe_allow_html=True)

trend = list(BASE_TREND)
if current_volume is not None:
    trend.insert(0, (report_label, current_volume))  # newest month goes first (descending order)

labels = [t[0] for t in trend]
values = [t[1] for t in trend]
bar_colors = [ACCENT_2] + [ACCENT_1] * (len(values) - 1) if current_volume is not None else [ACCENT_1] * len(values)

fig = go.Figure(go.Bar(x=labels, y=values, marker_color=bar_colors,
                        text=[f"{v:,}" for v in values], textposition="outside"))
fig.update_layout(template=PLOTLY_TEMPLATE, yaxis_title=None, xaxis_title=None,
                   showlegend=False, margin=dict(t=10, b=10))
st.plotly_chart(fig, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)
