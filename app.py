import streamlit as st
from pathlib import Path
from file_parser import xml_parser, csv_parser
import pandas as pd
import utils

st.set_page_config(
    page_title="Vitalize - Home",
    layout="wide",
    page_icon="💪",
    initial_sidebar_state="auto",
)

st.logo("./logo.png", size="large", icon_image="./logo.png")


@st.dialog("User Consent for Vitalize")
def consent_dialog():
    """
    Displays a user consent dialog before proceeding with the app.
    It asks the user to provide consent to participate in the Vitalize project.
    """

    st.write("# Welcome to Vitalize!")
    st.write("Before proceeding, please review the following information:")
    st.write(
        "By participating in the Vitalize project, you agree to our terms and conditions and consent to the use of your data in accordance with our privacy policy. "
        "Your participation is entirely voluntary, and you can withdraw at any time."
    )
    st.divider()
    if st.checkbox("I consent to participate in the Vitalize project") and st.button(
        "Submit"
    ):
        st.session_state.consent = True
        st.rerun()


def process_uploaded_file(uploaded_file) -> pd.DataFrame | None:
    """
    Process the uploaded file based on its extension.
    Supported file types: XML, CSV.
    """

    parsers = {"xml": xml_parser, "csv": csv_parser}
    file_extension = Path(uploaded_file.name).suffix.lower()[1:]
    if file_extension not in parsers:
        st.error("❌ Unsupported file type! Please upload an XML or CSV file.")
        return None

    return parsers[file_extension](uploaded_file)


def file_upload() -> None:
    """Handles the file upload UI."""
    st.title("Vitalize")
    uploaded_file = st.file_uploader(
        "📂 Please upload Apple Health or Google Fit file (XML or CSV) to proceed.",
        type=["xml", "csv"],
        accept_multiple_files=False,
    )

    if uploaded_file:
        data = process_uploaded_file(uploaded_file)
        if data is not None and not data.empty:
            st.session_state.data = data
            st.divider()
            st.header("Health Metrics")
            utils.display_metrics(data)
        else:
            st.warning("⚠️ No valid data found in the file.")


def main() -> None:
    """Main function with navigation."""
    file_upload()


# Ensure user consent before proceeding
if st.session_state.get("consent", False):
    main()
else:
    consent_dialog()
    st.info(
        "Please provide your consent to proceed. Reload the page if you do not see the dialog."
    )
