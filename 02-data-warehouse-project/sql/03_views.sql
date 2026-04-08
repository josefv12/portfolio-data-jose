-- ============================================================
-- Proyecto 2 — Online Retail II
-- Archivo: sql/03_views.sql
-- Descripción: Vistas analíticas reutilizables
-- ============================================================

SET search_path = retail;

-- ============================================================
-- VIEW 1 — Revenue mensual
-- Uso: base para gráficos de serie de tiempo
-- ============================================================

CREATE OR REPLACE VIEW vw_monthly_revenue AS
SELECT
    year,
    month,
    TO_CHAR(
        TO_DATE(year::TEXT || '-' || LPAD(month::TEXT, 2, '0'), 'YYYY-MM'),
        'Mon YYYY'
    )                                                             AS period,
    COUNT(DISTINCT i.invoice_no)                                  AS total_orders,
    COUNT(DISTINCT i.customer_id)                                  AS active_customers,
    ROUND(SUM(ii.quantity * ii.unit_price)::NUMERIC, 2)           AS revenue,
    ROUND(
        SUM(ii.quantity * ii.unit_price)::NUMERIC
        / COUNT(DISTINCT i.invoice_no)
    , 2)                                                          AS avg_order_value
FROM invoices i
JOIN invoice_items ii ON i.invoice_no = ii.invoice_no
WHERE i.is_guest = FALSE
GROUP BY year, month
ORDER BY year, month;

COMMENT ON VIEW vw_monthly_revenue IS
'Revenue, pedidos y clientes activos por mes. Excluye guests.';


-- ============================================================
-- VIEW 2 — Top productos por revenue
-- Uso: ranking de productos, análisis Pareto
-- ============================================================

CREATE OR REPLACE VIEW vw_top_products AS
SELECT
    p.stock_code,
    p.description,
    SUM(ii.quantity)                                              AS units_sold,
    COUNT(DISTINCT ii.invoice_no)                                 AS times_ordered,
    ROUND(SUM(ii.quantity * ii.unit_price)::NUMERIC, 2)          AS total_revenue,
    ROUND(
        100.0 * SUM(ii.quantity * ii.unit_price)
        / SUM(SUM(ii.quantity * ii.unit_price)) OVER ()
    , 2)                                                         AS revenue_pct,
    ROUND(
        100.0 * SUM(SUM(ii.quantity * ii.unit_price)) OVER (
            ORDER BY SUM(ii.quantity * ii.unit_price) DESC
        )
        / SUM(SUM(ii.quantity * ii.unit_price)) OVER ()
    , 2)                                                         AS cumulative_pct,
    RANK() OVER (
        ORDER BY SUM(ii.quantity * ii.unit_price) DESC
    )                                                            AS revenue_rank
FROM products p
JOIN invoice_items ii ON p.stock_code = ii.stock_code
GROUP BY p.stock_code, p.description;

COMMENT ON VIEW vw_top_products IS
'Ranking de productos por revenue con porcentaje acumulado (Pareto).';


-- ============================================================
-- VIEW 3 — Revenue y ticket promedio por país
-- Uso: mapa de calor geográfico, comparativa de mercados
-- ============================================================

CREATE OR REPLACE VIEW vw_revenue_by_country AS
SELECT
    i.country,
    COUNT(DISTINCT i.invoice_no)                                  AS total_orders,
    COUNT(DISTINCT i.customer_id)                                 AS unique_customers,
    SUM(ii.quantity)                                              AS units_sold,
    ROUND(SUM(ii.quantity * ii.unit_price)::NUMERIC, 2)          AS total_revenue,
    ROUND(
        SUM(ii.quantity * ii.unit_price)::NUMERIC
        / COUNT(DISTINCT i.invoice_no)
    , 2)                                                         AS avg_order_value,
    ROUND(
        SUM(ii.quantity * ii.unit_price)::NUMERIC
        / NULLIF(COUNT(DISTINCT i.customer_id), 0)
    , 2)                                                         AS revenue_per_customer,
    RANK() OVER (
        ORDER BY SUM(ii.quantity * ii.unit_price) DESC
    )                                                            AS revenue_rank
