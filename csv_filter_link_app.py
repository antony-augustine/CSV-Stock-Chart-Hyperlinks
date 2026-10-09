import streamlit as st
import pandas as pd 
 
# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="CSV Stock Scanner",
    page_icon="📊",
    layout="wide"
)

st.title("📊 CSV Stock Scanner")

# ============================================================
# UPLOAD CSV
# ============================================================

uploaded_file = st.file_uploader(
    "Upload CSV file",
    type=["csv"]
)

if uploaded_file is None:
    st.info("Upload a CSV file to begin.")
    st.stop()

# ============================================================
# READ CSV
# ============================================================

try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Error reading CSV: {e}")
    st.stop()

# Remove completely empty columns
df = df.dropna(axis=1, how="all")

original_df = df.copy()

# ============================================================
# SESSION STATE
# ============================================================

if "search_text" not in st.session_state:
    st.session_state.search_text = ""

if "selected_columns" not in st.session_state:
    st.session_state.selected_columns = list(df.columns)

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙️ Controls")

# ============================================================
# GLOBAL SEARCH
# ============================================================

search_text = st.sidebar.text_input(
    "🔎 Search",
    value=st.session_state.search_text,
    placeholder="Ticker, sector, industry..."
)

st.session_state.search_text = search_text

# ============================================================
# COLUMN SHOW / HIDE
# ============================================================

st.sidebar.subheader("👁️ Columns")

all_columns = list(df.columns)

# Select all / clear all
col1, col2 = st.sidebar.columns(2)

if col1.button("Select All"):
    st.session_state.selected_columns = all_columns

if col2.button("Clear All"):
    st.session_state.selected_columns = []

selected_columns = st.sidebar.multiselect(
    "Visible columns",
    options=all_columns,
    default=st.session_state.selected_columns
)

st.session_state.selected_columns = selected_columns

# ============================================================
# RESET FILTERS
# ============================================================

if st.sidebar.button("🔄 Reset Filters"):

    st.session_state.search_text = ""
    st.session_state.selected_columns = all_columns

    # Rerun
    st.rerun()

# ============================================================
# FILTER DATA
# ============================================================

filtered_df = df.copy()

# ============================================================
# GLOBAL SEARCH
# ============================================================

if search_text.strip():

    search_value = search_text.strip().lower()

    mask = filtered_df.astype(str).apply(
        lambda col: col.str.lower().str.contains(
            search_value,
            na=False,
            regex=False
        )
    ).any(axis=1)

    filtered_df = filtered_df[mask]

# ============================================================
# MULTI-COLUMN FILTERS
# ============================================================

st.sidebar.subheader("🎯 Filters")

for column in df.columns:

    series = df[column]

    # --------------------------------------------------------
    # NUMERIC FILTER
    # --------------------------------------------------------

    if pd.api.types.is_numeric_dtype(series):

        min_value = series.min()
        max_value = series.max()

        if pd.notna(min_value) and pd.notna(max_value):

            if min_value != max_value:

                selected_range = st.sidebar.slider(
                    column,
                    min_value=float(min_value),
                    max_value=float(max_value),
                    value=(
                        float(min_value),
                        float(max_value)
                    )
                )

                filtered_df = filtered_df[
                    filtered_df[column].between(
                        selected_range[0],
                        selected_range[1]
                    )
                ]

    # --------------------------------------------------------
    # TEXT / CATEGORY FILTER
    # --------------------------------------------------------

    else:

        unique_values = (
            series
            .dropna()
            .astype(str)
            .unique()
        )

        # Only create multiselect for reasonable categories
        if len(unique_values) <= 100:

            selected_values = st.sidebar.multiselect(
                column,
                options=sorted(unique_values),
                key=f"filter_{column}"
            )

            if selected_values:

                filtered_df = filtered_df[
                    filtered_df[column]
                    .astype(str)
                    .isin(selected_values)
                ]

# ============================================================
# SUMMARY
# ============================================================

st.subheader("📌 Summary")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Total Rows",
    f"{len(original_df):,}"
)

c2.metric(
    "Filtered Rows",
    f"{len(filtered_df):,}"
)

c3.metric(
    "Columns",
    f"{len(original_df.columns):,}"
)

if len(original_df) > 0:

    percentage = (
        len(filtered_df) /
        len(original_df) *
        100
    )

else:
    percentage = 0

c4.metric(
    "Rows Remaining",
    f"{percentage:.1f}%"
)

# ============================================================
# DISPLAY DATA
# ============================================================

st.subheader("📋 Data")

# Only show selected columns
display_df = filtered_df[selected_columns]

# st.dataframe(
#     display_df,
#     width="stretch",
#     height=350,
#    hide_index=True
# )

# ============================================================

 
# Create TradingView hyperlinks

display_df["Chart"] = (
    "https://www.tradingview.com/chart/?symbol=NSE:"
    + display_df["Symbol"].astype(str)
)

display_df["Yahoo Finance"] = (
    "https://finance.yahoo.com/quote/"
    + display_df["Symbol"].astype(str)
    + ".NS/"
)

display_df["News"] = (
    "https://www.google.com/search?q="
    + display_df["Symbol"].astype(str)
    + "+stock+news"
)

st.dataframe(
    display_df,
    column_config={
        "Chart": st.column_config.LinkColumn(
            "TradingView",
            display_text="Open Chart"
        ),
        "Yahoo Finance": st.column_config.LinkColumn(
            "Yahoo Finance",
            display_text="Open Quote"
        ),
        "News": st.column_config.LinkColumn(
            "Latest News",
            display_text="View News"
        )
    },
    hide_index=True,
    width="stretch"
)

 # DOWNLOAD
# ============================================================

st.subheader("💾 Export")

csv_data = filtered_df[selected_columns].to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="⬇️ Download Filtered CSV",
    data=csv_data,
    file_name="filtered_data.csv",
    mime="text/csv"
)
 
