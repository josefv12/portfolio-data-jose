-- ============================================================
-- Proyecto 2 — Online Retail II
-- Archivo: sql/02_queries.sql
-- Descripción: Queries analíticas — preguntas de negocio reales
-- ============================================================

SET search_path = retail;

-- ============================================================
-- QUERY 1 — Revenue mensual y crecimiento MoM
-- Pregunta: ¿En qué meses creció o cayó el negocio?
-- Técnica: Window function LAG para comparar mes anterior
-- ============================================================

SELECT
    year,
    month,
    ROUND(SUM(ii.quantity * ii.unit_price)::NUMERIC, 2)          AS revenue,
    ROUND(
        LAG(SUM(ii.quantity * ii.unit_price)) OVER (
            ORDER BY year, month
        )::NUMERIC, 2
    )                                                             AS revenue_prev_month,
    ROUND(
        (
            SUM(ii.quantity * ii.unit_price)
            - LAG(SUM(ii.quantity * ii.unit_price)) OVER (ORDER BY year, month)
        ) / NULLIF(
            LAG(SUM(ii.quantity * ii.unit_price)) OVER (ORDER BY year, month), 0
        ) * 100
    , 1)                                                          AS growth_pct
FROM invoices i
JOIN invoice_items ii ON i.invoice_no = ii.invoice_no
WHERE i.is_guest = FALSE
GROUP BY year, month
ORDER BY year, month;


-- ============================================================
-- QUERY 2 — Top 10 clientes por revenue total
-- Pregunta: ¿Quiénes son nuestros clientes más valiosos?
-- Técnica: JOIN, GROUP BY, RANK(), subconsulta
-- ============================================================

SELECT
    rank,
    customer_id,
    country,
    total_invoices,
    total_items,
    ROUND(total_revenue, 2)                                       AS total_revenue,
    ROUND(total_revenue / total_invoices, 2)                      AS avg_order_value
FROM (
    SELECT
        RANK() OVER (ORDER BY SUM(ii.quantity * ii.unit_price) DESC) AS rank,
        c.customer_id,
        c.country,
        COUNT(DISTINCT i.invoice_no)                               AS total_invoices,
        SUM(ii.quantity)                                           AS total_items,
        SUM(ii.quantity * ii.unit_price)                           AS total_revenue
    FROM customers c
    JOIN invoices i      ON c.customer_id = i.customer_id
    JOIN invoice_items ii ON i.invoice_no  = ii.invoice_no
    WHERE c.is_guest = FALSE
    GROUP BY c.customer_id, c.country
) ranked
WHERE rank <= 10
ORDER BY rank;


-- ============================================================
-- QUERY 3 — Análisis Pareto: productos que generan el 80% del revenue
-- Pregunta: ¿Cuántos productos concentran la mayor parte del negocio?
-- Técnica: SUM acumulado, porcentaje acumulado (Regla 80/20)
-- ============================================================

WITH product_revenue AS (
    SELECT
        p.stock_code,
        p.description,
        ROUND(SUM(ii.quantity * ii.unit_price)::NUMERIC, 2)       AS revenue,
        SUM(ii.quantity)                                           AS units_sold
    FROM products p
    JOIN invoice_items ii ON p.stock_code = ii.stock_code
    GROUP BY p.stock_code, p.description
),
pareto AS (
    SELECT
        stock_code,
        description,
        revenue,
        units_sold,
        ROUND(
            100.0 * SUM(revenue) OVER (ORDER BY revenue DESC)
            / SUM(revenue) OVER ()
        , 2)                                                       AS cumulative_pct,
        RANK() OVER (ORDER BY revenue DESC)                        AS rank
    FROM product_revenue
)
SELECT
    rank,
    stock_code,
    description,
    revenue,
    units_sold,
    cumulative_pct
FROM pareto
WHERE cumulative_pct <= 80
ORDER BY rank;


-- ============================================================
-- QUERY 4 — Revenue y ticket promedio por país
-- Pregunta: ¿Qué mercados internacionales son más rentables?
-- Técnica: JOIN, GROUP BY, HAVING, ORDER BY múltiple
-- ============================================================

SELECT
    i.country,
    COUNT(DISTINCT i.invoice_no)                                   AS total_orders,
    COUNT(DISTINCT i.customer_id)                                  AS unique_customers,
    ROUND(SUM(ii.quantity * ii.unit_price)::NUMERIC, 2)           AS total_revenue,
    ROUND(
        SUM(ii.quantity * ii.unit_price)::NUMERIC
        / COUNT(DISTINCT i.invoice_no)
    , 2)                                                           AS avg_order_value,
    ROUND(
        SUM(ii.quantity * ii.unit_price)::NUMERIC
        / NULLIF(COUNT(DISTINCT i.customer_id), 0)
    , 2)                                                           AS revenue_per_customer
FROM invoices i
JOIN invoice_items ii ON i.invoice_no = ii.invoice_no
WHERE i.is_guest = FALSE
GROUP BY i.country
HAVING COUNT(DISTINCT i.invoice_no) >= 10   -- mínimo 10 pedidos para ser significativo
ORDER BY total_revenue DESC;


-- ============================================================
-- QUERY 5 — Análisis RFM (Recency, Frequency, Monetary)
-- Pregunta: ¿Cómo segmentamos a los clientes por comportamiento?
-- Técnica: DATEDIFF, NTILE, múltiples CTEs, CASE
-- ============================================================

WITH rfm_base AS (
    SELECT
        c.customer_id,
        c.country,
        -- Recency: días desde la última compra (fecha máx del dataset = 2011-12-09)
        DATE_PART('day',
            '2011-12-09'::TIMESTAMP - MAX(i.invoice_date)
        )::INT                                                     AS recency_days,
        -- Frequency: número de facturas únicas
        COUNT(DISTINCT i.invoice_no)                               AS frequency,
        -- Monetary: revenue total
        ROUND(SUM(ii.quantity * ii.unit_price)::NUMERIC, 2)       AS monetary
    FROM customers c
    JOIN invoices i       ON c.customer_id = i.customer_id
    JOIN invoice_items ii ON i.invoice_no   = ii.invoice_no
    WHERE c.is_guest = FALSE
    GROUP BY c.customer_id, c.country
),
rfm_scores AS (
    SELECT
        customer_id,
        country,
        recency_days,
        frequency,
        monetary,
        -- Score 5 = mejor, 1 = peor
        -- Recency: menos días = mejor (5)
        NTILE(5) OVER (ORDER BY recency_days DESC)                 AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC)                     AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)                      AS m_score
    FROM rfm_base
)
SELECT
    customer_id,
    country,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    ROUND((r_score + f_score + m_score) / 3.0, 1)                 AS rfm_avg,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4
            THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3
            THEN 'Loyal customers'
        WHEN r_score >= 4 AND f_score <= 2
            THEN 'New customers'
        WHEN r_score <= 2 AND f_score >= 3
            THEN 'At risk'
        WHEN r_score <= 2 AND f_score <= 2
            THEN 'Lost'
        ELSE 'Potential loyalists'
    END                                                            AS segment
FROM rfm_scores
ORDER BY rfm_avg DESC;
