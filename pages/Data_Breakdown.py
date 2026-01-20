import streamlit as st
import pandas as pd
import altair as alt
from core.agent import Agent

st.set_page_config(page_title="Data Breakdown", layout="wide")

st.title("Data Breakdown")
st.caption("Select a date range (inclusive). Shows spend by category and spend per day.")

@st.cache_resource
def get_agent():
    return Agent()

agent = get_agent()

# --- Load transactions once ---
df_all = agent.load_transactions()

# --- Date range UI (inclusive) ---
col1, col2, col3 = st.columns([1, 1, 1])

min_date = df_all["Date"].min()
max_date = df_all["Date"].max()

with col1:
    start = st.date_input("Start date (inclusive)", value=min_date.date() if pd.notna(min_date) else None)

with col2:
    end = st.date_input("End date (inclusive)", value=max_date.date() if pd.notna(max_date) else None)

with col3:
    fill_missing_days = st.toggle("Fill missing days (0 spend)", value=True)

# Guard: if user selects reversed range, swap (simple UX)
if pd.to_datetime(start) > pd.to_datetime(end):
    start, end = end, start

# --- Call your flex spend function ---
by_category, by_day = agent.flex_spend_report(start, end, fill_missing_days=fill_missing_days)

# -----------------------------
# Section 1: Spend by Category
# -----------------------------
st.subheader("Spend by Category")

left, right = st.columns([1, 1])

with left:
    st.dataframe(by_category, use_container_width=True)

with right:
    if not by_category.empty:
        chart_cat = (
            alt.Chart(by_category)
            .mark_bar()
            .encode(
                x=alt.X("spend:Q", title="Spend"),
                y=alt.Y("Category:N", sort="-x", title="Category"),
                tooltip=["Category:N", alt.Tooltip("spend:Q", format=",.2f")]
            )
            .interactive()
        )
        st.altair_chart(chart_cat, use_container_width=True)
    else:
        st.info("No spend found in this date range.")

# -----------------------------
# Section 2: Spend per Day
# -----------------------------
st.subheader("Daily Spend")

left2, right2 = st.columns([1, 1])

with left2:
    st.dataframe(by_day, use_container_width=True)

with right2:
    if not by_day.empty:
        chart_day = (
            alt.Chart(by_day)
            .mark_line(point=True)
            .encode(
                x=alt.X("day:T", title="Day"),
                y=alt.Y("spend:Q", title="Spend"),
                tooltip=[alt.Tooltip("day:T", title="Day"), alt.Tooltip("spend:Q", format=",.2f")]
            )
            .interactive()
        )
        st.altair_chart(chart_day, use_container_width=True)
    else:
        st.info("No spend found in this date range.")