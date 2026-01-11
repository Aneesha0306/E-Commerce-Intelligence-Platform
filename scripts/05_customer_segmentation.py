import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("STEP 6: CUSTOMER SEGMENTATION WITH K-MEANS CLUSTERING")
print("=" * 60)

# Load the RFM data we saved
print("\nLoading RFM data...")
rfm_data = pd.read_csv('outputs/customer_rfm_data.csv')
print(f"RFM data shape: {rfm_data.shape}")
print(f"Columns: {list(rfm_data.columns)}")

# Show basic statistics
print("\n" + "-" * 40)
print("RFM DATA STATISTICS")
print("-" * 40)

print("\nBasic Statistics:")
print(rfm_data[['recency_days', 'frequency', 'monetary']].describe())

print("\nMissing values:")
print(rfm_data.isnull().sum())

print("\n" + "-" * 40)
print("DATA PREPARATION FOR CLUSTERING")
print("-" * 40)

# Handle missing values
rfm_clean = rfm_data.copy()
rfm_clean = rfm_clean.dropna()

# Create RFM features for clustering
# We'll use log transformation to handle skewness
rfm_features = rfm_clean[['recency_days', 'frequency', 'monetary']].copy()

# Apply log transformation (add 1 to avoid log(0))
rfm_features['recency_log'] = np.log1p(rfm_features['recency_days'])
rfm_features['frequency_log'] = np.log1p(rfm_features['frequency'])
rfm_features['monetary_log'] = np.log1p(rfm_features['monetary'])

# Drop original columns
rfm_features = rfm_features[['recency_log', 'frequency_log', 'monetary_log']]

print(f"After cleaning: {rfm_features.shape[0]} customers available for clustering")

# Standardize the features
print("\nStandardizing features...")
scaler = StandardScaler()
rfm_scaled = scaler.fit_transform(rfm_features)
rfm_scaled_df = pd.DataFrame(rfm_scaled, columns=['recency', 'frequency', 'monetary'])

print("\n" + "-" * 40)
print("FINDING OPTIMAL NUMBER OF CLUSTERS")
print("-" * 40)

# Method 1: Elbow Method
print("\nCalculating Elbow Method...")
inertia = []
k_range = range(2, 11)

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(rfm_scaled_df)
    inertia.append(kmeans.inertia_)

# Plot elbow curve
plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.plot(k_range, inertia, 'bx-')
plt.xlabel('Number of clusters (k)')
plt.ylabel('Inertia')
plt.title('Elbow Method for Optimal k')
plt.grid(True, alpha=0.3)

# Method 2: Silhouette Score
print("Calculating Silhouette Scores...")
silhouette_scores = []

for k in k_range:
    if k == 1:
        continue
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(rfm_scaled_df)
    silhouette_avg = silhouette_score(rfm_scaled_df, cluster_labels)
    silhouette_scores.append(silhouette_avg)

plt.subplot(1, 2, 2)
plt.plot(range(2, 11), silhouette_scores, 'rx-')
plt.xlabel('Number of clusters (k)')
plt.ylabel('Silhouette Score')
plt.title('Silhouette Analysis for Optimal k')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('outputs/elbow_silhouette_plot.png', dpi=100, bbox_inches='tight')
plt.close()

# Choose optimal k (based on silhouette score)
optimal_k = range(2, 11)[silhouette_scores.index(max(silhouette_scores))]
print(f"\nOptimal number of clusters: {optimal_k} (based on silhouette score)")

print("\n" + "-" * 40)
print(f"APPLYING K-MEANS WITH {optimal_k} CLUSTERS")
print("-" * 40)

# Apply K-Means with optimal k
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=20)
rfm_clean['cluster'] = kmeans.fit_predict(rfm_scaled_df)

# Add cluster centers back to original scale for interpretation
cluster_centers_scaled = kmeans.cluster_centers_
cluster_centers_original = scaler.inverse_transform(cluster_centers_scaled)

# Create cluster centers dataframe
centers_df = pd.DataFrame(
    cluster_centers_original,
    columns=['recency_log', 'frequency_log', 'monetary_log']
)

# Transform back from log scale
centers_df['recency_days'] = np.expm1(centers_df['recency_log'])
centers_df['frequency'] = np.expm1(centers_df['frequency_log'])
centers_df['monetary'] = np.expm1(centers_df['monetary_log'])

