import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
df = pd.read_csv("governance_data.csv")

st.title("🌍 ESG Governance Scorecard Dashboard")

# Show raw data
with st.expander("View Raw Data"):
    st.dataframe(df)

# Bar chart of governance scores
fig = px.bar(
    df, x="Company", y="Score_Percent", color="Score_Percent",
    text="Score_Percent", title="Governance Scores by Company"
)
st.plotly_chart(fig)

# Radar chart for detailed company profile
company = st.selectbox("Select a Company", df["Company"])
metrics = df.columns[1:-2]  # governance metrics only
values = df[df["Company"] == company][metrics].iloc[0].values

radar = px.line_polar(
    r=values, theta=metrics, line_close=True,
    title=f"Governance Profile: {company}"
)
st.plotly_chart(radar)
