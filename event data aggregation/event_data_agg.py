
#!/usr/bin/env python3
"""
Event Data Aggregation Lab - Transform Data: SQL & Pandas Mastery
Course: Product Analytics Unlocked: From Metrics to Meaningful Insights

This lab focuses on applying data aggregation techniques to summarize event data
and identifying syntactic differences between SQL dialects for enterprise analytics.
"""

import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# PROVIDED CODE - DO NOT MODIFY
def create_sample_dataset():
    """Creates a sample user event dataset similar to Netflix viewer analytics data"""
    np.random.seed(42)  # For reproducible results

    # Generate sample user events
    n_events = 50000
    user_ids = np.random.randint(1000, 5000, n_events)
    device_types = np.random.choice(
        ['mobile', 'desktop', 'tablet', 'smart_tv'], n_events, p=[0.4, 0.3, 0.2, 0.1]
    )

    # Generate timestamps over the last 7 days
    base_time = datetime.now() - timedelta(days=7)
    time_offsets = np.random.randint(0, 7 * 24 * 60 * 60, n_events)  # seconds in 7 days
    timestamps = [base_time + timedelta(seconds=int(offset)) for offset in time_offsets]

    # Generate session data
    session_durations = np.random.exponential(15, n_events)  # minutes, exponential distribution
    action_types = np.random.choice(['view', 'click', 'search', 'purchase'], n_events, p=[0.5, 0.3, 0.15, 0.05])

    # Create DataFrame
    events_df = pd.DataFrame({
        'user_id': user_ids,
        'timestamp': timestamps,
        'device_type': device_types,
        'action_type': action_types,
        'session_duration_minutes': session_durations
    })

    # Sort by timestamp for realistic event ordering
    events_df = events_df.sort_values('timestamp').reset_index(drop=True)

    return events_df


def setup_sql_database(df):
    """Sets up SQLite database with sample data for SQL dialect comparison"""
    conn = sqlite3.connect(':memory:')
    df.to_sql('user_events', conn, index=False, if_exists='replace')
    return conn


# Initialize the dataset and database connection
print("Setting up sample dataset and database...")
events_data = create_sample_dataset()
sql_connection = setup_sql_database(events_data)

print(f"Dataset created with {len(events_data)} events")
print("Sample data:")
print(events_data.head())
print("\nDataset info:")
print(events_data.info())
print("\nDevice type distribution:")
print(events_data['device_type'].value_counts())


# SQL DIALECT COMPARISON SECTION
print("\n" + "="*60)
print("SQL DIALECT COMPARISON")
print("="*60)

# PROVIDED CODE - DO NOT MODIFY
# ANSI-SQL window function example
ansi_sql_query = """
SELECT user_id, device_type, session_duration_minutes,
       ROW_NUMBER() OVER (
           PARTITION BY device_type
           ORDER BY session_duration_minutes DESC
       ) AS session_rank
FROM user_events
WHERE action_type = 'view'
LIMIT 10;
"""

# Spark-SQL equivalent (syntax differences highlighted)
spark_sql_query = """
SELECT user_id, device_type, session_duration_minutes,
       ROW_NUMBER() OVER (
           PARTITION BY device_type
           ORDER BY session_duration_minutes DESC ROWS UNBOUNDED PRECEDING
       ) AS session_rank
FROM user_events
WHERE action_type = 'view'
LIMIT 10;
"""

print("ANSI-SQL Query:")
print(ansi_sql_query)
print("\nSpark-SQL Query:")
print(spark_sql_query)

# Test both queries
print("ANSI-SQL Results:")
ansi_results = pd.read_sql_query(ansi_sql_query, sql_connection)
print(ansi_results)

print("\nNote: SQLite uses ANSI-SQL syntax. Spark-SQL differences would be visible in actual Spark environment.")


# PRACTICE CHALLENGE 1
# TASK: Write equivalent window function queries in both ANSI-SQL and Spark-SQL syntax
# to rank user sessions by duration within each device type.
# Focus on the window frame specification differences between dialects.
# YOUR CODE HERE
# Hint: Create two query strings that rank sessions by duration within device types
# Pay attention to how window frames are specified differently