# Sort clusters by monetary value (descending)
centers_df = centers_df.sort_values('monetary', ascending=False).reset_index(drop=True)
centers_df.index.name = 'cluster_rank'

print("\nCluster Centers (Interpretable Scale):")
print(centers_df[['recency_days', 'frequency', 'monetary']].round(2))

print("\n" + "-" * 40)
print("CLUSTER ANALYSIS AND PROFILING")
print("-" * 40)

# Create cluster profiles
cluster_profiles = []

for cluster_num in range(optimal_k):
    cluster_data = rfm_clean[rfm_clean['cluster'] == cluster_num]
    
    # Calculate percentiles for better interpretation
    profile = {
        'cluster': cluster_num,
        'size': len(cluster_data),
        'size_pct': len(cluster_data) / len(rfm_clean) * 100,
        'avg_recency_days': cluster_data['recency_days'].mean(),
        'avg_frequency': cluster_data['frequency'].mean(),
        'avg_monetary': cluster_data['monetary'].mean(),
        'median_monetary': cluster_data['monetary'].median(),
        'high_value_pct': (cluster_data['monetary'] > 1000).sum() / len(cluster_data) * 100,
        'recency_percentile': np.percentile(cluster_data['recency_days'], 50),
        'frequency_percentile': np.percentile(cluster_data['frequency'], 50),
        'monetary_percentile': np.percentile(cluster_data['monetary'], 50)
    }
    cluster_profiles.append(profile)

profiles_df = pd.DataFrame(cluster_profiles)

# Sort by monetary value (descending)
profiles_df = profiles_df.sort_values('avg_monetary', ascending=False).reset_index(drop=True)

# Assign meaningful segment names based on characteristics
segment_names = []
for i, row in profiles_df.iterrows():
    recency = row['avg_recency_days']
    monetary = row['avg_monetary']
    frequency = row['avg_frequency']
    
    if monetary > 1000 and frequency > 1.5:
        segment = "Champions"
    elif monetary > 500 and recency < 200:
        segment = "Loyal Customers"
    elif monetary > 200 and frequency > 1:
        segment = "Potential Loyalists"
    elif recency > 300:
        segment = "At Risk"
    elif monetary < 100 and frequency == 1:
        segment = "New Customers"
    elif monetary < 50:
        segment = "Price Sensitive"
    else:
        segment = "Need Attention"
    
    segment_names.append(segment)

profiles_df['segment_name'] = segment_names

print("\nCLUSTER PROFILES:")
print("=" * 80)
for i, row in profiles_df.iterrows():
    print(f"\nSEGMENT: {row['segment_name']} (Cluster {row['cluster']})")
    print(f"  Size: {row['size']:,} customers ({row['size_pct']:.1f}%)")
    print(f"  Avg Recency: {row['avg_recency_days']:.0f} days since last purchase")
    print(f"  Avg Frequency: {row['avg_frequency']:.2f} orders")
    print(f"  Avg Monetary: R${row['avg_monetary']:,.2f}")
    print(f"  High-value (>R$1000): {row['high_value_pct']:.1f}%")
    print("-" * 40)

# Merge segment names back to main data
segment_map = dict(zip(profiles_df['cluster'], profiles_df['segment_name']))
rfm_clean['segment'] = rfm_clean['cluster'].map(segment_map)

print("\n" + "-" * 40)
print("VISUALIZING CLUSTERS")
print("-" * 40)

# Create visualizations
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. Segment size distribution
segment_counts = rfm_clean['segment'].value_counts()
axes[0, 0].bar(segment_counts.index, segment_counts.values)
axes[0, 0].set_title('Customer Segment Distribution')
axes[0, 0].set_xlabel('Segment')
axes[0, 0].set_ylabel('Number of Customers')
axes[0, 0].tick_params(axis='x', rotation=45)
for i, v in enumerate(segment_counts.values):
    axes[0, 0].text(i, v, f'{v:,}', ha='center', va='bottom')

# 2. Average monetary value by segment
segment_monetary = rfm_clean.groupby('segment')['monetary'].mean().sort_values(ascending=False)
axes[0, 1].bar(segment_monetary.index, segment_monetary.values, color='green')
axes[0, 1].set_title('Average Monetary Value by Segment')
axes[0, 1].set_xlabel('Segment')
axes[0, 1].set_ylabel('Average Monetary (R$)')
axes[0, 1].tick_params(axis='x', rotation=45)
for i, v in enumerate(segment_monetary.values):
    axes[0, 1].text(i, v, f'R${v:,.0f}', ha='center', va='bottom')

