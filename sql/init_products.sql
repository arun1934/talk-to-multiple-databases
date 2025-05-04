-- Create products table
CREATE TABLE IF NOT EXISTS public.products (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    sku VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample product data
INSERT INTO public.products (product_id, product_name, description, price, sku, created_at) VALUES
(101, 'Luxury Leather Sofa Set', '3-seater premium leather sofa with matching armchairs', 8999.99, 'LR-SOFA-001', '2023-12-01'),
(102, 'Modern Fabric Sofa', 'Contemporary design fabric sofa in neutral colors', 4599.99, 'LR-SOFA-002', '2023-12-02'),
(103, 'Dining Table Set - Oak', '6-seater solid oak dining table with chairs', 5799.99, 'DR-TABLE-001', '2023-12-03'),
(104, 'King Size Bedroom Set', 'Complete bedroom set with king bed, wardrobes, and side tables', 12999.99, 'BR-SET-001', '2023-12-04'),
(105, 'Executive Office Desk', 'Large executive desk with built-in storage', 3299.99, 'OF-DESK-001', '2023-12-05'),
(106, 'Sliding Door Wardrobe', '3-door sliding wardrobe with mirror finish', 4899.99, 'BR-WARD-001', '2023-12-06'),
(107, 'Kitchen Cabinet Set', 'Modular kitchen cabinets with soft-close drawers', 7499.99, 'KT-CAB-001', '2023-12-07'),
(108, 'Sectional Sofa L-Shape', 'Large L-shaped sectional with ottoman', 6999.99, 'LR-SOFA-003', '2023-12-08'),
(109, 'Outdoor Patio Set', 'Weather-resistant outdoor furniture set', 3899.99, 'OD-PATIO-001', '2023-12-09'),
(110, 'Ergonomic Office Chair', 'High-back ergonomic office chair with lumbar support', 899.99, 'OF-CHAIR-001', '2023-12-10'),
(111, 'Dining Chair Set', 'Set of 6 upholstered dining chairs', 1499.99, 'DR-CHAIR-001', '2023-12-11'),
(112, 'Glass Coffee Table', 'Modern glass-top coffee table with metal frame', 799.99, 'LR-TABLE-001', '2023-12-12'),
(113, 'Kids Bunk Bed', 'Twin over twin bunk bed with safety rails', 1899.99, 'KD-BED-001', '2023-12-13'),
(114, 'Queen Size Bed Frame', 'Platform bed with upholstered headboard', 2299.99, 'BR-BED-001', '2023-12-14'),
(115, 'Standing Desk', 'Electric height-adjustable standing desk', 1599.99, 'OF-DESK-002', '2023-12-15'),
(116, 'Luxury Recliner Sofa', 'Power reclining sofa with USB ports', 5999.99, 'LR-SOFA-004', '2023-12-16'),
(117, 'Marble Dining Table', '8-seater marble top dining table', 8499.99, 'DR-TABLE-002', '2023-12-17'),
(118, 'Dresser with Mirror', '6-drawer dresser with attached mirror', 1799.99, 'BR-DRESS-001', '2023-12-18'),
(119, 'Custom Entertainment Unit', 'Wall-mounted entertainment center', 3499.99, 'LR-ENT-001', '2023-12-19'),
(120, 'Conference Table', '12-seater conference room table', 4999.99, 'OF-TABLE-001', '2023-12-20'),
(121, 'Outdoor Lounger Set', 'Set of 2 poolside loungers with side table', 2499.99, 'OD-LOUNG-001', '2023-12-21'),
(122, 'Chest of Drawers', '5-drawer tall chest in walnut finish', 1299.99, 'BR-CHEST-001', '2023-12-22'),
(123, 'Kitchen Island', 'Mobile kitchen island with granite top', 2799.99, 'KT-ISLAND-001', '2023-12-23');

-- Create index for better performance
CREATE INDEX idx_products_sku ON public.products(sku);
CREATE INDEX idx_products_name ON public.products(product_name);
