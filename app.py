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

    plot_title = st.text_input("Plot Title:", "Exo-up DSC stacked plot")
    xlabel = st.text_input("X-axis Label:", "Temperature (°C)")

    title_size = st.slider("Title Font Size:", 8, 30, 25)
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

            for i, label in enumerate(ordered_curves):
                df = curves[label]
                ax.plot(
                    df["Temperature"],
                    df["Heat Flow (Normalized)"] + i*offset,
                    linewidth=line_weight,
                    color=custom_colors[label]
                )
                # Annotation above line with adjustable gap
                ax.text(
                    df["Temperature"].iloc[-1],
                    df["Heat Flow (Normalized)"].iloc[-1] + i*offset + label_gap,
                    custom_labels[label],
                    fontsize=legend_size,
                    fontproperties=make_font(legend_size),
                    color=custom_colors[label],
                    va="bottom", ha="left"
                )

            # Title with correct font size
            ax.set_title(plot_title, fontproperties=make_font(title_size))

            # X-axis label
            ax.set_xlabel(xlabel, fontproperties=make_font(axis_label_size))

            # Clear default y-axis label and ticks
            ax.set_ylabel("")
            ax.set_yticks([])

            # Draw upward arrow with "Endo" as y-axis label
            ax.annotate(
                "Endo",
                xy=(0, 0.5), xycoords=("axes fraction", "axes fraction"),
                xytext=(-0.08, 0.5), textcoords=("axes fraction", "axes fraction"),
                arrowprops=dict(arrowstyle="->", linewidth=2),
                ha="center", va="center", rotation=90,
                fontproperties=make_font(axis_label_size)
            )

            ax.tick_params(axis="x", labelsize=tick_size)
            ax.grid(grid_enabled)

            # ✅ Dynamic ticks with endpoints always visible
            tickvals = list(range(min_temp, max_temp+1, tick_step))
            if tickvals[-1] != max_temp:
                tickvals.append(max_temp)
            ax.set_xlim(min_temp, max_temp)
            ax.set_xticks(tickvals)

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
