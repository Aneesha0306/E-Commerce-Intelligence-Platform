import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

print("=" * 60)
print("STEP 3: UNDERSTANDING DATA RELATIONSHIPS")
print("=" * 60)

# Load key datasets
print("\nLoading datasets...")
customers = pd.read_csv('data/olist_customers_dataset.csv')
orders = pd.read_csv('data/olist_orders_dataset.csv')
order_items = pd.read_csv('data/olist_order_items_dataset.csv')
order_payments = pd.read_csv('data/olist_order_payments_dataset.csv')
products = pd.read_csv('data/olist_products_dataset.csv')
sellers = pd.read_csv('data/olist_sellers_dataset.csv')

# 1. Show primary keys and foreign keys
print("\n" + "-" * 40)
print("PRIMARY KEYS ANALYSIS:")
print("-" * 40)

tables_info = {
    'customers': {'df': customers, 'pk': 'customer_id'},
    'orders': {'df': orders, 'pk': 'order_id'},
    'order_items': {'df': order_items, 'pk': ['order_id', 'order_item_id']},
    'products': {'df': products, 'pk': 'product_id'},
    'sellers': {'df': sellers, 'pk': 'seller_id'},
    'order_payments': {'df': order_payments, 'pk': ['order_id', 'payment_sequential']}
}

for table_name, info in tables_info.items():
    df = info['df']
    pk = info['pk']
    
    if isinstance(pk, list):
        # Composite key
        is_unique = df.duplicated(subset=pk).sum() == 0
        unique_count = df.drop_duplicates(subset=pk).shape[0]
    else:
        # Single column key
        is_unique = df[pk].is_unique
        unique_count = df[pk].nunique()
    
    print(f"{table_name.upper():20} | Primary Key: {pk}")
    print(f"{'':20} | Unique: {is_unique}")
    print(f"{'':20} | Total rows: {df.shape[0]:,}")
    print(f"{'':20} | Unique values: {unique_count:,}")
    if df.shape[0] != unique_count:
        print(f"{'':20} | DUPLICATES: {df.shape[0] - unique_count:,}")
    print("-" * 50)

# 2. Check relationships between tables
print("\n" + "-" * 40)
print("TABLE RELATIONSHIPS:")
print("-" * 40)

# Check orders -> customers
orders_in_customers = orders['customer_id'].isin(customers['customer_id']).mean() * 100
print(f"Orders with valid customer IDs: {orders_in_customers:.1f}%")

# Check order_items -> orders
order_items_in_orders = order_items['order_id'].isin(orders['order_id']).mean() * 100
print(f"Order items with valid order IDs: {order_items_in_orders:.1f}%")

# Check order_items -> products
order_items_in_products = order_items['product_id'].isin(products['product_id']).mean() * 100
print(f"Order items with valid product IDs: {order_items_in_products:.1f}%")

# Check order_items -> sellers
order_items_in_sellers = order_items['seller_id'].isin(sellers['seller_id']).mean() * 100
print(f"Order items with valid seller IDs: {order_items_in_sellers:.1f}%")

# 3. Create a simple ER diagram text representation
print("\n" + "-" * 40)
print("ENTITY-RELATIONSHIP DIAGRAM (Text Version):")
print("-" * 40)

er_diagram = """
CUSTOMERS (1) -----< (∞) ORDERS (1) -----< (∞) ORDER_ITEMS
    |                                               |
    | (1)                                         (∞) |
    |                                               |
    V                                               V
CUSTOMER_ZIP_CODE                               PRODUCTS (1)
    |                                               |
    | (∞)                                         (∞) |
    V                                               V
GEOLOCATION                                    ORDER_PAYMENTS (∞)
    ^                                               |
    | (∞)                                           |
    |                                               V
SELLERS (1) -----< (∞) ORDER_ITEMS (∞) -----> (1) ORDERS
                    |
                    | (∞)
                    V
                ORDER_REVIEWS

KEY:
(1) = One
(∞) = Many
-----< = One-to-Many
>-----< = Many-to-Many (through junction table)
"""

print(er_diagram)

# 4. Create relationship summary for our project
print("\n" + "-" * 40)
print("RELATIONSHIP SUMMARY FOR OUR ANALYSIS:")
print("-" * 40)

print("""
For CUSTOMER SEGMENTATION we need:
1. customers → orders (to get purchase history)
2. orders → order_items (to get products and prices)
3. order_items → products (to get categories)
4. orders → order_payments (to get payment info)

For DELIVERY ANALYSIS we need:
1. customers → geolocation (customer locations)
2. sellers → geolocation (seller locations)
3. orders (delivery dates and timestamps)

For RFM ANALYSIS we need:
1. customers (customer_id)
2. orders (dates, status)
3. order_payments (payment amounts)
""")

# 5. Save this information to a file
with open('outputs/data_relationships.txt', 'w') as f:
    f.write("DATA RELATIONSHIPS ANALYSIS\n")
    f.write("=" * 40 + "\n\n")
    
    for table_name, info in tables_info.items():
        df = info['df']
        f.write(f"{table_name.upper()}:\n")
        f.write(f"  Columns: {list(df.columns)}\n")
        f.write(f"  Shape: {df.shape}\n")
        f.write(f"  Sample data:\n")
        f.write(str(df.head(2)) + "\n\n")

print("\nRelationship analysis saved to: outputs/data_relationships.txt")
print("\n" + "=" * 60)
print("STEP 3 COMPLETE - READY FOR NEXT STEP")
print("=" * 60)