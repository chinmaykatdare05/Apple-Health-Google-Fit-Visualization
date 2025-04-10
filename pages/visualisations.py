import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
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
    Generates a line chart for the selected columns in the DataFrame using Plotly.
    """
    cols = st.multiselect(
        "Select columns to plot", df.columns, default=list(df.columns)[:1]
    )
    if cols:
        data = df.reset_index()
        x_col = data.columns[0]
        fig = px.line(
            data,
            x=x_col,
            y=cols,
            title="Line Plot of Health Data",
            labels={x_col: "Date", "value": "Value"},
        )
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
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
    fig.update_layout(width=800, height=800, title="Correlation Heatmap")
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)


def plot_bar_chart(df: pd.DataFrame) -> None:
    """
    Generates a bar chart for the selected columns.
    If the DataFrame index is of type datetime, aggregates the data by day.
    """
    cols = st.multiselect(
        "Select columns for Bar Chart", df.columns, default=list(df.columns)[:1]
    )
    if cols:
        # Aggregate data by day if the index is a datetime index
        if isinstance(df.index, pd.DatetimeIndex):
            data = df[cols].resample("D").mean().reset_index()
            x_col = data.columns[0]
        else:
            data = df[cols].reset_index()
            x_col = data.columns[0]
        fig = px.bar(
            data,
            x=x_col,
            y=cols,
            barmode="group",
            title="Bar Chart of Health Data",
        )
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
    else:
        st.info("Please select at least one column for the bar chart.")


def plot_scatter_chart(df: pd.DataFrame) -> None:
    """
    Generates a scatter plot based on user-selected X and Y axes.
    """
    if len(df.columns) < 2:
        st.warning("Not enough columns for a scatter plot.")
        return

    x_col = st.selectbox("Select X-axis", df.columns)
    y_options = [col for col in df.columns if col != x_col]
    y_col = st.selectbox("Select Y-axis", y_options)
    if x_col and y_col:
        # Reset index to use as a column for plotly if necessary
        data = df.reset_index()
        fig = px.scatter(
            data,
            x=x_col,
            y=y_col,
            title=f"Scatter Plot of {y_col} vs {x_col}",
            trendline="ols",
        )
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
    else:
        st.info("Please select columns for the scatter plot.")


def plot_histogram(df: pd.DataFrame) -> None:
    """
    Generates a histogram for a selected column.
    """
    col = st.selectbox("Select column for Histogram", df.columns)
    if col:
        fig = px.histogram(
            df,
            x=col,
            nbins=30,
            title=f"Histogram of {col}",
            labels={col: col},
        )
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
    else:
        st.info("Please select a column to display histogram.")


def plot_box_plot(df: pd.DataFrame) -> None:
    """
    Generates a box plot for a selected column.
    """
    col = st.selectbox("Select column for Box Plot", df.columns)
    if col:
        fig = px.box(
            df,
            y=col,
            title=f"Box Plot of {col}",
            labels={col: col},
        )
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
    else:
        st.info("Please select a column for the box plot.")


st.title("Health Data Visualisations")
if "data" not in st.session_state:
    st.write("Please upload a file to display visualizations.")
else:
    data = st.session_state["data"]
    # Sidebar for visualization type selection.
    vis_type = st.sidebar.selectbox(
        "Select Visualization Type",
        (
            "Line Chart",
            "Heatmap",
            "Bar Chart",
            "Scatter Plot",
            "Histogram",
            "Box Plot",
        ),
    )

    if vis_type == "Line Chart":
        plot_line_chart(data)
    elif vis_type == "Heatmap":
        plot_heatmap(data)
    elif vis_type == "Bar Chart":
        plot_bar_chart(data)
    elif vis_type == "Scatter Plot":
        plot_scatter_chart(data)
    elif vis_type == "Histogram":
        plot_histogram(data)
    elif vis_type == "Box Plot":
        plot_box_plot(data)
    else:
        st.write("Please select a visualization type from the sidebar.")
