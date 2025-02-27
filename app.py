import streamlit as st
import pandas as pd
import calplot
import plotly.express as px
import xml.etree.ElementTree as ET
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Health Data Visualization", layout="wide")


@st.cache_data
def parse_xml(file):
    """Parses Apple Health XML file and returns a cleaned DataFrame."""
    try:
        tree = ET.parse(file)
        root = tree.getroot()
        df = pd.DataFrame([record.attrib for record in root.iter("Record")])
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
            columns=["sourceName", "sourceVersion", "creationDate", "device"],
            inplace=True,
            errors="ignore",
        )
        # Shorten "type" values using regex
        df["type"] = df["type"].str.replace(
            r"HK(?:QuantityTypeIdentifier|CategoryTypeIdentifier|DataType)",
            "",
            regex=True,
        )
        # Remove unwanted types
        unwanted_types = {
            "HeadphoneAudioExposure",
            "SleepDurationGoal",
            "FlightsClimbed",
        }
        df = df[~df["type"].isin(unwanted_types)]

        # Convert date columns
        df["startDate"] = pd.to_datetime(df["startDate"].str[:-6], errors="coerce")
        if "endDate" in df.columns:
            df["endDate"] = pd.to_datetime(df["endDate"].str[:-6], errors="coerce")
            df.dropna(subset=["startDate", "endDate"], inplace=True)
            df["duration"] = (df["endDate"] - df["startDate"]).dt.total_seconds()
        else:
            df.dropna(subset=["startDate"], inplace=True)

        # Convert value to numeric and fill missing with 1.0
        df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(1.0)
        df.drop("unit", axis=1, inplace=True, errors="ignore")

        # Rename startDate to Date for consistency
        df.rename(columns={"startDate": "Date"}, inplace=True)

        # Reorder columns if duration exists
        if "duration" in df.columns:
            df = df[["type", "value", "Date", "duration"]]
        else:
            df = df[["type", "value", "Date"]]

        # Handle SleepAnalysis aggregation if available
        if "SleepAnalysis" in df["type"].values and "duration" in df.columns:
            sleep_df = (
                df[df["type"] == "SleepAnalysis"]
                .groupby(df["Date"].dt.date)["duration"]
                .sum()
            )
            sleep_df = sleep_df.rename("SleepAnalysis")

        # Pivot table to shape the data
        data = df.pivot_table(
            index=df["Date"].dt.date,
            columns="type",
            values="value",
            aggfunc="sum",
            fill_value=0,
        )
        data.index = pd.to_datetime(data.index)

        # Merge SleepAnalysis data if it was computed
        if "SleepAnalysis" in locals():
            data = data.join(sleep_df, how="left")

        return data
    except Exception as e:
        st.error(f"🚨 Error during XML processing: {e}")
        return pd.DataFrame()


@st.cache_data
def excel_parser(file):
    """Parses an Excel or CSV file and returns a DataFrame."""
    try:
        # Attempt to read as Excel first; if that fails, try CSV.
        try:
            df = pd.read_excel(file)
        except Exception:
            df = pd.read_csv(file)

        if "Date" not in df.columns:
            st.error("❌ 'Date' column not found in the uploaded file.")
            return None

        df["Date"] = pd.to_datetime(df["Date"], infer_datetime_format=True)
        df.set_index("Date", inplace=True)

        # Map and rename columns if available
        required_columns = {
            "Move Minutes count": "Move Minutes",
            "Calories (kcal)": "Calories",
            "Distance (m)": "Distance",
            "Walking duration (ms)": "Walking Duration",
            "Min speed (m/s)": "Min Speed",
            "Average speed (m/s)": "Average Speed",
            "Max speed (m/s)": "Max Speed",
            "Step count": "Steps",
            "Heart Points": "Heart Points",
        }
        available_columns = {
            k: v for k, v in required_columns.items() if k in df.columns
        }
        if available_columns:
            df = df[list(available_columns.keys())]
            df.rename(columns=available_columns, inplace=True)

        # Convert walking duration from milliseconds to seconds if applicable
        if "Walking Duration" in df.columns:
            df["Walking Duration"] = (
                pd.to_numeric(df["Walking Duration"], errors="coerce") / 1000
            )

        # Fill missing values in numeric columns
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col].fillna(0, inplace=True)

        return df
    except Exception as e:
        st.error(f"Error processing Excel/CSV file: {e}")
        return None


