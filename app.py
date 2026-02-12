import streamlit as st
import pandas as pd
import numpy as np

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="IPL Player Performance Analytics",
    page_icon="🏏",
    layout="wide"
)

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown(
    """
    <h1 style='text-align: center;'>🏏 IPL Player Performance Analysis System</h1>
    <p style='text-align: center; font-size:18px;'>
    Data-Driven Evaluation of Player Efficiency using Ball-by-Ball IPL Data
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
@st.cache_data
def load_data():
    matches = pd.read_csv("matches.csv")
    deliveries = pd.read_csv("deliveries.csv")
    return matches, deliveries

matches_df, deliveries_df = load_data()

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------
st.sidebar.header("🎯 Filters")

seasons = sorted(matches_df["season"].unique())
selected_season = st.sidebar.selectbox("Select Season", seasons)

match_ids = matches_df[matches_df["season"] == selected_season]["id"]
season_data = deliveries_df[deliveries_df["match_id"].isin(match_ids)]

players = sorted(season_data["batter"].unique())
selected_player = st.sidebar.selectbox("Select Player", ["All Players"] + players)

st.sidebar.markdown("---")
st.sidebar.markdown("📊 **Analysis Type**")
analysis_type = st.sidebar.radio(
    "", ["Overview", "Batting", "Bowling", "Efficiency"]
)

# --------------------------------------------------
# CORE CALCULATIONS
# --------------------------------------------------
batting = season_data.groupby("batter").agg(
    total_runs=("batsman_runs", "sum"),
    balls_faced=("ball", "count"),
    fours=("batsman_runs", lambda x: (x == 4).sum()),
    sixes=("batsman_runs", lambda x: (x == 6).sum())
).reset_index()

batting["strike_rate"] = (batting["total_runs"] / batting["balls_faced"]) * 100

bowling = season_data[season_data["is_wicket"] == 1] \
    .groupby("bowler") \
    .size() \
    .reset_index(name="wickets")

player_perf = batting.merge(
    bowling,
    left_on="batter",
    right_on="bowler",
    how="left"
).fillna(0)

# Realistic Efficiency Formula
player_perf["efficiency_score"] = (
    player_perf["total_runs"] * 0.45 +
    player_perf["strike_rate"] * 0.35 +
    player_perf["wickets"] * 0.20
)

# --------------------------------------------------
# FILTER PLAYER IF SELECTED
# --------------------------------------------------
if selected_player != "All Players":
    player_perf = player_perf[player_perf["batter"] == selected_player]

# --------------------------------------------------
# KPI METRICS
# --------------------------------------------------
st.subheader("📌 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

col1.metric("🏏 Avg Runs", round(player_perf["total_runs"].mean(), 2))
col2.metric("⚡ Avg Strike Rate", round(player_perf["strike_rate"].mean(), 2))
col3.metric("🎯 Total Wickets", int(player_perf["wickets"].sum()))
col4.metric("🔥 Avg Efficiency", round(player_perf["efficiency_score"].mean(), 2))

st.divider()

# --------------------------------------------------
# TABS
# --------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Overview", "🏏 Batting", "🎯 Bowling", "⚡ Efficiency"]
)

# --------------------------------------------------
# TAB 1: OVERVIEW
# --------------------------------------------------
with tab1:
    st.subheader("Top 10 Players (Overall Performance)")
    top10 = player_perf.sort_values(
        "efficiency_score", ascending=False
    ).head(10)

    st.dataframe(
        top10[[
            "batter",
            "total_runs",
            "strike_rate",
            "wickets",
            "efficiency_score"
        ]],
        use_container_width=True
    )

    st.bar_chart(
        top10.set_index("batter")["efficiency_score"]
    )

# --------------------------------------------------
# TAB 2: BATTING
# --------------------------------------------------
with tab2:
    st.subheader("Batting Analysis")

    st.scatter_chart(
        batting[["total_runs", "strike_rate"]]
    )

    st.markdown("""
    **Insight:**  
    Players with a balance of high strike rate and consistent runs
    are more valuable in T20 cricket.
    """)

# --------------------------------------------------
# TAB 3: BOWLING
# --------------------------------------------------
with tab3:
    st.subheader("Bowling Analysis")

    top_bowlers = bowling.sort_values(
        "wickets", ascending=False
    ).head(10)

    st.bar_chart(
        top_bowlers.set_index("bowler")["wickets"]
    )

    st.markdown("""
    **Insight:**  
    Wicket-taking bowlers significantly influence match outcomes,
    especially during powerplay and death overs.
    """)

# --------------------------------------------------
# TAB 4: EFFICIENCY
# --------------------------------------------------
with tab4:
    st.subheader("Player Efficiency Evaluation")

    st.line_chart(
        player_perf.sort_values("efficiency_score")
        .set_index("batter")["efficiency_score"]
    )

    st.markdown("""
    **Efficiency Score considers:**
    - Batting impact
    - Scoring speed
    - Bowling contribution  

    This provides a **holistic performance evaluation**.
    """)

# --------------------------------------------------
# FINAL INSIGHTS
# --------------------------------------------------
st.divider()
st.subheader("🧠 Final Insights")

st.markdown("""
- Not all high run-scorers are the most efficient players.
- All-rounders dominate efficiency rankings.
- Strike rate is as important as total runs in T20 cricket.
- Data-driven player evaluation improves team selection.
""")

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.caption(
    "🏏 IPL Player Performance Analysis | Built with Streamlit & Pandas | Big Data Analytics Project"
)
