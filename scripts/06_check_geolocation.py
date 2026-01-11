# File: scripts/06_check_geolocation.py
import sqlite3
import pandas as pd

print("=" * 60)
print("CHECKING GEOLOCATION DATA AVAILABILITY")
print("=" * 60)

conn = sqlite3.connect('ecommerce.db')

# Check what's in geolocation table
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM geolocation")
geo_count = cursor.fetchone()[0]
print(f"Rows in geolocation table: {geo_count:,}")

if geo_count == 0:
    print("\nGeolocation table is empty. Checking original CSV...")
    try:
        geo_df = pd.read_csv('data/olist_geolocation_dataset.csv')
        print(f"Original CSV has {geo_df.shape[0]:,} rows")
        print(f"Columns: {list(geo_df.columns)}")
        print("\nFirst 5 rows:")
        print(geo_df.head())
        
        # Check for duplicates
        print(f"\nUnique zip+city combos: {geo_df.drop_duplicates(subset=['geolocation_zip_code_prefix', 'geolocation_city']).shape[0]:,}")
        print(f"Total rows: {geo_df.shape[0]:,}")
        print(f"Duplicates: {geo_df.shape[0] - geo_df.drop_duplicates(subset=['geolocation_zip_code_prefix', 'geolocation_city']).shape[0]:,}")
        
    except Exception as e:
        print(f"Error reading CSV: {e}")

# Check customers with location info
print("\n" + "-" * 40)
print("CHECKING CUSTOMER LOCATION DATA")
print("-" * 40)

customer_loc_query = """
SELECT 
    COUNT(*) as total_customers,
    COUNT(DISTINCT customer_zip_code_prefix) as unique_zip_codes,
    COUNT(DISTINCT customer_city) as unique_cities,
    COUNT(DISTINCT customer_state) as unique_states
FROM customers
"""
loc_stats = pd.read_sql_query(customer_loc_query, conn)
print(loc_stats.to_string(index=False))

# Check sellers location
print("\n" + "-" * 40)
print("CHECKING SELLER LOCATION DATA")
print("-" * 40)

seller_loc_query = """
SELECT 
    COUNT(*) as total_sellers,
    COUNT(DISTINCT seller_zip_code_prefix) as unique_zip_codes,
    COUNT(DISTINCT seller_city) as unique_cities,
    COUNT(DISTINCT seller_state) as unique_states
FROM sellers
"""
seller_stats = pd.read_sql_query(seller_loc_query, conn)
print(seller_stats.to_string(index=False))

conn.close()