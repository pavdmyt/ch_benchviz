import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import sqlparse

DEFAULT_DATA = """clickhouse-systemlogs-eu-aiven-management-pavdmyt-test.avns.net:20001, queries: 30, QPS: 28.404, RPS: 17619645.884, MiB/s: 566.200, result RPS: 59733.005, result MiB/s: 14.272.

0.000%          0.013 sec.
10.000%         0.013 sec.
20.000%         0.013 sec.
30.000%         0.013 sec.
40.000%         0.013 sec.
50.000%         0.013 sec.
60.000%         0.013 sec.
70.000%         0.014 sec.
80.000%         0.015 sec.
90.000%         0.017 sec.
95.000%         0.020 sec.
99.000%         0.024 sec.
99.900%         0.024 sec.
99.990%         0.024 sec.
"""

DEFAULT_QUERY = """SELECT * FROM messages WHERE service_id = 40 LIMIT 50;"""

STATUS_REGEX = re.compile(
    r"([\w.-]+:\d+),\s*queries:\s*(\d+),\s*QPS:\s*([\d.]+),\s*RPS:\s*([\d.]+),\s*MiB/s:\s*([\d.]+),\s*result RPS:\s*([\d.]+),\s*result MiB/s:\s*([\d.]+)"
)

PERCENTILE_REGEX = re.compile(r"(\d+\.?\d*)%\s+(\d+\.\d+)\s+sec")

KEY_PERCENTILES = [50.0, 95.0, 99.0]


def format_sql(query: str) -> str:
    """Format the SQL query."""
    return sqlparse.format(query, reindent=True, keyword_case="upper")


def parse_status_string(text: str) -> dict:
    """Parse the benchmark status string into a dictionary."""
    status_match = STATUS_REGEX.search(text)
    if status_match:
        return {
            "endpoint": status_match.group(1),
            "queries": int(status_match.group(2)),
            "qps": float(status_match.group(3)),
            "rps": float(status_match.group(4)),
            "mib_s": float(status_match.group(5)),
            "result_rps": float(status_match.group(6)),
            "result_mib_s": float(status_match.group(7).rstrip(".")),
        }
    return None


def parse_benchmark_output(text: str) -> pd.DataFrame:
    """Parse the benchmark output text into a DataFrame."""
    lines = text.strip().split("\n")
    data = []

    for line in lines:
        match = PERCENTILE_REGEX.match(line)
        if match:
            percentile, latency = match.groups()
            data.append({"percentile": float(percentile), "latency": float(latency)})

    return pd.DataFrame(data)


def create_bar_chart(data: list, title: str, x_label: str, y_label: str) -> go.Figure:
    """Create a bar chart from the given data."""
    df = pd.DataFrame(data)
    fig = px.bar(
        df,
        x=x_label,
        y=["Query 1", "Query 2"],
        title=title,
        labels={"value": y_label, "variable": "Query"},
        barmode="group",
    )
    fig.update_layout(bargap=0.2, bargroupgap=0.1)
    return fig


def create_performance_metrics_charts(status_data1: dict, status_data2: dict) -> list:
    """Create multiple bar charts for performance metrics of two queries."""
    metrics = [
        ("QPS", "qps"),
        ("RPS (M/sec)", "rps", 1_000_000),
        ("MiB/s", "mib_s"),
        ("Result RPS (K/sec)", "result_rps", 1_000),
        ("Result MiB/s", "result_mib_s"),
    ]

    charts = []
    for metric in metrics:
        title, key = metric[0], metric[1]
        divisor = metric[2] if len(metric) > 2 else 1

        data = pd.DataFrame(
            {
                "Query": ["Query 1", "Query 2"],
                "Value": [status_data1[key] / divisor, status_data2[key] / divisor],
            }
        )
        fig = px.bar(
            data,
            x="Query",
            y="Value",
            title=title,
            labels={"Value": title},
            text="Value",
            color="Query",
            color_discrete_sequence=px.colors.qualitative.D3[:2],
            height=400,
        )
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig.update_layout(
            uniformtext_minsize=8,
            uniformtext_mode="hide",
            margin=dict(l=10, r=10, t=50, b=10),
            showlegend=False,
        )
        charts.append(fig)

    return charts


