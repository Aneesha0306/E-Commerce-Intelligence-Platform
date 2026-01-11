import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

print("=" * 60)
print("STEP 5: TESTING SQL DATABASE & DATA CLEANING")
print("=" * 60)

# Connect to database
db_path = 'ecommerce.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print(f"\nConnected to database: {db_path}")
print(f"Database size: {os.path.getsize(db_path) / (1024*1024):.2f} MB")

print("\n" + "-" * 40)
print("DATABASE OVERVIEW")
print("-" * 40)

# Get table information
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"Tables in database: {len(tables)}")
for table in tables:
    table_name = table[0]
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"  {table_name:30}: {count:,} rows")

print("\n" + "-" * 40)
print("FIXING DATA ISSUES IDENTIFIED IN STEP 4")
print("-" * 40)

# 1. Fix geolocation table (duplicate primary keys)
print("\n1. Fixing geolocation duplicates...")
cursor.execute("""
    DELETE FROM geolocation 
    WHERE rowid NOT IN (
        SELECT MIN(rowid) 
        FROM geolocation 
        GROUP BY geolocation_zip_code_prefix, geolocation_city
    )
""")
deleted_geo = cursor.rowcount
cursor.execute("SELECT COUNT(*) FROM geolocation")
geo_count = cursor.fetchone()[0]
print(f"   Removed {deleted_geo:,} duplicate rows")
print(f"   Geolocation rows after cleanup: {geo_count:,}")

# 2. Fix order_reviews table (duplicate review_id)
print("\n2. Fixing order_reviews duplicates...")
cursor.execute("""
    DELETE FROM order_reviews 
    WHERE rowid NOT IN (
        SELECT MIN(rowid) 
        FROM order_reviews 
        GROUP BY review_id
    )
""")
deleted_reviews = cursor.rowcount
cursor.execute("SELECT COUNT(*) FROM order_reviews")
review_count = cursor.fetchone()[0]
print(f"   Removed {deleted_reviews:,} duplicate rows")
print(f"   Order reviews rows after cleanup: {review_count:,}")

conn.commit()

print("\n" + "-" * 40)
print("TESTING KEY BUSINESS QUERIES")
print("-" * 40)

# Query 1: Basic RFM metrics
print("\nQUERY 1: CUSTOMER PURCHASE SUMMARY")
rfm_query = """
SELECT 
    COUNT(DISTINCT c.customer_id) as total_customers,
    COUNT(DISTINCT o.order_id) as total_orders,
    SUM(op.payment_value) as total_revenue,
    AVG(op.payment_value) as avg_order_value,
    COUNT(DISTINCT CASE WHEN o.order_status = 'delivered' THEN o.order_id END) as delivered_orders
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN order_payments op ON o.order_id = op.order_id
"""
rfm_result = pd.read_sql_query(rfm_query, conn)
print(rfm_result.to_string(index=False))

# Query 2: Revenue by state
print("\nQUERY 2: REVENUE BY STATE (Top 10)")
state_revenue_query = """
SELECT 
    c.customer_state,
    COUNT(DISTINCT o.order_id) as order_count,
    COUNT(DISTINCT c.customer_id) as customer_count,
    SUM(op.payment_value) as total_revenue,
    AVG(op.payment_value) as avg_order_value
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_payments op ON o.order_id = op.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY total_revenue DESC
LIMIT 10
"""
state_revenue = pd.read_sql_query(state_revenue_query, conn)
print(state_revenue.to_string(index=False))

# Query 3: Delivery performance
print("\nQUERY 3: DELIVERY TIME ANALYSIS")
delivery_query = """
SELECT 
    c.customer_state,
    COUNT(*) as delivered_orders,
    AVG(JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp)) as avg_delivery_days,
    MIN(JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp)) as min_delivery_days,
    MAX(JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp)) as max_delivery_days
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
    AND o.order_purchase_timestamp IS NOT NULL
GROUP BY c.customer_state
HAVING delivered_orders > 100
ORDER BY avg_delivery_days DESC
LIMIT 10
"""
delivery_results = pd.read_sql_query(delivery_query, conn)
print(delivery_results.to_string(index=False))

# Query 4: Product category performance
print("\nQUERY 4: TOP PRODUCT CATEGORIES BY REVENUE")
product_query = """
SELECT 
    p.product_category_name,
    COUNT(DISTINCT oi.order_id) as order_count,
    SUM(oi.price) as total_sales,
    AVG(oi.price) as avg_price,
    COUNT(DISTINCT oi.product_id) as unique_products
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
    AND p.product_category_name IS NOT NULL
GROUP BY p.product_category_name
ORDER BY total_sales DESC
LIMIT 10
"""
product_results = pd.read_sql_query(product_query, conn)
print(product_results.to_string(index=False))

