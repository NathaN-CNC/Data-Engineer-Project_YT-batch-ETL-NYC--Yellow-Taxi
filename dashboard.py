from pathlib import Path
import pandas as pd
import streamlit as st


DAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

PARQUET_PATH = (
    Path(__file__).resolve().parent / "data" / "yellow_taxi_2016-03.parquet"
)


@st.cache_data(show_spinner="Loading data from Parquet...")
def load_data(path: Path) -> pd.DataFrame:
    
    df = pd.read_parquet(path)
    return df


def filter_data(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    hour_range = st.sidebar.slider("Time slot", 0, 23, (0, 23))

    vendor_options = sorted(df["VendorID"].unique().tolist())
    selected_vendors = st.sidebar.multiselect(
        "Suppliers",
        options=vendor_options,
        default=vendor_options,
    )

    payment_options = sorted(df["payment_label"].unique().tolist())
    selected_payments = st.sidebar.multiselect(
        "Payment type",
        options=payment_options,
        default=payment_options,
    )

    return df[
        df["hour_of_day"].between(hour_range[0], hour_range[1])
        & df["VendorID"].isin(selected_vendors)
        & df["payment_label"].isin(selected_payments)
    ]


def format_currency(value: float) -> str:
    value_str = f"{value:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    return f"US$ {value_str}"


def format_int(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def main() -> None:
    st.set_page_config(
        page_title="NYC Yellow Taxi - ETL Panel",
        page_icon="🚕",
        layout="wide",
    )

    st.title("🚕 Batch ETL Dashboard - NYC Yellow Taxi")
    st.markdown(
        """
        Data Engineering project with a batch ETL workflow:
        **Extraction -> Validation -> Processing -> Transformation -> Loading (Parquet) -> Analysis**.
        """
    )

    df = load_data(PARQUET_PATH)
    filtered_df = filter_data(df)

    if filtered_df.empty:
        st.warning("No data found for the selected filters.")
        st.stop()

    st.subheader("General Summary")
    col1, col2, col3, col4, col5 = st.columns(5)

    total_trips = len(filtered_df)
    total_revenue = float(filtered_df["total_amount"].sum())
    avg_fare = float(filtered_df["fare_amount"].mean())
    avg_distance = float(filtered_df["trip_distance"].mean())
    avg_tip_pct = float(filtered_df["tip_pct"].mean())

    col1.metric("Trips", format_int(total_trips))
    col2.metric("Total Revenue", format_currency(total_revenue))
    col3.metric("Average Fare", format_currency(avg_fare))
    col4.metric("Average Distance (mi)", f"{avg_distance:.2f}")
    col5.metric("Average Tip (%)", f"{avg_tip_pct:.2f}")

    tab_hour, tab_vendor, tab_payment, tab_weekday = st.tabs(
        ["By Hour", "By Supplier", "By Payment", "By Day of the Week"]
    )

    with tab_hour:
        hourly = (
            filtered_df.groupby("hour_of_day", as_index=True)
            .agg(
                total_trips=("hour_of_day", "size"),
                avg_distance=("trip_distance", "mean"),
                avg_fare=("fare_amount", "mean"),
                avg_duration=("trip_duration_min", "mean"),
                avg_speed=("trip_speed_mph", "mean"),
                avg_tip_pct=("tip_pct", "mean"),
            )
            .sort_index()
            .round(2)
            .rename(
                columns={
                    "total_trips": "Total Trips",
                    "avg_distance": "Average Distance (mi)",
                    "avg_fare": "Average Fare (US$)",
                    "avg_duration": "Average Duration (min)",
                    "avg_speed": "Average speed (mph)",
                    "avg_tip_pct": "Average Tip (%)",
                }
            )
        )

        chart_col1, chart_col2 = st.columns(2)
        chart_col1.line_chart(hourly["Total Trips"], use_container_width=True)
        chart_col2.bar_chart(hourly["Average Fare (US$)"], use_container_width=True)
        st.dataframe(hourly, use_container_width=True)

    with tab_vendor:
        vendor = (
            filtered_df.groupby("VendorID", as_index=True)
            .agg(
                total_trips=("VendorID", "size"),
                avg_distance=("trip_distance", "mean"),
                avg_fare=("fare_amount", "mean"),
                total_revenue=("total_amount", "sum"),
                avg_tip_pct=("tip_pct", "mean"),
                avg_speed=("trip_speed_mph", "mean"),
            )
            .round(2)
            .rename(
                columns={
                    "total_trips": "Total Trips",
                    "avg_distance": "Average Distance (mi)",
                    "avg_fare": "Average Fare (US$)",
                    "total_revenue": "Total Revenue (US$)",
                    "avg_tip_pct": "Average Tip (%)",
                    "avg_speed": "Average speed (mph)",
                }
            )
        )

        st.bar_chart(vendor["Total Trips"], use_container_width=True)
        st.dataframe(vendor, use_container_width=True)

    with tab_payment:
        payment = (
            filtered_df.groupby("payment_label", as_index=True)
            .agg(
                total_trips=("payment_label", "size"),
                avg_fare=("fare_amount", "mean"),
                avg_tip=("tip_amount", "mean"),
                avg_tip_pct=("tip_pct", "mean"),
                total_revenue=("total_amount", "sum"),
            )
            .round(2)
            .rename(
                columns={
                    "total_trips": "Total Trips",
                    "avg_fare": "Average Fare (US$)",
                    "avg_tip": "Average Tip (US$)",
                    "avg_tip_pct": "Average Tip (%)",
                    "total_revenue": "Total Revenue (US$)",
                }
            )
        )
        payment["% of Trips"] = (
            (payment["Total Trips"] / payment["Total Trips"].sum()) * 100
        ).round(2)

        st.bar_chart(payment["Total Trips"], use_container_width=True)
        st.dataframe(payment, use_container_width=True)

    with tab_weekday:
        weekday = (
            filtered_df.groupby("day_of_week", as_index=True)
            .agg(
                total_trips=("day_of_week", "size"),
                avg_distance=("trip_distance", "mean"),
                avg_fare=("fare_amount", "mean"),
                avg_duration=("trip_duration_min", "mean"),
                avg_tip_pct=("tip_pct", "mean"),
            )
            .round(2)
            .rename(
                columns={
                    "total_trips": "Total Trips",
                    "avg_distance": "Average Distance (mi)",
                    "avg_fare": "Average Fare (US$)",
                    "avg_duration": "Average Duration (min)",
                    "avg_tip_pct": "Average Tip (%)",
                }
            )
        )
        weekday = weekday.reindex(DAY_ORDER)

        st.bar_chart(weekday["Total Trips"], use_container_width=True)
        st.dataframe(weekday, use_container_width=True)


if __name__ == "__main__":
    main()