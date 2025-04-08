import streamlit as st
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(
    page_title="Vitalize - Health Data Visualisation",
    layout="wide",
    page_icon="💪",
    initial_sidebar_state="auto",
)

st.logo(
    "./logo.png",
    size="large",
    icon_image="./logo.png",
)


def plot_line_chart(df: pd.DataFrame) -> None:
    """
    Generates a line chart for the selected columns in the DataFrame.
    """
    cols = st.multiselect(
        "Select columns to plot", df.columns, default=list(df.columns)[:1]
    )
    if cols:
        fig, ax = plt.subplots()
        df[cols].plot(ax=ax)
        ax.set_title("Line Plot of Health Data")
        ax.set_xlabel("Date")
        ax.set_ylabel("Value")
        st.pyplot(fig)
    else:
        st.info("Please select at least one column to plot.")


def plot_heatmap(df: pd.DataFrame) -> None:
    """
    Generates a heatmap of the correlation matrix for the DataFrame.
    """
    excluded_cols = [
        "Low Latitude (deg)",
        "Low Longitude (deg)",
        "High Latitude (deg)",
        "High Longitude (deg)",
    ]
    heatmap_df = df.copy()
    for col in excluded_cols:
        if col in heatmap_df.columns:
            heatmap_df.drop(col, axis=1, inplace=True)
    fig = go.Figure(
        data=go.Heatmap(z=heatmap_df.corr(), x=heatmap_df.columns, y=heatmap_df.columns)
    )
    fig.update_layout(width=800, height=800)
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)


st.title("Health Data Visualisations")
if "data" not in st.session_state:
    st.write("Please upload a file to display visualizations.")
else:
    df = st.session_state["data"]
    st.header("Correlation Heatmap")
    if st.button("Generate Heatmap"):
        plot_heatmap(df)
