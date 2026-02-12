import streamlit as st
import pandas as pd
import numpy as np

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="IPL Advanced Player Analytics",
    page_icon="🏏",
    layout="wide"
)

# ==================================================
# HEADER
# ==================================================
st.markdown(
    """
    <h1 style='text-align:center;'>🏏 IPL Advanced Player Analytics System</h1>
    <p style='text-align:center; font-size:18px;'>
    Player Efficiency • Comparison • Overs Analysis • Best XI • Consistency
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()

# ==================================================
# LOAD DATA
# ==================================================
@st.cache_data
def load_data():
    matches = pd.read_csv("matches.csv")
    deliveries = pd.read_csv("deliveries.csv")
    return matches, deliveries

matches_df, deliveries_df = load_data()

# ==================================================
# NORMALIZE SCHEMA (CRITICAL)
# ==================================================
matches_df.columns = matches_df.columns.str.lower()
deliveries_df.columns = deliveries_df.columns.str.lower()

if "batter" in deliveries_df.columns:
    deliveries_df.rename(columns={"batter": "batsman"}, inplace=True)

if "match_id" not in deliveries_df.columns and "id" in deliveries_df.columns:
    deliveries_df.rename(columns={"id": "match_id"}, inplace=True)

# Safe is_wicket creation
if "is_wicket" not in deliveries_df.columns:
    if "dismissal_kind" in deliveries_df.columns:
        deliveries_df["is_wicket"] = deliveries_df["dismissal_kind"].notna().astype(int)
    else:
        deliveries_df["is_wicket"] = 0

# ==================================================
# SIDEBAR FILTER
# ==================================================
st.sidebar.header("🎯 Filters")

season_col = "season"
match_id_col = "id"

seasons = sorted(matches_df[season_col].dropna().unique())
selected_season = st.sidebar.selectbox("Select Season", seasons)

season_match_ids = matches_df[
    matches_df[season_col] == selected_season
][match_id_col]

season_data = deliveries_df[
    deliveries_df["match_id"].isin(season_match_ids)
]

players = sorted(season_data["batsman"].dropna().unique())

# ==================================================
# CORE PLAYER STATS
# ==================================================
batting_df = season_data.groupby("batsman").agg(
    total_runs=("batsman_runs", "sum"),
    balls_faced=("ball", "count"),
    innings=("match_id", "nunique")
).reset_index()

batting_df["strike_rate"] = (
    batting_df["total_runs"] / batting_df["balls_faced"]
) * 100

bowling_df = season_data[season_data["is_wicket"] == 1] \
    .groupby("bowler") \
    .size() \
    .reset_index(name="wickets")

player_perf = batting_df.merge(
    bowling_df,
    left_on="batsman",
    right_on="bowler",
    how="left"
).fillna(0)

# ==================================================
# PLAYER CONSISTENCY INDEX ⭐
# Consistency = Avg Runs per Match / Std Dev
# ==================================================
runs_per_match = season_data.groupby(
    ["batsman", "match_id"]
)["batsman_runs"].sum().reset_index()

consistency = runs_per_match.groupby("batsman")["batsman_runs"].agg(
    avg_runs="mean",
    std_runs="std"
).reset_index()

consistency["consistency_index"] = (
    consistency["avg_runs"] / consistency["std_runs"]
).replace([np.inf, -np.inf], 0).fillna(0)

player_perf = player_perf.merge(
    consistency[["batsman", "consistency_index"]],
    on="batsman",
    how="left"
)

# ==================================================
# REALISTIC EFFICIENCY SCORE
# ==================================================
player_perf["efficiency_score"] = (
    player_perf["total_runs"] * 0.40 +
    player_perf["strike_rate"] * 0.30 +
    player_perf["wickets"] * 0.20 +
    player_perf["consistency_index"] * 0.10
)

# ==================================================
# POWERPLAY vs DEATH OVERS ⚡
# Powerplay: overs 1–6
# Death: overs 16–20
# ==================================================
powerplay = season_data[season_data["over"] <= 6]
death = season_data[season_data["over"] >= 16]

pp_runs = powerplay.groupby("batsman")["batsman_runs"].sum().reset_index(name="pp_runs")
death_runs = death.groupby("batsman")["batsman_runs"].sum().reset_index(name="death_runs")

overs_df = pp_runs.merge(death_runs, on="batsman", how="outer").fillna(0)

# ==================================================
# BEST XI RECOMMENDATION 🏆
# Top 6 Batsmen + Top 5 Bowlers
# ==================================================
top_batsmen = player_perf.sort_values(
    ["total_runs", "strike_rate"], ascending=False
).head(6)

top_bowlers = bowling_df.sort_values("wickets", ascending=False).head(5)

# ==================================================
# KPI METRICS
# ==================================================
st.subheader("📌 Season Summary")

c1, c2, c3, c4 = st.columns(4)
c1.metric("🏏 Total Runs", int(player_perf["total_runs"].sum()))
c2.metric("⚡ Avg Strike Rate", round(player_perf["strike_rate"].mean(), 2))
c3.metric("🎯 Total Wickets", int(player_perf["wickets"].sum()))
c4.metric("🔥 Avg Efficiency", round(player_perf["efficiency_score"].mean(), 2))

st.divider()

# ==================================================
# TABS
# ==================================================
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "⚡ Powerplay vs Death",
        "🏆 Best XI",
        "📈 Consistency Index",
        "📊 Overall Ranking"
    ]
)

# ==================================================
# TAB 1 – POWERPLAY vs DEATH
# ==================================================
with tab1:
    st.subheader("Powerplay vs Death Overs Impact")

    st.dataframe(
        overs_df.sort_values("pp_runs", ascending=False).head(10),
        use_container_width=True
    )

    st.markdown("✔ Powerplay aggression and death-over finishing define T20 matches.")

# ==================================================
# TAB 2 – BEST XI
# ==================================================
with tab2:
    st.subheader("🏆 Recommended Best XI (Data-driven)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🏏 Top 6 Batsmen")
        st.dataframe(
            top_batsmen[["batsman", "total_runs", "strike_rate"]],
            use_container_width=True
        )

    with col2:
        st.markdown("### 🎯 Top 5 Bowlers")
        st.dataframe(
            top_bowlers,
            use_container_width=True
        )

# ==================================================
# TAB 3 – CONSISTENCY
# ==================================================
with tab3:
    st.subheader("Player Consistency Index")

    st.dataframe(
        player_perf.sort_values(
            "consistency_index", ascending=False
        ).head(10)[["batsman", "consistency_index"]],
        use_container_width=True
    )

    st.markdown("✔ Higher consistency index = reliable performer across matches.")

# ==================================================
# TAB 4 – OVERALL RANKING
# ==================================================
with tab4:
    st.subheader("Top 10 Players Overall")

    top10 = player_perf.sort_values(
        "efficiency_score", ascending=False
    ).head(10)

    st.dataframe(
        top10[
            ["batsman", "total_runs", "strike_rate", "wickets",
             "consistency_index", "efficiency_score"]
        ],
        use_container_width=True
    )

    st.bar_chart(top10.set_index("batsman")["efficiency_score"])

# ==================================================
# FINAL INSIGHTS
# ==================================================
st.divider()
st.subheader("🧠 Final Cricket Insights")

st.markdown("""
- Powerplay specialists give early momentum.
- Death-over hitters decide match outcomes.
- Consistent players are more valuable than one-season wonders.
- Best XI selection should be data-driven, not reputation-based.
""")

# ==================================================
# FOOTER
# ==================================================
st.caption(
    "🏏 IPL Advanced Player Analytics | Streamlit | Sports Analytics | Big Data Project"
)
