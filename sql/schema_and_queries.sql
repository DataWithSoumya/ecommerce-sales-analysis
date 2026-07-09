-- ============================================================
-- E-commerce Sales Analysis — SQL Schema & Business Queries
-- Works with SQLite / PostgreSQL / MySQL (minor syntax tweaks
-- may be needed for date functions depending on engine)
-- ============================================================

-- ---------- SCHEMA ----------
CREATE TABLE IF NOT EXISTS orders (
    order_id        TEXT PRIMARY KEY,
    customer_id     TEXT NOT NULL,
    order_date      DATE NOT NULL,
    region          TEXT,
    category        TEXT,
    product         TEXT,
    quantity        INTEGER,
    unit_price      NUMERIC,
    discount_pct    NUMERIC,
    discount_amount NUMERIC,
    gross_amount    NUMERIC,
    net_amount      NUMERIC,
    payment_method  TEXT,
    order_status    TEXT
);

-- Load orders_clean.csv into this table before running queries below.
-- Example (SQLite CLI):
--   sqlite3 sales.db
--   .mode csv
--   .import data/orders_clean.csv orders

-- ============================================================
-- BUSINESS QUESTIONS
-- ============================================================

-- Q1. What is total revenue and order count by month?
SELECT
    strftime('%Y-%m', order_date) AS month,
    COUNT(DISTINCT order_id)      AS total_orders,
    SUM(net_amount)               AS total_revenue
FROM orders
WHERE order_status != 'Cancelled'
GROUP BY month
ORDER BY month;

-- Q2. Which product categories generate the most revenue?
SELECT
    category,
    SUM(net_amount) AS total_revenue,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(net_amount) / COUNT(DISTINCT order_id), 2) AS avg_order_value
FROM orders
WHERE order_status != 'Cancelled'
GROUP BY category
ORDER BY total_revenue DESC;

-- Q3. Top 10 customers by lifetime spend
SELECT
    customer_id,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(net_amount)          AS lifetime_spend
FROM orders
WHERE order_status != 'Cancelled'
GROUP BY customer_id
ORDER BY lifetime_spend DESC
LIMIT 10;

-- Q4. Return rate by category (which products get returned most?)
SELECT
    category,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN order_status = 'Returned' THEN 1 ELSE 0 END) AS returned_orders,
    ROUND(100.0 * SUM(CASE WHEN order_status = 'Returned' THEN 1 ELSE 0 END) / COUNT(*), 2) AS return_rate_pct
FROM orders
GROUP BY category
ORDER BY return_rate_pct DESC;

-- Q5. Revenue and order share by region
SELECT
    region,
    SUM(net_amount) AS total_revenue,
    ROUND(100.0 * SUM(net_amount) / (SELECT SUM(net_amount) FROM orders WHERE order_status != 'Cancelled'), 2) AS pct_of_total_revenue
FROM orders
WHERE order_status != 'Cancelled'
GROUP BY region
ORDER BY total_revenue DESC;

-- Q6. Most preferred payment methods
SELECT
    payment_method,
    COUNT(*) AS total_orders,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM orders), 2) AS pct_of_orders
FROM orders
GROUP BY payment_method
ORDER BY total_orders DESC;

-- Q7. Month-over-month revenue growth (%)
WITH monthly_rev AS (
    SELECT
        strftime('%Y-%m', order_date) AS month,
        SUM(net_amount) AS revenue
    FROM orders
    WHERE order_status != 'Cancelled'
    GROUP BY month
)
SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month)) / LAG(revenue) OVER (ORDER BY month), 2) AS mom_growth_pct
FROM monthly_rev
ORDER BY month;

-- Q8. Customers who haven't ordered in the last 90 days (churn risk)
-- (Assumes CURRENT_DATE is the reference point; adjust as needed)
SELECT
    customer_id,
    MAX(order_date) AS last_order_date,
    julianday('now') - julianday(MAX(order_date)) AS days_since_last_order
FROM orders
GROUP BY customer_id
HAVING days_since_last_order > 90
ORDER BY days_since_last_order DESC;

-- Q9. Discount effectiveness: does higher discount correlate with higher quantity sold?
SELECT
    discount_pct,
    COUNT(*) AS num_orders,
    SUM(quantity) AS total_units_sold,
    ROUND(AVG(quantity), 2) AS avg_units_per_order
FROM orders
WHERE order_status != 'Cancelled'
GROUP BY discount_pct
ORDER BY discount_pct;

-- Q10. Rank products within each category by revenue (window function)
SELECT
    category,
    product,
    SUM(net_amount) AS product_revenue,
    RANK() OVER (PARTITION BY category ORDER BY SUM(net_amount) DESC) AS rank_in_category
FROM orders
WHERE order_status != 'Cancelled'
GROUP BY category, product
ORDER BY category, rank_in_category;
