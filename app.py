import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
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

    # === Customization Options ===
    st.subheader("Plot Customization")

    plot_title = st.text_input("Plot Title:", "Exo-up DSC stacked plot")
    xlabel = st.text_input("X-axis Label:", "Temperature (°C)")
    ylabel = st.text_input("Y-axis Label:", "Heat flow (a.u.)")

    font_family = st.selectbox("Font Family:", ["Times New Roman", "Arial", "Calibri", "Helvetica"])
    title_size = st.slider("Title Font Size:", 8, 30, 16)
    axis_label_size = st.slider("Axis Label Font Size:", 8, 25, 14)
    tick_size = st.slider("Axis Tick Font Size:", 6, 20, 12)

    line_weight = st.slider("Line Width:", 1, 5, 2)
    grid_enabled = st.checkbox("Show Grid", True)

    # Temperature range
    min_temp, max_temp = st.slider("Temperature range (°C):", 0, 300, (0, 300))

    # Offset
    offset = st.number_input("Offset for stacking:", value=0.5, step=0.1)

    # === Curve Order and Custom Labels ===
    st.subheader("Stacking Order and Labels")
    curve_order = []
    for file in uploaded_files:
        for sheet in selected_sheets[file.name]:
            curve_order.append(f"{file.name} - {sheet}")

    ordered_curves = st.multiselect(
        "Select order of curves (top to bottom):",
        curve_order,
        default=curve_order
    )

    # Editable labels
    custom_labels = {}
    for label in ordered_curves:
        custom_labels[label] = st.text_input(f"Custom legend label for {label}:", label)

    # === Plot Button ===
    if st.button("Generate Plot"):
        curves = {}
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

                curves[f"{file.name} - {sheet}"] = df

        if curves:
            # Apply global font settings
            mpl.rcParams['font.family'] = font_family

            plt.figure(figsize=(8,6))
            for i, label in enumerate(ordered_curves):
                df = curves[label]
                plt.plot(
                    df["Temperature"],
                    df["Heat Flow (Normalized)"] + i*offset,
                    label=custom_labels[label],
                    linewidth=line_weight
                )

            plt.xlabel(xlabel, fontsize=axis_label_size)
            plt.ylabel(ylabel, fontsize=axis_label_size)
            plt.title(plot_title, fontsize=title_size)
            plt.legend(fontsize=axis_label_size-2)

            # Hide y-axis numbers
            plt.yticks([])

            # Customize tick font sizes
            plt.xticks(fontsize=tick_size)

            if grid_enabled:
                plt.grid(True, linestyle="--", alpha=0.5)
            plt.tight_layout()
            st.pyplot(plt)
        else:
            st.warning("No data selected.")
