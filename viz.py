import streamlit as st
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go


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


def main():
    st.set_page_config(page_title="ClickHouse Benchmark Visualization", layout="wide")

    st.title("ClickHouse Query Latency Analysis")

    # Input area for benchmark data
    st.subheader("Input Benchmark Data")
    default_data = """0.000%          0.013 sec.
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
99.990%         0.024 sec."""

    benchmark_text = st.text_area(
        "Paste your benchmark results here:", value=default_data, height=300
    )

    if benchmark_text:
        # Parse the data
        df = parse_benchmark_output(benchmark_text)

        # Create visualizations
        col1, col2 = st.columns(2)

        with col1:
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

            # Add custom hover template
            fig1.update_traces(
                hovertemplate="Percentile: %{x:.2f}<br>Latency: %{y:.3f} sec<extra></extra>"
            )

            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("Log-Scale View")
            # Create a log-scale version to better visualize tail latency
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

        # Display summary statistics
        st.subheader("Summary Statistics")
        col3, col4, col5 = st.columns(3)

        with col3:
            st.metric(
                "Median (P50) Latency",
                f"{df[df['percentile'] == 50.0]['latency'].iloc[0]:.3f} sec",
            )

        with col4:
            st.metric(
                "P95 Latency",
                f"{df[df['percentile'] == 95.0]['latency'].iloc[0]:.3f} sec",
            )

        with col5:
            st.metric(
                "P99 Latency",
                f"{df[df['percentile'] == 99.0]['latency'].iloc[0]:.3f} sec",
            )

        # Show the processed data
        st.subheader("Raw Data")
        st.dataframe(df)


if __name__ == "__main__":
    main()
