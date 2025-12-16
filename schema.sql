-- ===============  СПРАВОЧНИКИ  ===============
CREATE TABLE product_types (
    id              INT PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    coefficient     NUMERIC(10,2) NOT NULL CHECK (coefficient > 0)
);

CREATE TABLE material_types (
    id              INT PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    loss_percent    NUMERIC(10,6) NOT NULL CHECK (loss_percent >= 0)
);

-- ===============  ОСНОВНЫЕ СУЩНОСТИ  ===============
CREATE TABLE workshops (
    id                  INT PRIMARY KEY,
    name                TEXT NOT NULL UNIQUE,
    workshop_type       TEXT NOT NULL,
    people_count        INT NOT NULL CHECK (people_count >= 0)
);

CREATE TABLE products (
    id              INT PRIMARY KEY,
    product_type_id INT NOT NULL REFERENCES product_types(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    material_type_id INT NOT NULL REFERENCES material_types(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    name            TEXT NOT NULL UNIQUE,
    article         TEXT NOT NULL UNIQUE,
    min_partner_cost NUMERIC(14,2) NOT NULL CHECK (min_partner_cost >= 0)
);

-- связь продукт-цех + время
-- ВАЖНО: по ТЗ "время изготовления должно быть целым неотрицательным".
-- Поэтому храним минуты как INT.
CREATE TABLE product_workshops (
    product_id      INT NOT NULL REFERENCES products(id) ON UPDATE CASCADE ON DELETE CASCADE,
    workshop_id     INT NOT NULL REFERENCES workshops(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    time_minutes    INT NOT NULL CHECK (time_minutes >= 0),
    PRIMARY KEY (product_id, workshop_id)
);

-- ===============  ПОЛЕЗНЫЕ ИНДЕКСЫ  ===============
CREATE INDEX idx_products_product_type ON products(product_type_id);
CREATE INDEX idx_products_material_type ON products(material_type_id);
CREATE INDEX idx_pw_workshop ON product_workshops(workshop_id);

-- ===============  VIEW: список цехов для продукта  ===============
CREATE OR REPLACE VIEW v_product_workshops AS
SELECT
    p.id AS product_id,
    p.name AS product_name,
    w.id AS workshop_id,
    w.name AS workshop_name,
    w.workshop_type,
    w.people_count,
    pw.time_minutes
FROM product_workshops pw
JOIN products p ON p.id = pw.product_id
JOIN workshops w ON w.id = pw.workshop_id;

-- ===============  VIEW: общее время изготовления (в минутах и часах)  ===============
CREATE OR REPLACE VIEW v_product_total_time AS
SELECT
    p.id AS product_id,
    p.name AS product_name,
    COALESCE(SUM(pw.time_minutes), 0) AS total_time_minutes,
    CEIL(COALESCE(SUM(pw.time_minutes), 0) / 60.0)::INT AS total_time_hours_int
FROM products p
LEFT JOIN product_workshops pw ON pw.product_id = p.id
GROUP BY p.id, p.name;