def visualize_data(data):
    """Handles UI for attribute selection, chart type, and plotting."""
    st.header("📊 Visualization")

    # Time Period Selection for time series resampling
    time_period = st.radio(
        "⏳ Select Time Period", ["Daily", "Weekly", "Monthly"], horizontal=True
    )
    # Attribute Selection
    attributes = st.multiselect("📌 Select Attributes", data.columns.tolist())
    # Chart Type Selection
    chart_type = st.selectbox(
        "📈 Select Chart Type",
        [
            "Bar Chart",
            "Line Chart",
            "Area Chart",
            "Scatter Chart",
            "Box Plot",
            "Histogram",
            "Correlation Heatmap",
            "Pairplot",
            "KDE Plot",
            "Regplot",
            "Calplot",
        ],
    )

    if st.button("🚀 Generate Chart"):
        if not attributes:
            st.warning("⚠️ Please select at least one attribute.")
            return

        # Resample data based on time period selection
        resampled_data = data.copy()
        if time_period == "Weekly":
            resampled_data = resampled_data.resample("W").sum()
        elif time_period == "Monthly":
            resampled_data = resampled_data.resample("ME").sum()

        plot_data = resampled_data[attributes]

        try:
            # Plotting using Plotly for interactive charts
            if chart_type in [
                "Bar Chart",
                "Line Chart",
                "Area Chart",
                "Scatter Chart",
                "Box Plot",
                "Histogram",
                "Correlation Heatmap",
            ]:
                if chart_type == "Bar Chart":
                    fig = px.bar(
                        plot_data, x=plot_data.index, y=attributes, title="📊 Bar Chart"
                    )
                elif chart_type == "Line Chart":
                    fig = px.line(
                        plot_data,
                        x=plot_data.index,
                        y=attributes,
                        title="📈 Line Chart",
                    )
                elif chart_type == "Area Chart":
                    fig = px.area(
                        plot_data,
                        x=plot_data.index,
                        y=attributes,
                        title="📉 Area Chart",
                    )
                elif chart_type == "Scatter Chart":
                    if len(attributes) < 2:
                        st.warning("⚠️ Scatter Chart requires two attributes.")
                        return
                    fig = px.scatter(
                        plot_data,
                        x=attributes[0],
                        y=attributes[1],
                        title="🔘 Scatter Chart",
                    )
                elif chart_type == "Box Plot":
                    fig = px.box(
                        plot_data, x=plot_data.index, y=attributes, title="📦 Box Plot"
                    )
                elif chart_type == "Histogram":
                    fig = px.histogram(
                        plot_data, x=attributes[0], title="📊 Histogram", nbins=30
                    )
                elif chart_type == "Correlation Heatmap":
                    if len(attributes) < 2:
                        st.warning(
                            "⚠️ Correlation Heatmap requires at least two attributes."
                        )
                        return
                    fig = px.imshow(
                        plot_data[attributes].corr(),
                        title="🔥 Correlation Heatmap",
                        color_continuous_scale="RdBu",
                    )
                st.plotly_chart(fig, use_container_width=True)

            # Plotting using Seaborn for static charts
            elif chart_type in ["Pairplot", "KDE Plot", "Regplot"]:
                plt.figure(figsize=(10, 6))
                if chart_type == "Pairplot":
                    pairplot_fig = sns.pairplot(plot_data)
                    st.pyplot(pairplot_fig)
                    return
                elif chart_type == "KDE Plot":
                    sns.kdeplot(plot_data[attributes[0]], fill=True)
                    st.pyplot(plt.gcf())
                    return
                elif chart_type == "Regplot":
                    if len(attributes) < 2:
                        st.warning("⚠️ Regplot requires two attributes.")
                        return
                    sns.regplot(x=plot_data[attributes[0]], y=plot_data[attributes[1]])
                    st.pyplot(plt.gcf())
                    return

            # Plotting using Calplot for calendar heatmaps
            elif chart_type == "Calplot":
                if len(attributes) != 1:
                    st.warning("⚠️ Calplot only supports one attribute at a time.")
                    return
                fig, ax = calplot.calplot(plot_data[attributes[0]], cmap="coolwarm")
                st.pyplot(fig)
                return

            else:
                st.error("❌ Unsupported chart type!")
        except Exception as e:
            st.error(f"🚨 Error while plotting: {e}")


def main():
    st.title("Apple Health/Google Fit Data Visualization")
    uploaded_file = st.file_uploader(
        "📂 Upload a file (XML, Excel, or CSV)", type=["xml", "xlsx", "xls", "csv"]
    )

    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        st.write(f"**Uploaded file:** {uploaded_file.name}")

        if file_extension == "xml":
            data = parse_xml(uploaded_file)
        elif file_extension in ["xlsx", "xls", "csv"]:
            data = excel_parser(uploaded_file)
        else:
            st.error(
                "❌ Unsupported file type! Please upload an XML, Excel, or CSV file."
            )
            return

        if data is not None and not data.empty:
            on = st.toggle("**Data Preview**")
            if on:
                st.write(data)
            visualize_data(data)
        else:
            st.warning("⚠️ No valid data found in the file.")
    else:
        st.info("📂 Please upload a file to proceed.")


if __name__ == "__main__":
    main()