ansi_ranking_query = """
-- YOUR ANSI-SQL QUERY HERE
-- Should rank sessions by duration within each device type
"""

spark_ranking_query = """
-- YOUR SPARK-SQL QUERY HERE
-- Should be functionally identical but use Spark-SQL syntax
"""

# Test your queries (we'll use the ANSI version since we're using SQLite)


print("\n" + "="*60)
print("PANDAS AGGREGATION SECTION")
print("="*60)

# PROVIDED CODE - DO NOT MODIFY
# Prepare datetime column for time-based aggregation
events_data['timestamp'] = pd.to_datetime(events_data['timestamp'])
events_data['hour'] = events_data['timestamp'].dt.floor('H')  # Round down to nearest hour

print("Sample data with hourly grouping:")
print(events_data[['timestamp', 'hour', 'user_id', 'device_type', 'session_duration_minutes']].head())


# PRACTICE CHALLENGE 2
# TASK: Create a comprehensive hourly aggregation that includes:
# - session_count: Number of sessions per hour
# - unique_users: Number of unique users per hour
# - avg_session_duration: Average session duration per hour
# - most_popular_device: Most common device type per hour
# Hint: Combine multiple aggregation functions in a single groupby operation for efficiency
# YOUR CODE HERE
hourly_metrics = None  # Replace with your aggregation logic
# Uncomment and complete:
# hourly_metrics = events_data.groupby('hour').agg({
# YOUR AGGREGATION FUNCTIONS HERE
# })

print("\n" + "="*60)
print("DATA PIPELINE OPTIMIZATION SECTION")
print("="*60)

# PRACTICE CHALLENGE 3
# TASK: Build a complete data pipeline function that processes event data and
# exports optimized Parquet files for downstream analytics.
# The function should:
# 1. Accept a DataFrame of raw events
# 2. Perform time-based aggregations
# 3. Optimize data types for memory efficiency
# 4. Export results to Parquet format
# 5. Return summary statistics about the processing
# Hint: Consider memory optimization and data type efficiency in your implementation
# YOUR CODE HERE
def create_analytics_pipeline(events_df, output_filename='hourly_metrics.parquet'):
    """
    Complete data pipeline for event aggregation and export

    Args:
        events_df (pd.DataFrame): Raw event data
        output_filename (str): Output file path for Parquet export

    Returns:
        dict: Summary statistics about the processing
    """
    # YOUR PIPELINE IMPLEMENTATION HERE
    pass


# Test your pipeline
pipeline_results = create_analytics_pipeline(events_data)
print("Pipeline results:", pipeline_results)

print("\n" + "="*60)
print("TESTING AND VALIDATION")
print("="*60)

# PROVIDED CODE - DO NOT MODIFY
def validate_results():
    """Validation function to check if all challenges are completed correctly"""
    print("Validation checklist:")

    # Check if SQL queries are defined
    try:
        if 'ansi_ranking_query' in locals() and len(ansi_ranking_query.strip()) > 50:
            print("✅ ANSI-SQL ranking query created")
        else:
            print("❌ ANSI-SQL ranking query needs completion")

        if 'spark_ranking_query' in locals() and len(spark_ranking_query.strip()) > 50:
            print("✅ Spark-SQL ranking query created")
        else:
            print("❌ Spark-SQL ranking query needs completion")
    except:
        print("❌ SQL queries need to be defined")

    # Check if hourly metrics are created
    try:
        if hourly_metrics is not None and len(hourly_metrics) > 0:
            print("✅ Hourly metrics aggregation completed")
            print(f"✅ Generated {len(hourly_metrics)} hourly data points")
        else:
            print("❌ Hourly metrics aggregation needs completion")
    except:
        print("❌ Hourly metrics variable needs to be defined")

    # Check if pipeline function is implemented
    try:
        if hasattr(create_analytics_pipeline, '__code__') and len(create_analytics_pipeline.__code__.co_names) > 3:
            print("✅ Analytics pipeline function implemented")
        else:
            print("❌ Analytics pipeline function needs implementation")
    except:
        print("❌ Analytics pipeline function needs work")


# Run validation
validate_results()

print("\n" + "="*60)
print("LAB COMPLETE!")
print("Remember to check your work against the success checklist in the instructions.")
print("="*60)