# 3. Recency vs Monetary scatter plot (sampled)
sample_size = min(2000, len(rfm_clean))
sample_df = rfm_clean.sample(sample_size, random_state=42)
scatter = axes[1, 0].scatter(
    sample_df['recency_days'],
    sample_df['monetary'],
    c=sample_df['cluster'],
    cmap='viridis',
    alpha=0.6,
    s=20
)
axes[1, 0].set_xlabel('Recency (days since last purchase)')
axes[1, 0].set_ylabel('Monetary Value (R$)')
axes[1, 0].set_title('Recency vs Monetary Value by Cluster')
axes[1, 0].grid(True, alpha=0.3)

# 4. Frequency distribution by segment
segment_freq = rfm_clean.groupby('segment')['frequency'].mean().sort_values(ascending=False)
axes[1, 1].bar(segment_freq.index, segment_freq.values, color='orange')
axes[1, 1].set_title('Average Purchase Frequency by Segment')
axes[1, 1].set_xlabel('Segment')
axes[1, 1].set_ylabel('Average Frequency')
axes[1, 1].tick_params(axis='x', rotation=45)
for i, v in enumerate(segment_freq.values):
    axes[1, 1].text(i, v, f'{v:.2f}', ha='center', va='bottom')

plt.tight_layout()
plt.savefig('outputs/customer_segmentation_visualizations.png', dpi=100, bbox_inches='tight')
plt.close()

print(f"Visualizations saved to: outputs/customer_segmentation_visualizations.png")

print("\n" + "-" * 40)
print("SAVING SEGMENTATION RESULTS")
print("-" * 40)

# Save the segmented data
segmented_data = rfm_clean.copy()
segmented_data.to_csv('outputs/customer_segments.csv', index=False)
print(f"Saved segmented data to: outputs/customer_segments.csv")
print(f"Rows: {segmented_data.shape[0]}, Columns: {segmented_data.shape[1]}")

# Save cluster profiles
profiles_df.to_csv('outputs/cluster_profiles.csv', index=False)
print(f"Saved cluster profiles to: outputs/cluster_profiles.csv")

# Save business recommendations based on segments
print("\n" + "-" * 40)
print("BUSINESS RECOMMENDATIONS BY SEGMENT")
print("-" * 40)

recommendations = []
for i, row in profiles_df.iterrows():
    segment = row['segment_name']
    size_pct = row['size_pct']
    monetary = row['avg_monetary']
    
    if segment == "Champions":
        rec = "VIP treatment: Exclusive offers, early access to new products, dedicated support"
    elif segment == "Loyal Customers":
        rec = "Loyalty program: Points system, birthday discounts, referral bonuses"
    elif segment == "Potential Loyalists":
        rec = "Engagement campaigns: Cross-selling suggestions, product recommendations"
    elif segment == "At Risk":
        rec = "Win-back campaigns: Special discounts, personalized emails, feedback requests"
    elif segment == "New Customers":
        rec = "Onboarding: Welcome series, first-purchase follow-up, educational content"
    elif segment == "Price Sensitive":
        rec = "Budget-friendly offers: Bundle deals, flash sales, price alerts"
    else:
        rec = "Re-engagement: Survey to understand needs, personalized recommendations"
    
    recommendations.append({
        'Segment': segment,
        'Size (%)': f"{size_pct:.1f}%",
        'Avg Value (R$)': f"{monetary:,.0f}",
        'Key Action': rec
    })

rec_df = pd.DataFrame(recommendations)
print("\nSegment-Based Marketing Recommendations:")
print("=" * 100)
print(rec_df.to_string(index=False))

# Save recommendations
rec_df.to_csv('outputs/segment_recommendations.csv', index=False)
print(f"\nSaved recommendations to: outputs/segment_recommendations.csv")

print("\n" + "=" * 60)
print("STEP 6 COMPLETE - CUSTOMER SEGMENTATION DONE")
print("=" * 60)
print("\nKey Achievements:")
print(f"1. Segmented {rfm_clean.shape[0]:,} customers into {optimal_k} clusters")
print(f"2. Created meaningful segment names based on RFM characteristics")
print(f"3. Generated visualizations and saved to outputs/")
print(f"4. Created actionable business recommendations for each segment")
print(f"5. Saved all results for dashboard creation (next step)")