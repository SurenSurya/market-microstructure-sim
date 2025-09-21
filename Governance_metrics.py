import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
df = pd.read_csv("data/governance_data.csv")

st.title("🌍 ESG Governance Scorecard Dashboard")

# Raw data viewer
with st.expander("View Raw Data"):
    st.dataframe(df)

# Bar chart
fig = px.bar(df, x="Company", y="Score_Percent", color="Score_Percent",
             text="Score_Percent", title="Governance Scores by Company")
st.plotly_chart(fig)

# Heatmap
metrics = df.columns[1:-2]
heatmap_data = df.set_index("Company")[metrics]
fig_heatmap = px.imshow(heatmap_data, title="Governance Metrics Heatmap")
st.plotly_chart(fig_heatmap)

# Radar chart
company = st.selectbox("Select a Company", df["Company"])
values = df[df["Company"] == company][metrics].iloc[0].values
radar = px.line_polar(r=values, theta=metrics, line_close=True,
                      title=f"Governance Profile: {company}")
st.plotly_chart(radar)

# Top performers
top_n = st.slider("Select Top N Companies", 1, 10, 5)
st.subheader("🏆 Top Performers")
st.dataframe(df.nlargest(top_n, "Score_Percent"))

st.subheader("⚠️ Laggards")
st.dataframe(df.nsmallest(top_n, "Score_Percent"))
