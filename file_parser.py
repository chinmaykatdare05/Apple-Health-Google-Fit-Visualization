import pandas as pd
import streamlit as st
import xml.etree.ElementTree as ET


@st.cache_data
def xml_parser(file):
    """
    Parses Apple Health XML file and returns a cleaned DataFrame.
    """

    try:
        records = []
        for _, elem in ET.iterparse(file, events=("end",)):
            if elem.tag == "Record":
                records.append(elem.attrib)
            elem.clear()

        df = pd.DataFrame(records)
        if df.empty:
            st.warning("⚠️ No valid health records found in XML file.")
            return pd.DataFrame()
    except ET.ParseError:
        st.error("❌ XML Parsing Error! Ensure the file is correctly formatted.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"🚨 Unexpected error while reading XML: {e}")
        return pd.DataFrame()

    try:
        # Drop unnecessary columns
        df.drop(
            columns=["sourceName", "sourceVersion", "device", "unit"],
            inplace=True,
            errors="ignore",
        )
        # Parse dates and adjust formats in one go
        df["Date"] = pd.to_datetime(df["creationDate"])
        df["startDate"] = pd.to_datetime(df["startDate"])
        df["endDate"] = pd.to_datetime(df["endDate"])

        # Set index once after all transformations
        df.set_index(df["Date"].dt.date, inplace=True)

        # Calculate 'Duration (s)' in a vectorized manner
        df["Duration (s)"] = (df["endDate"] - df["startDate"]).dt.total_seconds()

        # Drop unnecessary columns after transformations
        df.drop(columns=["creationDate", "startDate", "endDate", "Date"], inplace=True)

        # Clean the 'type' column in a vectorized way
        df["type"] = df["type"].str.replace(
            r"HK(?:QuantityTypeIdentifier|CategoryTypeIdentifier|DataType)",
            "",
            regex=True,
        )

        # Convert 'value' column to numeric with coercion, filling NaN with 0
        df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0)

        # Define columns for summing and calculating weighted averages
        sum_cols = [
            "ActiveEnergyBurned",
            "BasalEnergyBurned",
            "DistanceWalkingRunning",
            "FlightsClimbed",
            "StepCount",
        ]
        weighted_cols = [
            "HeadphoneAudioExposure",
            "WalkingAsymmetryPercentage",
            "WalkingDoubleSupportPercentage",
            "WalkingSpeed",
            "WalkingStepLength",
        ]

        sum_df = (
            df[df["type"].isin(sum_cols)]
            .pivot_table(index="Date", columns="type", values="value", aggfunc="sum")
            .fillna(0)
            .round(2)
        )
        weighted_df = df[df["type"].isin(weighted_cols)]
        weighted_avg_df = (
            weighted_df.assign(
                Weighted=weighted_df["value"] * weighted_df["Duration (s)"]
            )
            .pivot_table(index="Date", columns="type", values="Weighted", aggfunc="sum")
            .div(
                weighted_df.pivot_table(
                    index="Date", columns="type", values="Duration (s)", aggfunc="sum"
                )
            )
        )

        # Concatenate the sum and weighted average DataFrames
        df = pd.concat([sum_df, weighted_avg_df], axis=1).fillna(0).round(2)
        df.rename(
            columns={
                "ActiveEnergyBurned": "Active Energy Burned (cal)",
                "BasalEnergyBurned": "Basal Energy Burned (cal)",
                "DistanceWalkingRunning": "Distance Walking & Running (km)",
                "FlightsClimbed": "Flights Climbed",
                "StepCount": "Step Count",
                "HeadphoneAudioExposure": "Headphone Audio Exposure (dB)",
                "WalkingAsymmetryPercentage": "Walking Asymmetry Percentage (%)",
                "WalkingDoubleSupportPercentage": "Walking Double Support Percentage (%)",
                "WalkingSpeed": "Walking Speed (m/s)",
                "WalkingStepLength": "Walking Step Length (m)",
            },
            inplace=True,
        )

        return df
    except Exception as e:
        st.error(f"🚨 Error during XML processing: {e}")
        return pd.DataFrame()


@st.cache_data
def csv_parser(file):
    """
    Parses an Excel or CSV file and returns a DataFrame.
    """

    try:
        df = pd.read_csv(file)

        if df.empty:
            st.warning("⚠️ No valid records found in the file.")
            return None

        df.set_index(pd.to_datetime(df.pop("Date")), inplace=True)
        df.fillna(0, inplace=True)

        df.rename(columns=google_fit_units, inplace=True)

        df["Distance Covered (km)"] /= 1000
        df["Cycling duration (s)"] /= 1000
        df["Inactive duration (s)"] /= 1000
        df["Walking duration (s)"] /= 1000
        df["Running duration (s)"] /= 1000

        df["Calories Burned (kcal)"] = df["Calories Burned (kcal)"].round(2)
        df["Distance Covered (km)"] = df["Distance Covered (km)"].round(2)
        df["Average Speed (m/s)"] = df["Average Speed (m/s)"].round(2)
        df["Max Speed (m/s)"] = df["Max Speed (m/s)"].round(2)
        df["Min Speed (m/s)"] = df["Min Speed (m/s)"].round(2)

        if not df["Cycling duration (s)"].sum():
            df.drop("Cycling duration (s)", axis=1, inplace=True)

        return df

    except Exception as e:
        st.error(f"Error processing Excel/CSV file: {e}")
        return None


google_fit_units = {
    "Move Minutes count": "Move Minutes (mins)",
    "Calories (kcal)": "Calories Burned (kcal)",
    "Distance (m)": "Distance Covered (km)",
    "Heart Points": "Heart Points",
    "Heart Minutes": "Heart Minutes (minutes)",
    "Low latitude (deg)": "Low Latitude (deg)",
    "Low longitude (deg)": "Low Longitude (deg)",
    "High latitude (deg)": "High Latitude (deg)",
    "High longitude (deg)": "High Longitude (deg)",
    "Average speed (m/s)": "Average Speed (m/s)",
    "Max speed (m/s)": "Max Speed (m/s)",
    "Min speed (m/s)": "Min Speed (m/s)",
    "Step count": "Step Count",
    "Cycling duration (ms)": "Cycling duration (s)",
    "Inactive duration (ms)": "Inactive duration (s)",
    "Walking duration (ms)": "Walking duration (s)",
    "Running duration (ms)": "Running duration (s)",
}

apple_health_units = {
    "ActiveEnergyBurned": "Active Energy Burned (kcal)",
    "BasalEnergyBurned": "Basal Energy Burned (kcal)",
    "DistanceWalkingRunning": "Distance Covered (km)",
    "FlightsClimbed": "Flights Climbed",
    "HeadphoneAudioExposure": "Headphone Audio Exposure (dBASPL)",
    "StepCount": "Step Count",
    "WalkingAsymmetryPercentage": "Walking Asymmetry Percentage (%)",
    "WalkingDoubleSupportPercentage": "Walking Double Support Percentage (%)",
    "WalkingSpeed": "Walking Speed (km/hr)",
    "WalkingStepLength": "Walking Step Length (cm)",
}
