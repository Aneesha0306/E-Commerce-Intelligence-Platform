import sqlite3
import pandas as pd
import os
import time

print("=" * 60)
print("STEP 4: CREATING SQL DATABASE")
print("=" * 60)

# Create database connection
db_path = 'ecommerce.db'
print(f"\nCreating SQLite database: {db_path}")

# Remove existing database if exists
if os.path.exists(db_path):
    os.remove(db_path)
    print("Removed existing database")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("\n" + "-" * 40)
print("CREATING TABLES WITH PROPER SCHEMA")
print("-" * 40)

# 1. Create customers table
cursor.execute('''
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    customer_unique_id TEXT NOT NULL,
    customer_zip_code_prefix INTEGER,
    customer_city TEXT,
    customer_state TEXT
)
''')
print("Created table: customers")

# 2. Create geolocation table
cursor.execute('''
CREATE TABLE geolocation (
    geolocation_zip_code_prefix INTEGER,
    geolocation_lat REAL,
    geolocation_lng REAL,
    geolocation_city TEXT,
    geolocation_state TEXT,
    PRIMARY KEY (geolocation_zip_code_prefix, geolocation_city)
)
''')
print("Created table: geolocation")

# 3. Create orders table
cursor.execute('''
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT,
    order_status TEXT,
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
)
''')
print("Created table: orders")

# 4. Create order_items table
cursor.execute('''
CREATE TABLE order_items (
    order_id TEXT,
    order_item_id INTEGER,
    product_id TEXT,
    seller_id TEXT,
    shipping_limit_date TIMESTAMP,
    price REAL,
    freight_value REAL,
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id)
)
''')
print("Created table: order_items")

# 5. Create products table
cursor.execute('''
CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    product_category_name TEXT,
    product_name_lenght INTEGER,
    product_description_lenght INTEGER,
    product_photos_qty INTEGER,
    product_weight_g INTEGER,
    product_length_cm INTEGER,
    product_height_cm INTEGER,
    product_width_cm INTEGER
)
''')
print("Created table: products")

# 6. Create sellers table
cursor.execute('''
CREATE TABLE sellers (
    seller_id TEXT PRIMARY KEY,
    seller_zip_code_prefix INTEGER,
    seller_city TEXT,
    seller_state TEXT
)
''')
print("Created table: sellers")

# 7. Create order_payments table
cursor.execute('''
CREATE TABLE order_payments (
    order_id TEXT,
    payment_sequential INTEGER,
    payment_type TEXT,
    payment_installments INTEGER,
    payment_value REAL,
    PRIMARY KEY (order_id, payment_sequential),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
)
''')
print("Created table: order_payments")

# 8. Create order_reviews table
cursor.execute('''
CREATE TABLE order_reviews (
    review_id TEXT PRIMARY KEY,
    order_id TEXT,
    review_score INTEGER,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
)
''')
print("Created table: order_reviews")

# 9. Create product_category_translation table
cursor.execute('''
CREATE TABLE product_category_translation (
    product_category_name TEXT PRIMARY KEY,
    product_category_name_english TEXT
)
''')
print("Created table: product_category_translation")

print("\n" + "-" * 40)
print("LOADING DATA INTO TABLES")
print("-" * 40)

# Load data from CSV files
tables_to_load = [
    ('customers', 'data/olist_customers_dataset.csv'),
    ('geolocation', 'data/olist_geolocation_dataset.csv'),
    ('orders', 'data/olist_orders_dataset.csv'),
    ('order_items', 'data/olist_order_items_dataset.csv'),
    ('products', 'data/olist_products_dataset.csv'),
    ('sellers', 'data/olist_sellers_dataset.csv'),
    ('order_payments', 'data/olist_order_payments_dataset.csv'),
    ('order_reviews', 'data/olist_order_reviews_dataset.csv'),
    ('product_category_translation', 'data/product_category_name_translation.csv')
]

total_rows_loaded = 0
start_time = time.time()

for table_name, file_path in tables_to_load:
    try:
        # Read CSV
        df = pd.read_csv(file_path)
        rows = len(df)
        
        # Handle date columns for specific tables
        if table_name == 'orders':
            date_cols = ['order_purchase_timestamp', 'order_approved_at', 
                        'order_delivered_carrier_date', 'order_delivered_customer_date',
                        'order_estimated_delivery_date']
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
        
        elif table_name == 'order_items':
            if 'shipping_limit_date' in df.columns:
                df['shipping_limit_date'] = pd.to_datetime(df['shipping_limit_date'], errors='coerce')
        
        elif table_name == 'order_reviews':
            date_cols = ['review_creation_date', 'review_answer_timestamp']
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Load into SQLite
        df.to_sql(table_name, conn, if_exists='append', index=False)
        total_rows_loaded += rows
        print(f"Loaded {rows:,} rows into {table_name}")
        
    except Exception as e:
        print(f"Error loading {table_name}: {e}")

