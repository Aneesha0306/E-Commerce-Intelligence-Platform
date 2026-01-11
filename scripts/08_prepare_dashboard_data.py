import pandas as pd
import os

print("=" * 60)
print("CREATING SIMPLE DASHBOARD DATA")
print("=" * 60)

# Create folder
os.makedirs('dashboard_data', exist_ok=True)

# 1. Load customer segments
segments = pd.read_csv('outputs/customer_segments.csv')
print(f"Loaded segments: {segments.shape[0]:,} rows")

# Save as is
segments.to_csv('dashboard_data/customer_segments.csv', index=False)
print("Saved: customer_segments.csv")

# 2. Load delivery data
delivery = pd.read_csv('outputs/delivery_by_state.csv')
print(f"Loaded delivery: {delivery.shape[0]:,} states")

# Add cluster info
def get_cluster(state):
    slow = ['AM', 'AL', 'PA', 'MA', 'SE', 'CE', 'PB', 'RN', 'PI', 'RO', 'BA', 'PE', 'MT', 'TO']
    if state == 'SP':
        return 'Efficient'
    elif state in slow:
        return 'Slow'
    else:
        return 'Moderate'

delivery['cluster'] = delivery['state'].apply(get_cluster)
delivery.to_csv('dashboard_data/delivery.csv', index=False)
print("Saved: delivery.csv")

# 3. Create summary table
summary = segments.groupby(['segment', 'customer_state']).agg(
    customers=('customer_id', 'count'),
    revenue=('monetary', 'sum'),
    avg_value=('monetary', 'mean')
).reset_index()

summary.to_csv('dashboard_data/summary.csv', index=False)
print("Saved: summary.csv")

# 4. Create KPIs
kpis = pd.DataFrame({
    'metric': ['Customers', 'Revenue', 'Avg Delivery', 'Slow States', 'At Risk %'],
    'value': [
        f"{len(segments):,}",
        f"R${segments['monetary'].sum():,.0f}",
        f"{delivery['avg_delivery_days'].mean():.1f} days",
        f"{len(delivery[delivery['cluster'] == 'Slow'])}",
        f"{(segments['segment'] == 'At Risk').mean()*100:.1f}%"
    ]
})

kpis.to_csv('dashboard_data/kpis.csv', index=False)
print("Saved: kpis.csv")

print("\n" + "=" * 60)
print("DONE! 4 files created in dashboard_data/")
print("1. customer_segments.csv")
print("2. delivery.csv")
print("3. summary.csv")
print("4. kpis.csv")
print("=" * 60)