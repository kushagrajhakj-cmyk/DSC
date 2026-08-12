import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import io

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
    ylabel = st.text_input("Y-axis Label:", "Heat flow (mW) (Exo up)")

    font_family = st.selectbox("Font Family:", ["Times New Roman", "Arial", "Calibri", "Helvetica"], index=0)
    title_size = st.slider("Title Font Size:", 8, 30, 25)
    axis_label_size = st.slider("Axis Label Font Size:", 8, 30, 25)
    tick_size = st.slider("Axis Tick Font Size:", 6, 25, 20)

    line_weight = st.slider("Line Width:", 1, 5, 2)
    grid_enabled = st.checkbox("Show Grid", True)

    min_temp, max_temp = st.slider("Temperature range (°C):", 0, 300, (0, 300))
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

    default_labels = {0: "5 °C/min", 1: "10 °C/min", 2: "20 °C/min", 3: "30 °C/min"}
    default_colors = {0: "#F60505", 1: "#F2DA09", 2: "#0E19E8", 3: "#F00FEC"}

    custom_labels = {}
    custom_colors = {}
    for i, label in enumerate(ordered_curves):
        default_label = default_labels.get(i, label)
        default_color = default_colors.get(i, "#000000")
        custom_labels[label] = st.text_input(f"Custom legend label for {label}:", default_label)
        custom_colors[label] = st.color_picker(f"Line color for {label}:", default_color)

    # === Plot Button ===
    if st.button("Generate Plot"):
        curves = {}
        for file in uploaded_files:
            for sheet in selected_sheets[file.name]:
                df = pd.read_excel(file, sheet_name=sheet)
                df = df[pd.to_numeric(df["Temperature"], errors="coerce").notnull()]
                df = df[pd.to_numeric(df["Heat Flow (Normalized)"], errors="coerce").notnull()]
                df["Temperature"] = pd.to_numeric(df["Temperature"], errors="coerce")
                df["Heat Flow (Normalized)"] = pd.to_numeric(df["Heat Flow (Normalized)"], errors="coerce")
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
                    line=dict(width=line_weight, color=custom_colors[label]),
                    showlegend=False
                ))

                # Annotation above each line
                fig.add_annotation(
                    x=df["Temperature"].iloc[-1],
                    y=df["Heat Flow (Normalized)"].iloc[-1] + i*offset,
                    text=custom_labels[label],
                    font=dict(size=axis_label_size-2, family=font_family, color=custom_colors[label]),
                    showarrow=False,
                    align="left",
                    xanchor="left",
                    yanchor="bottom"
                )

            # Generate evenly spaced ticks including min & max
            tick_step = 50  # adjust spacing here
            tickvals = list(range(min_temp, max_temp + 1, tick_step))
            if tickvals[-1] != max_temp:
                tickvals.append(max_temp)

            fig.update_layout(
                title=dict(text=plot_title, font=dict(size=title_size, family=font_family, color="black")),
                xaxis=dict(
                    title=dict(text=xlabel, font=dict(size=axis_label_size, family=font_family, color="black")),
                    tickfont=dict(size=tick_size, family=font_family, color="black"),
                    showgrid=grid_enabled,
                    linecolor="black",
                    mirror=True,
                    zeroline=False,
                    tickcolor="black",
                    range=[min_temp, max_temp],
                    tickmode="array",
                    tickvals=tickvals,
                    ticktext=[str(t) for t in tickvals]
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
                plot_bgcolor="white",
                paper_bgcolor="white"
            )

            # Show chart (with Plotly’s built-in PNG export button in modebar)
            st.plotly_chart(fig, use_container_width=True)

            # ✅ Provide SVG and HTML download options
            try:
                svg_bytes = pio.to_image(fig, format="svg")
                st.download_button(
                    label="Download Plot as SVG",
                    data=svg_bytes,
                    file_name="dsc_plot.svg",
                    mime="image/svg+xml"
                )
            except Exception:
                st.warning("SVG export failed.")

            st.download_button(
                label="Download Plot as HTML",
                data=fig.to_html(full_html=False),
                file_name="dsc_plot.html",
                mime="text/html"
            )
        else:
            st.warning("No data selected.")
