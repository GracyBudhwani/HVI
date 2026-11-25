"""Interactive companion website for State_Health_Vulnerability_Index.ipynb."""

import re

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="State Health Vulnerability Index", page_icon="🩺", layout="wide")

DATA_URL = "https://raw.githubusercontent.com/pratapvardhan/NFHS-5/master/NFHS-5-States.csv"
METRICS = {
    "High_Blood_Sugar": "blood sugar level - high or very high",
    "Hypertension": "elevated blood pressure",
    "Health_Insurance": "health insurance",
    "Clean_Fuel": "clean fuel for cooking",
    "Improved_Sanitation": "improved sanitation",
}
WEIGHTS = {
    "High_Blood_Sugar": 0.30,
    "Hypertension": 0.30,
    "Health_Insurance": -0.15,
    "Clean_Fuel": -0.15,
    "Improved_Sanitation": -0.10,
}


@st.cache_data(ttl=3600, show_spinner="Loading NFHS-5 state data…")
def load_analysis():
    data = pd.read_csv(DATA_URL)
    data = data[data["state"].astype(str).str.casefold() != "india"].copy()
    data["nfhs5_total"] = pd.to_numeric(data["nfhs5_total"], errors="coerce")

    def label_indicator(value):
        text = str(value).lower()
        for metric, phrase in METRICS.items():
            if phrase in text:
                return metric
        return None

    data["metric"] = data["indicator"].apply(label_indicator)
    pivot = (
        data.dropna(subset=["metric"])
        .groupby(["state", "metric"])["nfhs5_total"]
        .mean()
        .unstack()
        .dropna()
    )
    raw_score = sum(pivot[column] * weight for column, weight in WEIGHTS.items())
    spread = raw_score.max() - raw_score.min()
    pivot["Vulnerability_Index"] = 0.0 if spread == 0 else (raw_score - raw_score.min()) / spread * 100
    return pivot.sort_values("Vulnerability_Index", ascending=False), pivot[list(METRICS)].corr()


def normalize_name(value):
    return re.sub(r"[^a-z0-9]+", "", str(value).casefold())


st.title("State Health Vulnerability Index")
st.caption("Explore the NFHS-5 based state and union territory analysis, or type a state name to look it up.")

try:
    states, corr = load_analysis()
except Exception as exc:
    st.error("The NFHS-5 dataset could not be loaded. Check your internet connection and try again.")
    with st.expander("Technical details"):
        st.code(str(exc))
    st.stop()

if states.empty:
    st.error("No state rows were available after applying the notebook's indicator filters.")
    st.stop()

top_state = states.index[0]
low_state = states.index[-1]
avg_score = states["Vulnerability_Index"].mean()

tab_overview, tab_lookup, tab_data, tab_method = st.tabs(["Report", "State lookup", "All states", "Method"])

with tab_overview:
    st.subheader("At a glance")
    c1, c2, c3 = st.columns(3)
    c1.metric("States / UTs included", len(states))
    c2.metric("Highest index", top_state, f"{states.loc[top_state, 'Vulnerability_Index']:.1f} / 100")
    c3.metric("Lowest index", low_state, f"{states.loc[low_state, 'Vulnerability_Index']:.1f} / 100")
    st.markdown("#### Ten highest index scores")
    chart_data = states.head(10).reset_index(names="State / UT")
    fig = px.bar(chart_data.sort_values("Vulnerability_Index"), x="Vulnerability_Index", y="State / UT",
                 orientation="h", color="Vulnerability_Index", color_continuous_scale="Reds",
                 range_x=[0, 100], labels={"Vulnerability_Index": "Index (0–100)"})
    fig.update_layout(coloraxis_showscale=False, height=430, yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Indicator correlations")
    corr_display = corr.rename(columns={key: key.replace("_", " ") for key in corr.columns},
                               index={key: key.replace("_", " ") for key in corr.index})
    corr_fig = px.imshow(corr_display, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                         aspect="auto", labels=dict(color="Correlation"))
    st.plotly_chart(corr_fig, use_container_width=True)

with tab_lookup:
    st.subheader("Look up a state or union territory")
    query = st.text_input("Type a state name", placeholder="For example: Kerala")
    if query.strip():
        target = normalize_name(query)
        matches = [name for name in states.index if normalize_name(name) == target]
        if not matches:
            suggestions = [name for name in states.index if target in normalize_name(name)] if target else []
            if suggestions:
                st.info("I couldn't find an exact match. Did you mean: " + ", ".join(suggestions) + "?")
            else:
                st.warning("No matching state or union territory. Check the spelling or use the All states tab.")
        else:
            name = matches[0]
            row = states.loc[name]
            rank = states.index.get_loc(name) + 1
            score = float(row["Vulnerability_Index"])
            percentile = 100 * (len(states) - rank) / max(len(states) - 1, 1)
            st.markdown(f"### {name}")
            a, b, c = st.columns(3)
            a.metric("Vulnerability index", f"{score:.1f} / 100")
            b.metric("Relative rank", f"{rank} of {len(states)}", "Higher index ranks first")
            c.metric("Relative position", f"{percentile:.0f}th percentile")
            st.progress(min(max(score / 100, 0.0), 1.0), text="Index position within this dataset")
            st.info("This is a relative composite score: higher means more vulnerable under this notebook's chosen indicators and weights. It is not a clinical assessment or an official government rating.")
            st.markdown("#### Indicators used for this result")
            metrics = pd.DataFrame({"Indicator": list(METRICS), "NFHS-5 value": [row[key] for key in METRICS]})
            metrics["Indicator"] = metrics["Indicator"].str.replace("_", " ")
            st.dataframe(metrics, hide_index=True, use_container_width=True,
                         column_config={"NFHS-5 value": st.column_config.NumberColumn(format="%.2f")})

with tab_data:
    st.subheader("State and union territory scores")
    table = states.reset_index(names="State / UT")
    st.dataframe(table, hide_index=True, use_container_width=True,
                 column_config={"Vulnerability_Index": st.column_config.NumberColumn("Index (0–100)", format="%.2f")})
    st.download_button("Download results as CSV", table.to_csv(index=False).encode("utf-8"),
                       "state_health_vulnerability_index.csv", "text/csv")

with tab_method:
    st.subheader("How the notebook calculates the index")
    st.markdown("The app preserves the notebook's data source, indicator matching, averaging across rows for each state/indicator, weights, and min–max normalization.")
    st.latex(r"Raw = 0.30(BloodSugar) + 0.30(Hypertension) - 0.15(Insurance) - 0.15(CleanFuel) - 0.10(Sanitation)")
    st.latex(r"Index = 100 \times \frac{Raw - \min(Raw)}{\max(Raw) - \min(Raw)}")
    st.markdown("**Indicators:** high or very high blood sugar, elevated blood pressure, health insurance, clean fuel for cooking, and improved sanitation. Clinical risk values add to the raw score; the three protection values subtract from it.")
    st.markdown("**Interpretation:** 0 and 100 are the lowest and highest raw scores among the included states in this dataset. Scores are relative to this dataset and these chosen weights; they do not measure an individual's health risk, prove causation, or establish official vulnerability categories. Changing the included states can change the normalized scores.")
    st.markdown(f"**Source dataset:** [NFHS-5 state data CSV]({DATA_URL})")
    st.caption(f"Included {len(states)} state/UT rows. Mean index across the included rows: {avg_score:.1f}.")

st.divider()
st.caption("Companion website for State_Health_Vulnerability_Index.ipynb • Data refreshes hourly when the app is running.")