print("\n" + "-" * 40)
print("DATABASE VERIFICATION")
print("-" * 40)

# Verify data was loaded correctly
verification_queries = [
    ("Total customers", "SELECT COUNT(*) FROM customers"),
    ("Total orders", "SELECT COUNT(*) FROM orders"),
    ("Total order items", "SELECT COUNT(*) FROM order_items"),
    ("Total products", "SELECT COUNT(*) FROM products"),
    ("Total sellers", "SELECT COUNT(*) FROM sellers"),
    ("Delivered orders", "SELECT COUNT(*) FROM orders WHERE order_status = 'delivered'"),
    ("Average order value", "SELECT AVG(payment_value) FROM order_payments"),
    ("Unique product categories", "SELECT COUNT(DISTINCT product_category_name) FROM products"),
]

for description, query in verification_queries:
    try:
        result = cursor.execute(query).fetchone()[0]
        if isinstance(result, float):
            print(f"{description:30}: {result:,.2f}")
        else:
            print(f"{description:30}: {result:,}")
    except:
        print(f"{description:30}: Error executing query")

# Create indexes for better query performance
print("\n" + "-" * 40)
print("CREATING INDEXES FOR PERFORMANCE")
print("-" * 40)

indexes = [
    "CREATE INDEX idx_orders_customer_id ON orders(customer_id)",
    "CREATE INDEX idx_orders_status ON orders(order_status)",
    "CREATE INDEX idx_order_items_order_id ON order_items(order_id)",
    "CREATE INDEX idx_order_items_product_id ON order_items(product_id)",
    "CREATE INDEX idx_order_payments_order_id ON order_payments(order_id)",
    "CREATE INDEX idx_products_category ON products(product_category_name)",
    "CREATE INDEX idx_customers_state ON customers(customer_state)",
    "CREATE INDEX idx_orders_dates ON orders(order_purchase_timestamp)",
]

for idx in indexes:
    try:
        cursor.execute(idx)
        idx_name = idx.split('ON ')[1].split('(')[0]
        print(f"Created index: {idx_name}")
    except:
        pass

# Save some sample queries for later use
print("\n" + "-" * 40)
print("SAVING SAMPLE QUERIES")
print("-" * 40)

sample_queries = {
    "rfm_base_query.sql": """
-- RFM Base Query: Gets customer purchase history
SELECT 
    c.customer_id,
    c.customer_state,
    COUNT(DISTINCT o.order_id) as frequency,
    MAX(DATE(o.order_purchase_timestamp)) as last_purchase_date,
    SUM(op.payment_value) as monetary_value,
    AVG(op.payment_value) as avg_order_value
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_payments op ON o.order_id = op.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_id, c.customer_state
ORDER BY monetary_value DESC
LIMIT 10;
""",
    
    "delivery_analysis_query.sql": """
-- Delivery Analysis: Calculates delivery times
SELECT 
    c.customer_state,
    AVG(JULIANDAY(o.order_delivered_customer_date) - 
        JULIANDAY(o.order_purchase_timestamp)) as avg_delivery_days,
    COUNT(*) as order_count
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
    AND o.order_purchase_timestamp IS NOT NULL
GROUP BY c.customer_state
ORDER BY avg_delivery_days DESC;
"""
}

# Create sql_queries folder
os.makedirs('sql_queries', exist_ok=True)

for filename, query in sample_queries.items():
    with open(f'sql_queries/{filename}', 'w') as f:
        f.write(query)
    print(f"Saved: sql_queries/{filename}")

# Calculate and show statistics
elapsed_time = time.time() - start_time
db_size = os.path.getsize(db_path) / (1024*1024)  # MB

print("\n" + "-" * 40)
print("DATABASE CREATION SUMMARY")
print("-" * 40)
print(f"Total rows loaded: {total_rows_loaded:,}")
print(f"Database size: {db_size:.2f} MB")
print(f"Time taken: {elapsed_time:.2f} seconds")
print(f"Tables created: 9")
print(f"Indexes created: 8")
print(f"Sample queries saved: 2")

# Close connection
conn.commit()
conn.close()

print("\n" + "=" * 60)
print("STEP 4 COMPLETE - SQL DATABASE READY")
print("=" * 60)
print("\nNext: Test the database with SQL queries")
print("Database file: ecommerce.db")