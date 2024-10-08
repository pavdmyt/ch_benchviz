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

DEFAULT_QUERY = """SELECT
    toStartOfFiveMinute(timestamp) AS ts,
    countDistinct(user_id) AS users
FROM user_actions
WHERE timestamp >= now() - INTERVAL '1 hour'
GROUP BY ts
ORDER BY ts DESC
"""


def format_sql(query):
    """Format the SQL query."""
    return sqlparse.format(query, reindent=True, keyword_case="upper")


def parse_status_string(text):
    """Parse the benchmark status string into a dictionary."""
    # Find the status string using regex
    status_match = re.search(
        r"([\w.-]+:\d+),\s*queries:\s*(\d+),\s*QPS:\s*([\d.]+),\s*RPS:\s*([\d.]+),\s*MiB/s:\s*([\d.]+),\s*result RPS:\s*([\d.]+),\s*result MiB/s:\s*([\d.]+)",
        text,
    )

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


def parse_benchmark_output(text):
    """Parse the benchmark output text into a DataFrame."""
    lines = text.strip().split("\n")
    data = []

    for line in lines:
        # Match lines containing percentile data
        match = re.match(r"(\d+\.?\d*)%\s+(\d+\.\d+)\s+sec", line)
        if match:
            percentile, latency = match.groups()
            data.append({"percentile": float(percentile), "latency": float(latency)})

    return pd.DataFrame(data)


def create_summary_bar_chart(df):
    """Create a bar chart for key percentiles."""
    key_percentiles = [50.0, 95.0, 99.0]
    summary_data = df[df["percentile"].isin(key_percentiles)].copy()
    summary_data["percentile_label"] = summary_data["percentile"].apply(
        lambda x: f"P{int(x)}"
    )

    fig = px.bar(
        summary_data,
        x="percentile_label",
        y="latency",
        title="Key Percentile Latencies",
        labels={"percentile_label": "Percentile", "latency": "Latency (seconds)"},
    )

    fig.update_traces(
        marker_color="rgb(136, 132, 216)",
        hovertemplate="Percentile: %{x}<br>Latency: %{y:.3f} sec<extra></extra>",
    )

    fig.update_layout(bargap=0.4, showlegend=False)

    return fig


def create_performance_metrics_chart(status_data):
    """Create a bar chart for performance metrics."""
    # Prepare data for visualization
    metrics = [
        {"metric": "QPS", "value": status_data["qps"]},
        {"metric": "RPS (M/sec)", "value": status_data["rps"] / 1_000_000},
        {"metric": "MiB/s", "value": status_data["mib_s"]},
        {"metric": "Result RPS (K/sec)", "value": status_data["result_rps"] / 1_000},
        {"metric": "Result MiB/s", "value": status_data["result_mib_s"]},
    ]

    df = pd.DataFrame(metrics)

    fig = px.bar(
        df,
        x="metric",
        y="value",
        title="Performance Metrics",
        labels={"metric": "Metric", "value": "Value"},
    )

    fig.update_traces(
        marker_color="rgb(99, 110, 250)",
        hovertemplate="Metric: %{x}<br>Value: %{y:.3f}<extra></extra>",
    )

    fig.update_layout(bargap=0.4, showlegend=False)

    return fig


def main():
    st.set_page_config(page_title="ClickHouse Benchmark Visualization", layout="wide")

    st.title("ClickHouse Query Latency Analysis")

    # Input area for benchmark data
    st.subheader("Input Benchmark Data")

    # Add query input field
    query_text = st.text_area(
        "Query being benchmarked:",
        value=DEFAULT_QUERY,
        height=150,
        help="Enter the ClickHouse query that was used in the benchmark",
    )

    # Add some visual separation
    st.markdown("---")

    # Existing benchmark results input
    benchmark_text = st.text_area(
        "Benchmark results:",
        value=DEFAULT_DATA,
        height=300,
        help="Paste the complete benchmark output including the status line and percentile data",
    )

    if benchmark_text:
        # Parse the status string and percentile data
        status_data = parse_status_string(benchmark_text)
        df = parse_benchmark_output(benchmark_text)

        if status_data:
            # Display benchmark information
            st.subheader("Benchmark Information")
            st.info(
                f"📊 Running benchmarks against: **{status_data['endpoint']}**\n\n"
                f"Number of queries executed: **{status_data['queries']}**"
            )

            # Display formatted SQL query
            st.subheader("Benchmarked Query")
            formatted_sql = format_sql(query_text)
            st.code(formatted_sql, language="sql")

            # Display performance metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("QPS", f"{status_data['qps']:.2f}")
                st.metric("RPS", f"{status_data['rps']:,.0f}")

            with col2:
                st.metric("MiB/s", f"{status_data['mib_s']:.2f}")
                st.metric("Result RPS", f"{status_data['result_rps']:,.0f}")

            with col3:
                st.metric("Result MiB/s", f"{status_data['result_mib_s']:.2f}")

            # Add performance metrics chart
            st.plotly_chart(
                create_performance_metrics_chart(status_data), use_container_width=True
            )

        # Create visualizations for percentile data
        col4, col5 = st.columns(2)

        with col4:
            st.subheader("Query Latency Distribution")
            fig1 = px.line(
                df,
                x="percentile",
                y="latency",
                markers=True,
                title="Query Latency by Percentile",
            )

            fig1.update_layout(
                xaxis_title="Percentile",
                yaxis_title="Latency (seconds)",
                hovermode="x",
                showlegend=False,
            )

            fig1.update_traces(
                hovertemplate="Percentile: %{x:.2f}<br>Latency: %{y:.3f} sec<extra></extra>"
            )

            st.plotly_chart(fig1, use_container_width=True)

        with col5:
            st.subheader("Log-Scale View")
            fig2 = go.Figure()
            fig2.add_trace(
                go.Scatter(
                    x=df["percentile"],
                    y=df["latency"],
                    mode="lines+markers",
                    name="Latency",
                )
            )

            fig2.update_layout(
                title="Query Latency by Percentile (Log Scale)",
                xaxis_title="Percentile",
                yaxis_title="Latency (seconds)",
                yaxis_type="log",
                hovermode="x",
            )

            fig2.update_traces(
                hovertemplate="Percentile: %{x:.2f}<br>Latency: %{y:.3f} sec<extra></extra>"
            )

            st.plotly_chart(fig2, use_container_width=True)

        # Display latency statistics
        st.subheader("Latency Statistics")

        # Display metrics
        col6, col7, col8 = st.columns(3)

        with col6:
            st.metric(
                "Median (P50) Latency",
                f"{df[df['percentile'] == 50.0]['latency'].iloc[0]:.3f} sec",
            )

        with col7:
            st.metric(
                "P95 Latency",
                f"{df[df['percentile'] == 95.0]['latency'].iloc[0]:.3f} sec",
            )

        with col8:
            st.metric(
                "P99 Latency",
                f"{df[df['percentile'] == 99.0]['latency'].iloc[0]:.3f} sec",
            )

        # Add bar chart for latency statistics
        st.plotly_chart(create_summary_bar_chart(df), use_container_width=True)

        # Show the processed data
        st.subheader("Raw Data")
        st.dataframe(df)


if __name__ == "__main__":
    main()
