import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import streamlit as st
import io

st.title("Exo-up DSC Stacked Plot Dashboard (Matplotlib Style)")

# === Font Handling ===
available_fonts = fm.findSystemFonts(fontpaths=None, fontext='ttf')
times_new_roman_path = None
for f in available_fonts:
    if "Times New Roman" in f:
        times_new_roman_path = f
        break

def make_font(size):
    if times_new_roman_path:
        return fm.FontProperties(fname=times_new_roman_path, size=size)
    else:
        return fm.FontProperties(family="serif", size=size)

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

    axis_label_size = st.slider("Axis Label Font Size:", 8, 30, 25)
    tick_size = st.slider("Axis Tick Font Size:", 6, 25, 20)

    line_weight = st.slider("Line Width:", 1, 5, 2)
    grid_enabled = st.checkbox("Show Grid", True)

    min_temp, max_temp = st.slider("Temperature range (°C):", 0, 300, (0, 300))
    offset = st.number_input("Offset for stacking:", value=0.5, step=0.1)

    # === Legend and Annotation Controls ===
    st.subheader("Legend and Annotation Settings")
    legend_size = st.slider("Legend Font Size:", 8, 30, 15)
    label_gap = st.slider("Gap between line and label:", 0.0, 2.0, 0.3, step=0.1)
    label_x_offset = st.slider("Horizontal offset from y-axis:", 0.0, 2.0, 0.5, step=0.1)
    top_margin_factor = st.slider("Extra margin factor (× label_gap):", 0.0, 3.0, 1.5, step=0.1)

    # === Tick Spacing Control ===
    tick_step = st.selectbox("Tick spacing (°C):", [10, 20, 30, 40, 50, 100], index=1)

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
            fig, ax = plt.subplots(figsize=(8, 6))

            max_label_y = None  # track highest label position

            for i, label in enumerate(ordered_curves):
                df = curves[label]
                ax.plot(
                    df["Temperature"],
                    df["Heat Flow (Normalized)"] + i*offset,
                    linewidth=line_weight,
                    color=custom_colors[label]
                )
                # Place legend text inside plot near left side
                y_pos = df["Heat Flow (Normalized)"].iloc[0] + i*offset + label_gap
                x_pos = min_temp + label_x_offset
                ax.text(
                    x_pos,
                    y_pos,
                    custom_labels[label],
                    fontsize=legend_size,
                    fontproperties=make_font(legend_size),
                    color=custom_colors[label],
                    va="bottom", ha="left"
                )
                if max_label_y is None or y_pos > max_label_y:
                    max_label_y = y_pos

            # ❌ Remove plot title
            ax.set_title("")

            # X-axis label
            ax.set_xlabel(xlabel, fontproperties=make_font(axis_label_size))

            # Y-axis label only text "Heat Flow (mW) Exo up"
            ax.set_ylabel("Heat Flow (mW) Exo up", fontproperties=make_font(axis_label_size))

            # Remove y-axis tick values
            ax.set_yticks([])

            ax.tick_params(axis="x", labelsize=tick_size)
            ax.grid(grid_enabled)

            # ✅ Dynamic ticks with endpoints always visible
            tickvals = list(range(min_temp, max_temp+1, tick_step))
            if tickvals[-1] != max_temp:
                tickvals.append(max_temp)
            ax.set_xlim(min_temp, max_temp)
            ax.set_xticks(tickvals)

            # Extend y-limit if topmost label crosses, with extra margin
            if max_label_y is not None:
                ymin, ymax = ax.get_ylim()
                if max_label_y > ymax:
                    # Add margin proportional to label_gap
                    margin = label_gap * top_margin_factor
                    ax.set_ylim(ymin, max_label_y + margin)

            st.pyplot(fig)

            # ✅ Export PNG option
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
            st.download_button(
                label="Download Plot as PNG",
                data=buf.getvalue(),
                file_name="dsc_plot.png",
                mime="image/png"
            )
        else:
            st.warning("No data selected.")
