import os
import tempfile

import pandas as pd
import streamlit as st
import plotly.express as px

from core.agent import Agent


st.set_page_config(page_title="Personal Finance", layout="wide")
st.title("Home — Upload & Summary")

# ---------- sidebar controls ----------
st.sidebar.header("Upload / Ingest")


# ---------- init ----------
agent = Agent(data_dir="agent_data", filename="transactions.csv")

if "tx_df" not in st.session_state:
    st.session_state["tx_df"] = None


def _load_into_session() -> pd.DataFrame:
    df = agent.load_transactions()
    st.session_state["tx_df"] = df
    return df



def _compute_amount_metrics(amount: pd.Series) -> tuple[float, float, float]:
    """Compute gross spend, credits/refunds, and net using a consistent convention.

    Convention used throughout the app:
      - Amount > 0  => spend (charges)
      - Amount < 0  => credits/refunds/payments

    This avoids auto-inferring sign from the dataset, which breaks when you mix
    sources or have many payments/refunds.
    """
    s = amount.dropna()
    gross_spend = float(s[s > 0].sum())
    credits = float(s[s < 0].abs().sum())
    net = float(s.sum())
    return gross_spend, credits, net


firm = st.sidebar.selectbox("Statement type", ["DISCOVER", "AMEX"])
allowed = ["csv"] if firm == "DISCOVER" else ["xlsx"]

uploaded = st.sidebar.file_uploader(
    f"Upload {firm} statement ({', '.join(allowed)})",
    type=allowed,
)

col_a, col_b = st.sidebar.columns(2)
with col_a:
    ingest_clicked = st.button("Ingest", use_container_width=True)
with col_b:
    load_clicked = st.button("Load", use_container_width=True)

# ---------- Data_Loading ----------
if load_clicked:
    try:
        _load_into_session()
        st.sidebar.success("Loaded stored transactions.")
    except Exception as e:
        st.sidebar.error(f"Load failed: {e}")

if ingest_clicked:
    if uploaded is None:
        st.sidebar.error("Upload a file first.")
    else:
        suffix = ".csv" if firm == "DISCOVER" else ".xlsx"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.getbuffer())
            tmp_path = tmp.name

        try:
            stats = agent.add_data(tmp_path, firm)
            st.sidebar.success(
                f"Ingested. +{stats.get('inserted_estimate', 0)} rows "
                f"(skipped ~{stats.get('skipped_estimate', 0)})"
            )
            _load_into_session()
        except Exception as e:
            st.sidebar.error(f"Ingest failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass


# ---------- main display ----------
df = st.session_state.get("tx_df")

st.subheader("Data Summary")

if df is None or df.empty:
    st.info("No data loaded. Use the sidebar to load stored transactions or ingest a statement.")
else:

    # Required columns check
    missing = [c for c in ["Date", "Amount"] if c not in df.columns]
    if missing:
        st.error(f"Missing required columns for summary: {', '.join(missing)}")
        st.stop()

    # Transactions count
    n_tx = int(len(df))

    # Date range (inclusive)
    valid_dates = df["Date"].dropna()
    if valid_dates.empty:
        time_range_days = None
    else:
        min_date = valid_dates.min()
        max_date = valid_dates.max()
        time_range_days = int((max_date - min_date).days) + 1

    # Amount metrics (global)
    total_spend, total_credits, total_net = _compute_amount_metrics(df["Amount"])

    # Past 30 days
    cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=30)
    df_30d = df.loc[df["Date"] >= cutoff]
    spend_30d, credits_30d, net_30d = _compute_amount_metrics(df_30d["Amount"]) if not df_30d.empty else (0.0, 0.0, 0.0)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("# Transactions", f"{n_tx:,}")
    c2.metric("Time range (days)", "N/A" if time_range_days is None else f"{time_range_days:,}")
    c3.metric("Gross spend (all time)", f"{total_spend:,.2f}")
    c4.metric("Credits/refunds (all time)", f"{total_credits:,.2f}")
    c5.metric("Net total (all time)", f"{total_net:,.2f}")

    st.caption(f"Past 30 days — spend: {spend_30d:,.2f} | credits: {credits_30d:,.2f} | net: {net_30d:,.2f}")

    st.divider()
    st.subheader("Quick Visualization (Past 30 Days)")

    import plotly.express as px

    # Build a positive "Spend" series for plotting
    df_plot = df.dropna(subset=["Date"]).copy()
    if df_plot.empty:
        st.info("No valid dates to visualize.")
        st.stop()

    # Plot spend consistently as positive charges
    df_plot["Spend"] = df_plot["Amount"].clip(lower=0)

    cutoff_30d = pd.Timestamp.today().normalize() - pd.Timedelta(days=30)
    df_30d = df_plot.loc[df_plot["Date"] >= cutoff_30d]

    if df_30d.empty:
        st.info("No transactions in the past 30 days.")
        st.stop()

    v1, v2 = st.columns(2)

    # ---- Past 30 days spend by category (interactive bar) ----
    with v1:
        st.caption("Spend by category (past 30 days)")
        if "Category" not in df_30d.columns:
            st.info("No 'Category' column available.")
        else:
            cat_30d = (
                df_30d.groupby("Category", as_index=False)["Spend"]
                .sum()
                .sort_values("Spend", ascending=False)
            )

            fig_cat = px.bar(
                cat_30d,
                x="Category",
                y="Spend",
                title=None,
            )
            st.plotly_chart(fig_cat, use_container_width=True)

    # ---- Past 30 days daily spend (interactive line) ----
    with v2:
        st.caption("Daily spend (past 30 days)")
        daily = (
            df_30d.assign(day=df_30d["Date"].dt.date)
            .groupby("day", as_index=False)["Spend"]
            .sum()
            .sort_values("day")
        )

        fig_daily = px.line(
            daily,
            x="day",
            y="Spend",
            markers=True,
        )
        st.plotly_chart(fig_daily, use_container_width=True)

# Reset Transactions
st.sidebar.divider()
st.sidebar.subheader("Danger Zone")
with st.sidebar.expander("Reset transactions.csv", expanded=False):
    confirm_text = st.sidebar.text_input(
        "Type RESET to confirm",
        value="",
        placeholder="RESET",
        key="reset_confirm"
    )

    st.sidebar.warning(
        "This will permanently delete ALL transactions and recreate an empty transactions.csv. "
        "This action cannot be undone."
    )
    do_reset = st.sidebar.button(
        "Reset now",
        type="primary",
        disabled=(confirm_text.strip().upper() != "RESET"),
        key="reset_button"
    )

    if do_reset:
        agent.storage.reset_file()
        st.sidebar.success("transactions.csv has been reset.")
        st.rerun()