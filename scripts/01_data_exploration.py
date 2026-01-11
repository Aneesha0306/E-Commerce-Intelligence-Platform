import pandas as pd
import os

print("=" * 60)
print("E-COMMERCE DATA SCIENCE PROJECT - STEP 2: DATA VERIFICATION")
print("=" * 60)

# Check if data folder exists and list files
data_path = 'data/'
if os.path.exists(data_path):
    csv_files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    print(f"Found {len(csv_files)} CSV files in 'data/' folder:")
    for i, file in enumerate(csv_files, 1):
        print(f"   {i:2}. {file}")
else:
    print(f"ERROR: '{data_path}' folder not found!")
    print("   Make sure you:")
    print("   1. Downloaded dataset from Kaggle")
    print("   2. Extracted ZIP to 'data/' folder")
    print("   3. Have all 9 CSV files in 'data/'")
    exit()

# Check if we have all 9 expected files
expected_files = [
    'olist_customers_dataset.csv',
    'olist_geolocation_dataset.csv', 
    'olist_order_items_dataset.csv',
    'olist_order_payments_dataset.csv',
    'olist_order_reviews_dataset.csv',
    'olist_orders_dataset.csv',
    'olist_products_dataset.csv',
    'olist_sellers_dataset.csv',
    'olist_product_category_name_translation.csv'
]

missing_files = [f for f in expected_files if f not in csv_files]
if missing_files:
    print(f"\nWARNING: Missing {len(missing_files)} files:")
    for f in missing_files:
        print(f"   - {f}")
else:
    print("\nAll 9 expected files found!")

# Load and check key datasets
print("\n" + "=" * 60)
print("DATASET OVERVIEW:")
print("=" * 60)

datasets_to_check = [
    ('olist_orders_dataset.csv', 'Orders'),
    ('olist_customers_dataset.csv', 'Customers'),
    ('olist_order_items_dataset.csv', 'Order Items'),
    ('olist_products_dataset.csv', 'Products')
]

for file, name in datasets_to_check:
    try:
        df = pd.read_csv(f'data/{file}')
        print(f"\n{name}:")
        print(f"   Rows: {df.shape[0]:,}")
        print(f"   Columns: {df.shape[1]}")
        print(f"   Memory: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
        print(f"   Sample columns: {list(df.columns)[:5]}...")
    except Exception as e:
        print(f"\nError loading {name}: {e}")

print("\n" + "=" * 60)
print("QUICK DATA QUALITY CHECK:")
print("=" * 60)

# Check orders dataset specifically
try:
    orders_df = pd.read_csv('data/olist_orders_dataset.csv')
    print("\nOrders Dataset Details:")
    print(f"   Unique customers: {orders_df['customer_id'].nunique():,}")
    print(f"   Order statuses: {orders_df['order_status'].value_counts().to_dict()}")
    
    # Check date columns
    date_cols = [col for col in orders_df.columns if 'date' in col or 'timestamp' in col]
    print(f"   Date columns: {date_cols}")
    
    # Check for missing values
    missing = orders_df.isnull().sum()
    if missing.sum() > 0:
        print(f"   Missing values found in {len(missing[missing > 0])} columns")
        for col, count in missing[missing > 0].items():
            print(f"     - {col}: {count} missing ({count/len(orders_df)*100:.1f}%)")
    else:
        print("   No missing values found")
        
except Exception as e:
    print(f"Error in orders analysis: {e}")

print("\n" + "=" * 60)
print("STEP 2 COMPLETE - READY FOR NEXT STEP")
print("=" * 60)