def create_latency_distribution_chart(df1: pd.DataFrame, df2: pd.DataFrame) -> go.Figure:
    """Create a line chart for query latency distribution of two queries."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df1["percentile"], y=df1["latency"], mode="lines+markers", name="Query 1"))
    fig.add_trace(go.Scatter(x=df2["percentile"], y=df2["latency"], mode="lines+markers", name="Query 2"))
    fig.update_layout(
        title="Query Latency by Percentile (Comparison)",
        xaxis_title="Percentile",
        yaxis_title="Latency (seconds)",
        hovermode="x unified",
    )
    return fig


def create_summary_bar_chart(df1: pd.DataFrame, df2: pd.DataFrame) -> go.Figure:
    """Create a bar chart for key percentiles of two queries."""
    data = []
    for percentile in KEY_PERCENTILES:
        data.append(
            {
                "percentile": f"P{int(percentile)}",
                "Query 1": df1[df1["percentile"] == percentile]["latency"].iloc[0],
                "Query 2": df2[df2["percentile"] == percentile]["latency"].iloc[0],
            }
        )

    return create_bar_chart(data, "Key Percentile Latencies Comparison", "percentile", "Latency (seconds)")


def main():
    st.set_page_config(page_title="ClickHouse Benchmark Comparison", layout="wide")
    st.title("ClickHouse Query Benchmark Results - Comparison")

    # Input section for benchmark data
    st.subheader("Input Benchmark Data")
    col1, col2 = st.columns(2)

    with col1:
        # Text area for Query 1
        query_text1 = st.text_area("Query 1:", value=DEFAULT_QUERY, height=150, key="query1")
        # Text area for Benchmark results of Query 1
        benchmark_text1 = st.text_area(
            "Benchmark results for Query 1:",
            value=DEFAULT_DATA,
            height=300,
            key="benchmark1",
        )

    with col2:
        # Text area for Query 2
        query_text2 = st.text_area("Query 2:", value=DEFAULT_QUERY, height=150, key="query2")
        # Text area for Benchmark results of Query 2
        benchmark_text2 = st.text_area(
            "Benchmark results for Query 2:",
            value=DEFAULT_DATA,
            height=300,
            key="benchmark2",
        )

    # Check if both benchmark texts are provided
    if benchmark_text1 and benchmark_text2:
        # Parse the benchmark status strings
        status_data1 = parse_status_string(benchmark_text1)
        status_data2 = parse_status_string(benchmark_text2)
        # Parse the benchmark output into DataFrames
        df1 = parse_benchmark_output(benchmark_text1)
        df2 = parse_benchmark_output(benchmark_text2)

        # Check if both status data are successfully parsed
        if status_data1 and status_data2:
            st.subheader("Benchmark Information")
            col3, col4 = st.columns(2)

            with col3:
                st.subheader("Query 1")
                # Display formatted SQL query for Query 1
                st.code(format_sql(query_text1), language="sql")
                # Display benchmark information for Query 1
                st.info(
                    f"📊 Running benchmarks against: **{status_data1['endpoint']}**\n\nNumber of queries executed: **{status_data1['queries']}**"
                )
                # Display metrics for Query 1
                st.metric("QPS", f"{status_data1['qps']:.2f}")
                st.metric("RPS", f"{status_data1['rps']:,.0f}")
                st.metric("MiB/s", f"{status_data1['mib_s']:.2f}")
                st.metric("Result RPS", f"{status_data1['result_rps']:,.0f}")
                st.metric("Result MiB/s", f"{status_data1['result_mib_s']:.2f}")

            with col4:
                st.subheader("Query 2")
                st.code(format_sql(query_text2), language="sql")
                st.info(
                    f"📊 Running benchmarks against: **{status_data2['endpoint']}**\n\nNumber of queries executed: **{status_data2['queries']}**"
                )
                st.metric("QPS", f"{status_data2['qps']:.2f}")
                st.metric("RPS", f"{status_data2['rps']:,.0f}")
                st.metric("MiB/s", f"{status_data2['mib_s']:.2f}")
                st.metric("Result RPS", f"{status_data2['result_rps']:,.0f}")
                st.metric("Result MiB/s", f"{status_data2['result_mib_s']:.2f}")

            # Performance metrics comparison chart
            st.subheader("Performance Metrics Comparison")
            metric_charts = create_performance_metrics_charts(status_data1, status_data2)
            cols = st.columns(len(metric_charts))
            # Display each chart in its own column
            for i, chart in enumerate(metric_charts):
                with cols[i]:
                    st.plotly_chart(chart, use_container_width=True)

            # Query Latency Distribution comparison chart
            st.plotly_chart(create_latency_distribution_chart(df1, df2), use_container_width=True)

            # Latency Statistics
            st.subheader("Latency Statistics")
            col5, col6 = st.columns(2)

            with col5:
                st.subheader("Query 1")
                st.metric(
                    "Median (P50) Latency",
                    f"{df1[df1['percentile'] == 50.0]['latency'].iloc[0]:.3f} sec",
                )
                st.metric(
                    "P95 Latency",
                    f"{df1[df1['percentile'] == 95.0]['latency'].iloc[0]:.3f} sec",
                )
                st.metric(
                    "P99 Latency",
                    f"{df1[df1['percentile'] == 99.0]['latency'].iloc[0]:.3f} sec",
                )

            with col6:
                st.subheader("Query 2")
                st.metric(
                    "Median (P50) Latency",
                    f"{df2[df2['percentile'] == 50.0]['latency'].iloc[0]:.3f} sec",
                )
                st.metric(
                    "P95 Latency",
                    f"{df2[df2['percentile'] == 95.0]['latency'].iloc[0]:.3f} sec",
                )
                st.metric(
                    "P99 Latency",
                    f"{df2[df2['percentile'] == 99.0]['latency'].iloc[0]:.3f} sec",
                )

            # Key Percentile Latencies comparison chart
            st.plotly_chart(create_summary_bar_chart(df1, df2), use_container_width=True)

            # Show the processed data
            st.subheader("Raw Data")
            col7, col8 = st.columns(2)
            with col7:
                st.subheader("Query 1")
                st.dataframe(df1)
            with col8:
                st.subheader("Query 2")
                st.dataframe(df2)


if __name__ == "__main__":
    main()
