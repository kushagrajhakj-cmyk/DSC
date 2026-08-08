import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.title("Exo-up DSC Stacked Plot Dashboard")

# === File Upload ===
uploaded_files = st.file_uploader(
    "Upload one or more Excel files",
    type=["xls", "xlsx"],
    accept_multiple_files=True
)

if uploaded_files:
    # Dictionary to store selected sheets per file
    selected_sheets = {}

    for file in uploaded_files:
        xls = pd.ExcelFile(file)
        sheets = xls.sheet_names
        selected_sheets[file.name] = st.multiselect(
            f"Select sheets from {file.name}:", sheets
        )

    # Temperature range
    min_temp, max_temp = st.slider("Temperature range (°C):", 0, 300, (0, 300))

    # Offset
    offset = st.number_input("Offset for stacking:", value=0.5, step=0.1)

    # Plot button
    if st.button("Generate Plot"):
        curves = []
        for file in uploaded_files:
            for sheet in selected_sheets[file.name]:
                df = pd.read_excel(file, sheet_name=sheet)

                # Clean dataset
                df = df[pd.to_numeric(df["Temperature"], errors="coerce").notnull()]
                df = df[pd.to_numeric(df["Heat Flow (Normalized)"], errors="coerce").notnull()]
                df["Temperature"] = pd.to_numeric(df["Temperature"], errors="coerce")
                df["Heat Flow (Normalized)"] = pd.to_numeric(df["Heat Flow (Normalized)"], errors="coerce")

                # Apply temperature range
                df = df[(df["Temperature"] >= min_temp) & (df["Temperature"] <= max_temp)]

                curves.append((df, f"{file.name} - {sheet}"))

        if curves:
            plt.figure(figsize=(8,6))
            for i, (df, label) in enumerate(curves):
                plt.plot(df["Temperature"], df["Heat Flow (Normalized)"] + i*offset, label=label)

            plt.xlabel("Temperature (°C)", fontsize=12, fontname="Times New Roman")
            plt.ylabel("Heat flow (a.u.)", fontsize=12, fontname="Times New Roman")
            plt.title("Exo-up DSC stacked plot", fontsize=14, fontname="Times New Roman")
            plt.legend(fontsize=9)
            plt.grid(True, linestyle="--", alpha=0.5)
            plt.tight_layout()
            st.pyplot(plt)
        else:
            st.warning("No data selected.")
