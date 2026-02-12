import streamlit as st
import pandas as pd
import numpy as np

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="IPL Player Performance Analysis",
    page_icon="🏏",
    layout="wide"
)

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown(
    """
    <h1 style='text-align:center;'>🏏 IPL Player Performance Analysis System</h1>
    <p style='text-align:center; font-size:18px;'>
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
# NORMALIZE COLUMN NAMES (MOST IMPORTANT)
# --------------------------------------------------
matches_df.columns = matches_df.columns.str.lower()
deliveries_df.columns = deliveries_df.columns.str.lower()

# batsman vs batter safety
if "batter" in deliveries_df.columns:
    deliveries_df.rename(columns={"batter": "batsman"}, inplace=True)

# match id safety
if "match_id" not in deliveries_df.columns and "id" in deliveries_df.columns:
    deliveries_df.rename(columns={"id": "match_id"}, inplace=True)

# --------------------------------------------------
# CREATE is_wicket COLUMN SAFELY (NO KEYERROR)
# --------------------------------------------------
if "is_wicket" not in deliveries_df.columns:
    if "dismissal_kind" in deliveries_df.columns:
        deliveries_df["is_wicket"] = deliveries_df["dismissal_kind"].notna().astype(int)
    else:
        deliveries_df["is_wicket"] = 0

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------
st.sidebar.header("🎯 Filters")

season_col = "season" if "season" in matches_df.columns else "year"
match_id_col = "id" if "id" in matches_df.columns else "match_id"

seasons = sorted(matches_df[season_col].dropna().unique())
selected_season = st.sidebar.selectbox("Select Season", seasons)

season_match_ids = matches_df[
    matches_df[season_col] == selected_season
][match_id_col]

season_data = deliveries_df[
    deliveries_df["match_id"].isin(season_match_ids)
]

players = sorted(season_data["batsman"].dropna().unique())
selected_player = st.sidebar.selectbox(
    "Select Player",
    ["All Players"] + players
)

# --------------------------------------------------
# BATTING STATS
# --------------------------------------------------
batting_df = season_data.groupby("batsman").agg(
    total_runs=("batsman_runs", "sum"),
    balls_faced=("ball", "count"),
    fours=("batsman_runs", lambda x: (x == 4).sum()),
    sixes=("batsman_runs", lambda x: (x == 6).sum())
).reset_index()

batting_df["strike_rate"] = (
    batting_df["total_runs"] / batting_df["balls_faced"]
) * 100

# --------------------------------------------------
# BOWLING STATS (SAFE)
# --------------------------------------------------
bowling_df = season_data[season_data["is_wicket"] == 1] \
    .groupby("bowler") \
    .size() \
    .reset_index(name="wickets")

# --------------------------------------------------
# MERGE PERFORMANCE
# --------------------------------------------------
player_perf = batting_df.merge(
    bowling_df,
    left_on="batsman",
    right_on="bowler",
    how="left"
)

player_perf["wickets"] = player_perf["wickets"].fillna(0)

# --------------------------------------------------
# REALISTIC EFFICIENCY SCORE
# --------------------------------------------------
player_perf["efficiency_score"] = (
    player_perf["total_runs"] * 0.45 +
    player_perf["strike_rate"] * 0.35 +
    player_perf["wickets"] * 0.20
)

# --------------------------------------------------
# PLAYER FILTER
# --------------------------------------------------
if selected_player != "All Players":
    player_perf = player_perf[player_perf["batsman"] == selected_player]

# --------------------------------------------------
# KPI METRICS
# --------------------------------------------------
st.subheader("📌 Key Performance Indicators")

c1, c2, c3, c4 = st.columns(4)

c1.metric("🏏 Avg Runs", int(player_perf["total_runs"].mean()))
c2.metric("⚡ Avg Strike Rate", round(player_perf["strike_rate"].mean(), 2))
c3.metric("🎯 Total Wickets", int(player_perf["wickets"].sum()))
c4.metric("🔥 Avg Efficiency", round(player_perf["efficiency_score"].mean(), 2))

st.divider()

# --------------------------------------------------
# TABS
# --------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Overview", "🏏 Batting", "🎯 Bowling", "⚡ Efficiency"]
)

# --------------------------------------------------
# TAB 1 – OVERVIEW
# --------------------------------------------------
with tab1:
    st.subheader("Top 10 Players by Efficiency")

    top10 = player_perf.sort_values(
        "efficiency_score", ascending=False
    ).head(10)

    st.dataframe(
        top10[[
            "batsman",
            "total_runs",
            "strike_rate",
            "wickets",
            "efficiency_score"
        ]],
        use_container_width=True
    )

    st.bar_chart(
        top10.set_index("batsman")["efficiency_score"]
    )

# --------------------------------------------------
# TAB 2 – BATTING
# --------------------------------------------------
with tab2:
    st.subheader("Batting Impact")

    st.scatter_chart(
        batting_df[["total_runs", "strike_rate"]]
    )

    st.markdown(
        "✔ High strike-rate + consistency = T20 success."
    )

# --------------------------------------------------
# TAB 3 – BOWLING
# --------------------------------------------------
with tab3:
    st.subheader("Top Wicket Takers")

    top_bowlers = bowling_df.sort_values(
        "wickets", ascending=False
    ).head(10)

    st.bar_chart(
        top_bowlers.set_index("bowler")["wickets"]
    )

    st.markdown(
        "✔ Wickets change the game momentum."
    )

# --------------------------------------------------
# TAB 4 – EFFICIENCY
# --------------------------------------------------
with tab4:
    st.subheader("Efficiency Distribution")

    st.line_chart(
        player_perf.sort_values("efficiency_score")
        .set_index("batsman")["efficiency_score"]
    )

    st.markdown("""
    **Efficiency Score Includes**
    - Batting impact  
    - Scoring speed  
    - Bowling contribution  
    """)

# --------------------------------------------------
# FINAL INSIGHTS
# --------------------------------------------------
st.divider()
st.subheader("🧠 Final Insights")

st.markdown("""
- Top scorers are not always the most efficient.
- All-rounders dominate modern T20 cricket.
- Strike rate matters as much as total runs.
- Data-driven evaluation improves team selection.
""")

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.caption(
    "🏏 IPL Player Performance Analysis | Streamlit | Pandas | Sports Analytics"
)

