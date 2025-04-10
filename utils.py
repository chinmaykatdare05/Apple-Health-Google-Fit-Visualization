import pandas as pd
import streamlit as st
import calplot


def resample_data(df, freq="D") -> pd.DataFrame:
    """
    Resamples the data to daily frequency.
    """
    sum_cols = [
        "Active Energy Burned (kcal)",
        "Basal Energy Burned (kcal)",
        "Distance Walking & Running (m)",
        "Flights Climbed",
        "Step Count",
    ]
    max_cols = [
        "Headphone Audio Exposure (dB)",
        "Walking Asymmetry Percentage (%)",
        "Walking Double Support Percentage (%)",
    ]
    avg_cols = [
        "Walking Speed (m/s)",
        "Walking Step Length (m)",
    ]

    sum_df = df[sum_cols].resample(freq).sum()
    max_df = df[max_cols].resample(freq).max()
    avg_df = df[avg_cols].resample(freq).mean()
    return pd.concat([sum_df, max_df, avg_df], axis=1).fillna(0).round(2)


def safe_percentage_change(current, previous):
    """Safely calculate percentage change, avoiding division by zero."""
    if not previous:
        return "N/A"
    return f"{((current - previous) / previous) * 100:.2f} % (last 30 days)"


def display_metrics(data) -> None:
    """
    Display health data metrics based on the uploaded file.
    """
    # Check if "Heart Points" exists to distinguish between Apple Health & Google Fit
    is_google_fit = "Heart Points" in data.columns

    # Common metrics
    avg_steps = data["Step Count"].mean()
    avg_steps_30 = data["Step Count"].tail(30).mean()

    # Apple Health or Google Fit specific metrics
    if is_google_fit:
        avg_distance = data["Distance Covered (km)"].mean()
        avg_distance_30 = data["Distance Covered (km)"].tail(30).mean()
        avg_energy = data["Calories Burned (kcal)"].mean()
        avg_energy_30 = data["Calories Burned (kcal)"].tail(30).mean()
        avg_hp = data["Heart Points"].mean()
        avg_hp_30 = data["Heart Points"].tail(30).mean()
    else:
        avg_distance = data["Distance Walking & Running (km)"].mean()
        avg_distance_30 = data["Distance Walking & Running (km)"].tail(30).mean()
        avg_energy = (
            (data["Active Energy Burned (cal)"] + data["Basal Energy Burned (cal)"]) / 2
        ).mean()
        avg_energy_30 = (
            (
                data["Active Energy Burned (cal)"].tail(30)
                + data["Basal Energy Burned (cal)"].tail(30)
            )
            / 2
        ).mean()
        avg_hp, avg_hp_30 = None, None

    # Set up columns dynamically
    cols = st.columns(4 if avg_hp else 3)

    # Display metrics
    cols[0].metric(
        "Average Distance",
        f"{avg_distance:.2f} km",
        safe_percentage_change(avg_distance_30, avg_distance),
        border=True,
    )
    cols[1].metric(
        "Average Energy Burned",
        f"{avg_energy:.2f} cal",
        safe_percentage_change(avg_energy_30, avg_energy),
        border=True,
    )
    cols[2].metric(
        "Average Steps",
        f"{avg_steps:.0f}",
        safe_percentage_change(avg_steps_30, avg_steps),
        border=True,
    )
    if avg_hp is not None:
        cols[3].metric(
            "Average Heart Points",
            f"{avg_hp:.0f}",
            safe_percentage_change(avg_hp_30, avg_hp),
            border=True,
        )


def plot_calendar_heatmap(data: pd.DataFrame) -> None:
    """
    Generates a calendar heatmap for a selected column using calplot.
    """
    col = st.selectbox("Select column for Calendar Heatmap", data.columns)
    if col:
        if not isinstance(data.index, pd.DatetimeIndex):
            try:
                data.index = pd.to_datetime(data.index)
            except Exception as e:
                st.error(f"Failed to convert index to DatetimeIndex: {e}")
                return

        if isinstance(data.index, pd.DatetimeIndex):
            data = data[col]
            fig, _ = calplot.calplot(
                data,
                cmap="Blues",
                colorbar=True,
                suptitle=f"Calendar Heatmap of {col}",
                figsize=(8, 6),
            )
            st.pyplot(fig)
        else:
            st.warning(
                "The DataFrame index must be a DatetimeIndex for a calendar heatmap."
            )
    else:
        st.info("Please select a column for the calendar heatmap.")
