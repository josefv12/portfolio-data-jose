-- ============================================================
-- Proyecto 2 — Online Retail II
-- Archivo: sql/01_schema.sql
-- Descripción: DDL completo — tablas, PKs, FKs e índices
-- Base de datos: PostgreSQL 14+
-- ============================================================

-- ------------------------------------------------------------
-- 0. SETUP
-- ------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS retail;
SET search_path = retail;

-- ------------------------------------------------------------
-- 1. CUSTOMERS
--    Un cliente puede no tener ID (is_guest = TRUE).
--    Los guests se asignan a customer_id = 0 en invoices.
-- ------------------------------------------------------------
CREATE TABLE customers (
    customer_id     INT             PRIMARY KEY,
    country         VARCHAR(60)     NOT NULL,
    is_guest        BOOLEAN         NOT NULL DEFAULT FALSE,
    first_purchase  TIMESTAMP,
    last_purchase   TIMESTAMP
);

-- ------------------------------------------------------------
-- 2. PRODUCTS
--    Un producto puede cambiar de precio entre facturas.
--    unit_price aquí es el precio base/más frecuente.
-- ------------------------------------------------------------
CREATE TABLE products (
    stock_code      VARCHAR(20)     PRIMARY KEY,
    description     VARCHAR(255),
    unit_price      NUMERIC(10, 2)  NOT NULL CHECK (unit_price > 0)
);

-- ------------------------------------------------------------
-- 3. INVOICES
--    Cada factura pertenece a un cliente (o guest = 0).
--    country se guarda aquí también porque puede diferir
--    del país registrado del cliente.
-- ------------------------------------------------------------
CREATE TABLE invoices (
    invoice_no      VARCHAR(20)     PRIMARY KEY,
    customer_id     INT             NOT NULL REFERENCES customers(customer_id),
    country         VARCHAR(60)     NOT NULL,
    invoice_date    TIMESTAMP       NOT NULL,
    year            SMALLINT        NOT NULL,
    month           SMALLINT        NOT NULL,
    is_guest        BOOLEAN         NOT NULL DEFAULT FALSE
);

-- ------------------------------------------------------------
-- 4. INVOICE_ITEMS
--    Líneas de detalle de cada factura.
--    unit_price se guarda aquí porque puede diferir
--    del precio base del producto (descuentos, época).
-- ------------------------------------------------------------
CREATE TABLE invoice_items (
    item_id         SERIAL          PRIMARY KEY,
    invoice_no      VARCHAR(20)     NOT NULL REFERENCES invoices(invoice_no),
    stock_code      VARCHAR(20)     NOT NULL REFERENCES products(stock_code),
    quantity        INT             NOT NULL CHECK (quantity > 0),
    unit_price      NUMERIC(10, 2)  NOT NULL CHECK (unit_price > 0),
    revenue         NUMERIC(12, 2)  GENERATED ALWAYS AS (quantity * unit_price) STORED
);

-- ------------------------------------------------------------
-- 5. RETURNS
--    Facturas prefijadas con "C" en el dataset original.
--    quantity es positivo aquí — la semántica de devolución
--    está implícita en la tabla, no en el signo.
-- ------------------------------------------------------------
CREATE TABLE returns (
    return_id       SERIAL          PRIMARY KEY,
    invoice_no      VARCHAR(20)     NOT NULL,
    customer_id     INT             REFERENCES customers(customer_id),
    stock_code      VARCHAR(20)     REFERENCES products(stock_code),
    country         VARCHAR(60),
    quantity        INT             NOT NULL,
    unit_price      NUMERIC(10, 2),
    invoice_date    TIMESTAMP       NOT NULL,
    revenue_lost    NUMERIC(12, 2)  GENERATED ALWAYS AS (quantity * unit_price) STORED
);

-- ============================================================
-- ÍNDICES — para acelerar las queries analíticas
-- ============================================================

CREATE INDEX idx_invoices_customer    ON invoices(customer_id);
CREATE INDEX idx_invoices_date        ON invoices(invoice_date);
CREATE INDEX idx_invoices_year_month  ON invoices(year, month);
CREATE INDEX idx_invoices_country     ON invoices(country);

CREATE INDEX idx_items_invoice        ON invoice_items(invoice_no);
CREATE INDEX idx_items_stock          ON invoice_items(stock_code);

CREATE INDEX idx_returns_customer     ON returns(customer_id);
CREATE INDEX idx_returns_stock        ON returns(stock_code);
CREATE INDEX idx_returns_date         ON returns(invoice_date);

-- ============================================================
-- CLIENTE GUEST (customer_id = 0)
-- Registro especial para agrupar todos los pedidos anónimos.
-- Se inserta antes de cargar los datos.
-- ============================================================
INSERT INTO customers (customer_id, country, is_guest)
VALUES (0, 'Unknown', TRUE);

-- ============================================================
-- COMENTARIOS DE TABLAS
-- ============================================================
COMMENT ON TABLE customers     IS 'Clientes registrados y guests (customer_id=0)';
COMMENT ON TABLE products      IS 'Catálogo de productos con precio base';
COMMENT ON TABLE invoices      IS 'Cabeceras de factura — una por transacción';
COMMENT ON TABLE invoice_items IS 'Líneas de detalle — revenue calculado automáticamente';
COMMENT ON TABLE returns       IS 'Devoluciones separadas del flujo de ventas';

COMMENT ON COLUMN invoice_items.revenue  IS 'quantity * unit_price — columna generada';
COMMENT ON COLUMN returns.revenue_lost   IS 'quantity * unit_price — columna generada';
COMMENT ON COLUMN invoices.customer_id   IS '0 = pedido guest sin Customer ID';