print("\n" + "-" * 40)
print("CALCULATING RFM METRICS FOR CUSTOMER SEGMENTATION")
print("-" * 40)

# Create RFM table for segmentation
rfm_calc_query = """
CREATE TABLE IF NOT EXISTS customer_rfm AS
SELECT 
    c.customer_id,
    c.customer_state,
    
    -- Recency: Days since last purchase
    JULIANDAY('2018-10-17') - JULIANDAY(MAX(o.order_purchase_timestamp)) as recency_days,
    
    -- Frequency: Total orders
    COUNT(DISTINCT o.order_id) as frequency,
    
    -- Monetary: Total spent
    COALESCE(SUM(op.payment_value), 0) as monetary,
    
    -- Additional useful metrics
    AVG(op.payment_value) as avg_order_value,
    MIN(DATE(o.order_purchase_timestamp)) as first_purchase_date,
    MAX(DATE(o.order_purchase_timestamp)) as last_purchase_date,
    COUNT(DISTINCT p.product_category_name) as unique_categories,
    AVG(oi.price) as avg_product_price
    
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN order_payments op ON o.order_id = op.order_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
LEFT JOIN products p ON oi.product_id = p.product_id
WHERE o.order_status = 'delivered' OR o.order_id IS NULL
GROUP BY c.customer_id, c.customer_state
"""

cursor.execute("DROP TABLE IF EXISTS customer_rfm")
cursor.execute(rfm_calc_query)
conn.commit()

# Check RFM table
cursor.execute("SELECT COUNT(*) FROM customer_rfm")
rfm_count = cursor.fetchone()[0]
print(f"Created customer_rfm table with {rfm_count:,} customers")

# Show RFM statistics
rfm_stats_query = """
SELECT 
    COUNT(*) as total_customers,
    AVG(recency_days) as avg_recency_days,
    AVG(frequency) as avg_frequency,
    AVG(monetary) as avg_monetary,
    SUM(CASE WHEN frequency = 0 THEN 1 ELSE 0 END) as one_time_buyers,
    SUM(CASE WHEN frequency > 1 THEN 1 ELSE 0 END) as repeat_buyers,
    SUM(CASE WHEN monetary > 1000 THEN 1 ELSE 0 END) as high_value_customers
FROM customer_rfm
"""
rfm_stats = pd.read_sql_query(rfm_stats_query, conn)
print("\nRFM Statistics Summary:")
print(rfm_stats.to_string(index=False))

print("\n" + "-" * 40)
print("SAVING KEY INSIGHTS FOR NEXT STEP")
print("-" * 40)

# Save the RFM data to CSV for next step
rfm_data = pd.read_sql_query("SELECT * FROM customer_rfm", conn)
rfm_data.to_csv('outputs/customer_rfm_data.csv', index=False)
print(f"Saved RFM data to: outputs/customer_rfm_data.csv")
print(f"Rows: {rfm_data.shape[0]}, Columns: {rfm_data.shape[1]}")

# Save query results for documentation
with open('outputs/sql_query_results.txt', 'w') as f:
    f.write("SQL QUERY RESULTS FROM DATABASE TESTING\n")
    f.write("=" * 50 + "\n\n")
    
    f.write("QUERY 1: CUSTOMER PURCHASE SUMMARY\n")
    f.write(str(rfm_result) + "\n\n")
    
    f.write("QUERY 2: REVENUE BY STATE (Top 10)\n")
    f.write(str(state_revenue) + "\n\n")
    
    f.write("QUERY 3: DELIVERY TIME ANALYSIS\n")
    f.write(str(delivery_results) + "\n\n")
    
    f.write("QUERY 4: TOP PRODUCT CATEGORIES\n")
    f.write(str(product_results) + "\n\n")
    
    f.write("RFM STATISTICS SUMMARY\n")
    f.write(str(rfm_stats) + "\n")

print(f"Saved query results to: outputs/sql_query_results.txt")

# Close connection
conn.close()

print("\n" + "=" * 60)
print("STEP 5 COMPLETE - DATABASE TESTED AND CLEANED")
print("=" * 60)
print("\nKey Achievements:")
print("1. Fixed duplicate data issues in geolocation and order_reviews")
print("2. Tested 4 key business queries successfully")
print("3. Created customer_rfm table with RFM metrics")
print("4. Saved RFM data for segmentation (next step)")
print("5. Documented all query results")
print("\nReady for Step 6: Customer Segmentation with K-Means")