"""
E-commerce Sales Analysis
--------------------------
This script:
1. Loads raw order data
2. Cleans it (missing values, inconsistent text, duplicates)
3. Computes key business metrics
4. Generates charts for the README / dashboard
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

pd.set_option("display.float_format", lambda x: f"{x:,.2f}")

# ---------- 1. LOAD ----------
df = pd.read_csv("data/orders.csv", parse_dates=["order_date"])
print(f"Raw rows: {len(df)}")

# ---------- 2. CLEAN ----------
# drop exact duplicates
before = len(df)
df = df.drop_duplicates()
print(f"Removed {before - len(df)} duplicate rows")

# standardize text columns
df["region"] = df["region"].str.strip().str.title()
df["payment_method"] = df["payment_method"].str.strip()
df["category"] = df["category"].str.strip()

# handle missing unit_price -> fill with category median
df["unit_price"] = df.groupby("category")["unit_price"].transform(
    lambda x: x.fillna(x.median())
)

# recompute amounts for rows where price was missing (recalculate to be safe)
df["gross_amount"] = df["unit_price"] * df["quantity"]
df["discount_amount"] = df["gross_amount"] * df["discount_pct"] / 100
df["net_amount"] = df["gross_amount"] - df["discount_amount"]

# exclude cancelled orders from revenue (business rule)
completed = df[df["order_status"] != "Cancelled"].copy()

df.to_csv("data/orders_clean.csv", index=False)
print("Saved cleaned data to data/orders_clean.csv")

# ---------- 3. KEY METRICS ----------
total_revenue = completed["net_amount"].sum()
total_orders = completed["order_id"].nunique()
avg_order_value = completed.groupby("order_id")["net_amount"].sum().mean()
return_rate = (df["order_status"] == "Returned").mean() * 100

print("\n--- KEY METRICS ---")
print(f"Total Revenue: Rs. {total_revenue:,.0f}")
print(f"Total Orders: {total_orders:,}")
print(f"Average Order Value: Rs. {avg_order_value:,.0f}")
print(f"Return Rate: {return_rate:.1f}%")

# ---------- 4. CHARTS ----------
plt.style.use("seaborn-v0_8-whitegrid")

# 4a. Monthly revenue trend
completed["month"] = completed["order_date"].dt.to_period("M").astype(str)
monthly = completed.groupby("month")["net_amount"].sum().sort_index()

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(monthly.index, monthly.values, marker="o", color="#2E86AB")
ax.set_title("Monthly Revenue Trend (2024-2025)", fontsize=14, fontweight="bold")
ax.set_ylabel("Revenue (Rs. )")
ax.set_xlabel("Month")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}K"))
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("images/monthly_revenue_trend.png", dpi=150)
plt.close()

# 4b. Revenue by category
cat_rev = completed.groupby("category")["net_amount"].sum().sort_values(ascending=True)

fig, ax = plt.subplots(figsize=(9, 5))
ax.barh(cat_rev.index, cat_rev.values, color="#A23B72")
ax.set_title("Revenue by Category", fontsize=14, fontweight="bold")
ax.set_xlabel("Revenue (Rs. )")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}K"))
plt.tight_layout()
plt.savefig("images/revenue_by_category.png", dpi=150)
plt.close()

# 4c. Revenue by region
region_rev = completed.groupby("region")["net_amount"].sum().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(7, 5))
ax.bar(region_rev.index, region_rev.values, color="#F18F01")
ax.set_title("Revenue by Region", fontsize=14, fontweight="bold")
ax.set_ylabel("Revenue (Rs. )")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}K"))
plt.tight_layout()
plt.savefig("images/revenue_by_region.png", dpi=150)
plt.close()

# 4d. Order status breakdown
status_counts = df["order_status"].value_counts()

fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(status_counts.values, labels=status_counts.index, autopct="%1.1f%%",
       colors=["#2E86AB", "#F18F01", "#C73E1D", "#A23B72"])
ax.set_title("Order Status Breakdown", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("images/order_status_breakdown.png", dpi=150)
plt.close()

# 4e. Payment method popularity
pay_counts = df["payment_method"].value_counts()

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(pay_counts.index, pay_counts.values, color="#2E86AB")
ax.set_title("Orders by Payment Method", fontsize=14, fontweight="bold")
ax.set_ylabel("Number of Orders")
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
plt.savefig("images/payment_method_popularity.png", dpi=150)
plt.close()

print("\nCharts saved to images/")

# ---------- 5. Save summary for README ----------
with open("summary_metrics.txt", "w") as f:
    f.write(f"Total Revenue: Rs. {total_revenue:,.0f}\n")
    f.write(f"Total Orders: {total_orders:,}\n")
    f.write(f"Average Order Value: Rs. {avg_order_value:,.0f}\n")
    f.write(f"Return Rate: {return_rate:.1f}%\n")
    f.write(f"Top Category: {cat_rev.idxmax()}\n")
    f.write(f"Top Region: {region_rev.idxmax()}\n")
