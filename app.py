import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_plotly_events import plotly_events
import io

st.title("Interactive DSC Plot Dashboard (Plotly Style)")

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

    xlabel = st.text_input("X-axis Label:", "Temperature (°C)")
    ylabel = "Heat flow (mW)"  # fixed, no ticks shown
    title_text = "↓ Endo"       # downward arrow with Endo

    line_weight = st.slider("Line Width:", 1, 5, 2)
    min_temp, max_temp = st.slider("Temperature range (°C):", 0, 300, (0, 300))
    tick_step = st.selectbox("Tick spacing (°C):", [25, 50, 100], index=1)

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
    default_colors = {0: "#FF0000", 1: "#FFA500", 2: "#0000FF", 3: "#FF00FF"}

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
                    y=df["Heat Flow (Normalized)"] + i*0.5,  # stacking offset
                    mode="lines",
                    name=custom_labels[label],
                    line=dict(width=line_weight, color=custom_colors[label])
                ))

            # Dynamic ticks with endpoints
            tickvals = list(range(min_temp, max_temp+1, tick_step))
            if tickvals[-1] != max_temp:
                tickvals.append(max_temp)

            fig.update_layout(
                title=dict(text=title_text, font=dict(size=20, family="Times New Roman", color="black")),
                xaxis=dict(
                    title=dict(text=xlabel, font=dict(size=18, family="Times New Roman", color="black")),
                    tickmode="array",
                    tickvals=tickvals,
                    ticktext=[str(t) for t in tickvals],
                    range=[min_temp, max_temp],
                    linecolor="black",
                    mirror=True,
                    zeroline=False
                ),
                yaxis=dict(
                    title=dict(text=ylabel, font=dict(size=18, family="Times New Roman", color="black")),
                    showticklabels=False,  # ✅ no y-axis ticks
                    linecolor="black",
                    mirror=True,
                    zeroline=False
                ),
                plot_bgcolor="white",
                paper_bgcolor="white"
            )

            # Show chart and capture clicks
            selected_points = plotly_events(fig, click_event=True, hover_event=False)

            if selected_points:
                x_val = selected_points[0]["x"]
                y_val = selected_points[0]["y"]

                # Add annotation at clicked point
                fig.add_annotation(
                    x=x_val,
                    y=y_val,
                    text="Custom Label",
                    font=dict(size=16, family="Times New Roman", color="black"),
                    showarrow=True,
                    arrowhead=2
                )

            st.plotly_chart(fig, use_container_width=True)

            # ✅ Export PNG option
            buf = io.BytesIO()
            fig.write_image(buf, format="png")
            st.download_button(
                label="Download Plot as PNG",
                data=buf.getvalue(),
                file_name="dsc_plot.png",
                mime="image/png"
            )
        else:
            st.warning("No data selected.")
