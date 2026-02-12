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
    Player Selection • Player Comparison • Overs Analysis • Best XI • Consistency
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
# NORMALIZE SCHEMA (NO ERROR GUARANTEE)
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
# SIDEBAR FILTERS (IMPORTANT)
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

# PLAYER SELECTION 🔥
selected_player = st.sidebar.selectbox(
    "Select Player (Single Analysis)",
    ["All Players"] + players
)

# PLAYER COMPARISON 🔥
st.sidebar.markdown("---")
st.sidebar.subheader("🆚 Player Comparison")

player1 = st.sidebar.selectbox("Player 1", players)
player2 = st.sidebar.selectbox("Player 2", players, index=1)

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
# CONSISTENCY INDEX
# ==================================================
runs_match = season_data.groupby(
    ["batsman", "match_id"]
)["batsman_runs"].sum().reset_index()

consistency = runs_match.groupby("batsman")["batsman_runs"].agg(
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
# EFFICIENCY SCORE
# ==================================================
player_perf["efficiency_score"] = (
    player_perf["total_runs"] * 0.40 +
    player_perf["strike_rate"] * 0.30 +
    player_perf["wickets"] * 0.20 +
    player_perf["consistency_index"] * 0.10
)

# ==================================================
# POWERPLAY vs DEATH OVERS
# ==================================================
pp = season_data[season_data["over"] <= 6]
death = season_data[season_data["over"] >= 16]

pp_runs = pp.groupby("batsman")["batsman_runs"].sum().reset_index(name="powerplay_runs")
death_runs = death.groupby("batsman")["batsman_runs"].sum().reset_index(name="death_runs")

overs_df = pp_runs.merge(death_runs, on="batsman", how="outer").fillna(0)

# ==================================================
# BEST XI
# ==================================================
best_batsmen = player_perf.sort_values(
    ["total_runs", "strike_rate"], ascending=False
).head(6)

best_bowlers = bowling_df.sort_values("wickets", ascending=False).head(5)

# ==================================================
# PLAYER FILTER (SINGLE PLAYER VIEW)
# ==================================================
display_df = player_perf.copy()
if selected_player != "All Players":
    display_df = display_df[display_df["batsman"] == selected_player]

# ==================================================
# KPIs
# ==================================================
st.subheader("📌 Key Performance Indicators")

c1, c2, c3, c4 = st.columns(4)
c1.metric("🏏 Total Runs", int(display_df["total_runs"].sum()))
c2.metric("⚡ Avg Strike Rate", round(display_df["strike_rate"].mean(), 2))
c3.metric("🎯 Total Wickets", int(display_df["wickets"].sum()))
c4.metric("🔥 Avg Efficiency", round(display_df["efficiency_score"].mean(), 2))

st.divider()

# ==================================================
# TABS
# ==================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📊 Overview",
        "🆚 Player vs Player",
        "⚡ Powerplay vs Death",
        "🏆 Best XI",
        "📈 Consistency"
    ]
)

# ==================================================
# TAB 1 – OVERVIEW
# ==================================================
with tab1:
    st.subheader("Top Players")

    st.dataframe(
        display_df.sort_values("efficiency_score", ascending=False).head(10),
        use_container_width=True
    )

# ==================================================
# TAB 2 – PLAYER vs PLAYER
# ==================================================
with tab2:
    st.subheader("🆚 Player Comparison")

    p1 = player_perf[player_perf["batsman"] == player1].iloc[0]
    p2 = player_perf[player_perf["batsman"] == player2].iloc[0]

    compare_df = pd.DataFrame({
        "Metric": ["Runs", "Strike Rate", "Wickets", "Consistency", "Efficiency"],
        player1: [
            p1["total_runs"], round(p1["strike_rate"], 2),
            int(p1["wickets"]), round(p1["consistency_index"], 2),
            round(p1["efficiency_score"], 2)
        ],
        player2: [
            p2["total_runs"], round(p2["strike_rate"], 2),
            int(p2["wickets"]), round(p2["consistency_index"], 2),
            round(p2["efficiency_score"], 2)
        ]
    })

    st.dataframe(compare_df, use_container_width=True)

# ==================================================
# TAB 3 – POWERPLAY vs DEATH
# ==================================================
with tab3:
    st.subheader("Powerplay vs Death Overs Impact")

    st.dataframe(
        overs_df.sort_values("powerplay_runs", ascending=False).head(10),
        use_container_width=True
    )

# ==================================================
# TAB 4 – BEST XI
# ==================================================
with tab4:
    st.subheader("🏆 Data-Driven Best XI")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🏏 Top 6 Batsmen")
        st.dataframe(best_batsmen[["batsman", "total_runs", "strike_rate"]])

    with col2:
        st.markdown("### 🎯 Top 5 Bowlers")
        st.dataframe(best_bowlers)

# ==================================================
# TAB 5 – CONSISTENCY
# ==================================================
with tab5:
    st.subheader("Player Consistency Index")

    st.dataframe(
        player_perf.sort_values("consistency_index", ascending=False)
        .head(10)[["batsman", "consistency_index"]],
        use_container_width=True
    )

# ==================================================
# FINAL INSIGHTS
# ==================================================
st.divider()
st.subheader("🧠 Final Insights")

st.markdown("""
- Player selection helps deep-dive individual performance.
- Player comparison supports data-driven team selection.
- Powerplay & death overs decide T20 outcomes.
- Consistency is more valuable than one-time big scores.
""")

# ==================================================
# FOOTER
# ==================================================
st.caption(
    "🏏 IPL Advanced Player Analytics | Streamlit | Big Data & Sports Analytics"
)
