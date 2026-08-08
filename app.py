import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.title("Exo-up DSC Stacked Plot Dashboard (Plotly Style)")

# === File Upload ===
uploaded_files = st.file_uploader(
    "Upload one or more Excel files",
    type=["xls", "xlsx"],
    accept_multiple_files=True
)

if uploaded_files:
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
    st.subheader("Stacking Order, Labels, and Colors")
    curve_order = []
    for file in uploaded_files:
        for sheet in selected_sheets[file.name]:
            curve_order.append(f"{file.name} - {sheet}")

    ordered_curves = st.multiselect(
        "Select order of curves (top to bottom):",
        curve_order,
        default=curve_order
    )

    custom_labels = {}
    custom_colors = {}
    for label in ordered_curves:
        custom_labels[label] = st.text_input(f"Custom legend label for {label}:", label)
        custom_colors[label] = st.color_picker(f"Line color for {label}:", "#000000")

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
            fig = go.Figure()

            for i, label in enumerate(ordered_curves):
                df = curves[label]
                fig.add_trace(go.Scatter(
                    x=df["Temperature"],
                    y=df["Heat Flow (Normalized)"] + i*offset,
                    mode="lines",
                    name=custom_labels[label],
                    line=dict(width=line_weight, color=custom_colors[label])
                ))

            fig.update_layout(
                title=dict(text=plot_title, font=dict(size=title_size, family=font_family, color="black")),
                xaxis=dict(
                    title=dict(text=xlabel, font=dict(size=axis_label_size, family=font_family, color="black")),
                    tickfont=dict(size=tick_size, family=font_family, color="black"),
                    showgrid=grid_enabled,
                    linecolor="black",
                    mirror=True,
                    zeroline=False,
                    tickcolor="black"
                ),
                yaxis=dict(
                    title=dict(text=ylabel, font=dict(size=axis_label_size, family=font_family, color="black")),
                    tickfont=dict(size=tick_size, family=font_family, color="black"),
                    showgrid=grid_enabled,
                    showticklabels=False,
                    linecolor="black",
                    mirror=True,
                    zeroline=False,
                    tickcolor="black"
                ),
                legend=dict(
                    font=dict(size=axis_label_size-2, family=font_family, color="black"),
                    traceorder="normal"   # preserve order of traces
                ),
                plot_bgcolor="white",
                paper_bgcolor="white"
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data selected.")