FROM invoices i
JOIN invoice_items ii ON i.invoice_no = ii.invoice_no
WHERE i.is_guest = FALSE
GROUP BY i.country;

COMMENT ON VIEW vw_revenue_by_country IS
'Revenue, ticket promedio y clientes únicos por país.';


-- ============================================================
-- VIEW 4 — Segmentación RFM de clientes
-- Uso: targeting de campañas, análisis de retención
-- ============================================================

CREATE OR REPLACE VIEW vw_customer_rfm AS
WITH rfm_base AS (
    SELECT
        c.customer_id,
        c.country,
        DATE_PART('day',
            '2011-12-09'::TIMESTAMP - MAX(i.invoice_date)
        )::INT                                                    AS recency_days,
        COUNT(DISTINCT i.invoice_no)                              AS frequency,
        ROUND(SUM(ii.quantity * ii.unit_price)::NUMERIC, 2)      AS monetary
    FROM customers c
    JOIN invoices i       ON c.customer_id = i.customer_id
    JOIN invoice_items ii ON i.invoice_no   = ii.invoice_no
    WHERE c.is_guest = FALSE
    GROUP BY c.customer_id, c.country
),
rfm_scores AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY recency_days DESC)               AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC)                   AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)                    AS m_score
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
    ROUND((r_score + f_score + m_score) / 3.0, 1)               AS rfm_avg,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4     THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3     THEN 'Loyal customers'
        WHEN r_score >= 4 AND f_score <= 2                      THEN 'New customers'
        WHEN r_score <= 2 AND f_score >= 3                      THEN 'At risk'
        WHEN r_score <= 2 AND f_score <= 2                      THEN 'Lost'
        ELSE                                                          'Potential loyalists'
    END                                                          AS segment
FROM rfm_scores;

COMMENT ON VIEW vw_customer_rfm IS
'Segmentación RFM completa. Fecha de referencia: 2011-12-09 (último registro).';


-- ============================================================
-- VIEW 5 — Resumen de devoluciones por producto
-- Uso: identificar productos con alta tasa de retorno
-- ============================================================

CREATE OR REPLACE VIEW vw_return_rate AS
SELECT
    p.stock_code,
    p.description,
    COALESCE(s.units_sold, 0)                                    AS units_sold,
    COALESCE(r.units_returned, 0)                                AS units_returned,
    COALESCE(s.revenue, 0)                                       AS revenue,
    COALESCE(r.revenue_lost, 0)                                  AS revenue_lost,
    ROUND(
        100.0 * COALESCE(r.units_returned, 0)
        / NULLIF(COALESCE(s.units_sold, 0), 0)
    , 2)                                                         AS return_rate_pct
FROM products p
LEFT JOIN (
    SELECT stock_code,
           SUM(quantity)                                         AS units_sold,
           SUM(quantity * unit_price)                            AS revenue
    FROM invoice_items
    GROUP BY stock_code
) s ON p.stock_code = s.stock_code
LEFT JOIN (
    SELECT stock_code,
           SUM(quantity)                                         AS units_returned,
           SUM(quantity * unit_price)                            AS revenue_lost
    FROM returns
    GROUP BY stock_code
) r ON p.stock_code = r.stock_code
WHERE COALESCE(s.units_sold, 0) > 0
ORDER BY return_rate_pct DESC;

COMMENT ON VIEW vw_return_rate IS
'Tasa de devolución por producto. Útil para control de calidad.';


-- ============================================================
-- VERIFICACIÓN — listar vistas creadas
-- ============================================================
SELECT
    viewname                                                     AS view,
    pg_size_pretty(
        pg_total_relation_size(
            (schemaname || '.' || viewname)::REGCLASS
        )
    )                                                            AS size
FROM pg_views
WHERE schemaname = 'retail'
ORDER BY viewname;
