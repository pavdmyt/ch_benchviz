# ClickHouse Benchmark Comparison Tool

## Description

This is a web-based tool for comparing ClickHouse query benchmark results. It allows you to input and visualize performance metrics for two different ClickHouse queries, providing insights into their relative efficiency and performance characteristics.

Key features:
- Input areas for two SQL queries and their respective benchmark results
- Parsing and visualization of benchmark data
- Performance metrics comparison charts (QPS, RPS, MiB/s, etc.)
- Query latency distribution chart
- Key percentile latencies comparison
- Raw data display

## Installation

To set up the project, follow these steps:

1. Clone the repository
2. Ensure you have Python 3.12+ installed.
3. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application:
1. Navigate to the project directory in your terminal.
2. Run the following command:

   ```
   streamlit run viz.py
   ```

3. The application will start, and you should see output similar to:

   ```
   You can now view your Streamlit app in your browser.
   Local URL: http://localhost:8501
   Network URL: http://192.168.1.5:8501
   ```

4. Open the provided URL in your web browser to access the tool.

5. In the web interface:
   - Enter your ClickHouse SQL queries in the "Query 1" and "Query 2" text areas.
   - Paste the corresponding benchmark results in the "Benchmark results" text areas.
   - The tool will automatically parse the input and generate visualizations and comparisons.
