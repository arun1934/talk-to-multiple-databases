-- Create NPS feedback table
CREATE TABLE IF NOT EXISTS public.nps_feedback (
    feedback_id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    category VARCHAR(50),
    subcategory VARCHAR(50),
    region VARCHAR(50),
    carpenter_name VARCHAR(100),
    driver_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data (25 entries for various UAE regions)
INSERT INTO public.nps_feedback (product_id, rating, comment, category, subcategory, region, carpenter_name, driver_name, created_at) VALUES
(101, 5, 'Excellent delivery service, very professional team!', 'Furniture', 'Living Room', 'Dubai', 'Ahmed Al-Mansoori', 'Khalid Hassan', '2024-01-15 10:30:00'),
(102, 4, 'Good quality sofa, delivery was on time', 'Furniture', 'Living Room', 'Abu Dhabi', 'Mohammed Rashid', 'Omar Saeed', '2024-01-16 14:20:00'),
(103, 2, 'Dining table arrived with scratches, poor packaging', 'Furniture', 'Dining Room', 'Sharjah', 'Hassan Ali', 'Yousef Ibrahim', '2024-01-17 09:15:00'),
(104, 5, 'Perfect bedroom set installation, carpenter was very skilled', 'Furniture', 'Bedroom', 'Dubai', 'Saeed Khalifa', 'Ali Mohammed', '2024-01-18 16:45:00'),
(105, 3, 'Average service, delivery was delayed by 2 hours', 'Furniture', 'Office', 'Ajman', 'Ibrahim Ahmed', 'Rashid Ali', '2024-01-19 11:00:00'),
(106, 4, 'Great wardrobe, assembly was professional', 'Furniture', 'Bedroom', 'Fujairah', 'Khalifa Omar', 'Hassan Yousef', '2024-01-20 13:30:00'),
(107, 1, 'Very disappointed, wrong item delivered', 'Furniture', 'Kitchen', 'Ras Al Khaimah', 'Yousef Hassan', 'Mohammed Saeed', '2024-01-21 10:00:00'),
(108, 5, 'Outstanding service from start to finish', 'Furniture', 'Living Room', 'Dubai', 'Ali Rashid', 'Omar Hassan', '2024-01-22 15:20:00'),
(109, 4, 'Good quality outdoor furniture, satisfied with purchase', 'Furniture', 'Outdoor', 'Abu Dhabi', 'Mohammed Yousef', 'Khalid Ali', '2024-01-23 12:10:00'),
(110, 3, 'Delivery team was late but product is good', 'Furniture', 'Office', 'Sharjah', 'Ahmed Hassan', 'Saeed Ibrahim', '2024-01-24 17:30:00'),
(101, 5, 'Second purchase, consistently excellent service', 'Furniture', 'Living Room', 'Dubai', 'Rashid Mohammed', 'Ali Omar', '2024-01-25 09:45:00'),
(111, 2, 'Chair legs were uneven, needs replacement', 'Furniture', 'Dining Room', 'Umm Al Quwain', 'Omar Khalifa', 'Hassan Mohammed', '2024-01-26 14:00:00'),
(112, 4, 'Beautiful coffee table, careful handling during delivery', 'Furniture', 'Living Room', 'Dubai', 'Saeed Hassan', 'Yousef Ali', '2024-01-27 11:30:00'),
(113, 5, 'Perfect kids furniture, very safe and sturdy', 'Furniture', 'Kids Room', 'Abu Dhabi', 'Ibrahim Khalid', 'Mohammed Omar', '2024-01-28 10:15:00'),
(114, 3, 'Decent quality but assembly instructions unclear', 'Furniture', 'Bedroom', 'Al Ain', 'Hassan Saeed', 'Rashid Yousef', '2024-01-29 16:00:00'),
(115, 4, 'Great customer service, resolved issues quickly', 'Furniture', 'Office', 'Dubai', 'Ali Ibrahim', 'Khalid Hassan', '2024-01-30 13:45:00'),
(116, 5, 'Luxury furniture worth every dirham', 'Furniture', 'Living Room', 'Dubai Marina', 'Mohammed Ali', 'Omar Saeed', '2024-01-31 15:30:00'),
(117, 2, 'Delivery damage, waiting for replacement', 'Furniture', 'Dining Room', 'Sharjah', 'Yousef Rashid', 'Hassan Ali', '2024-02-01 09:00:00'),
(118, 4, 'Good value for money, sturdy construction', 'Furniture', 'Bedroom', 'Abu Dhabi', 'Khalifa Hassan', 'Ibrahim Mohammed', '2024-02-02 14:20:00'),
(119, 5, 'Exceptional craftsmanship on custom piece', 'Furniture', 'Living Room', 'Dubai', 'Saeed Omar', 'Ali Yousef', '2024-02-03 11:00:00'),
(120, 3, 'Average quality, expected better for the price', 'Furniture', 'Office', 'Ajman', 'Rashid Ali', 'Mohammed Hassan', '2024-02-04 16:30:00'),
(105, 4, 'Much better experience this time, thank you', 'Furniture', 'Office', 'Dubai', 'Ahmed Ibrahim', 'Khalid Omar', '2024-02-05 10:45:00'),
(121, 5, 'Premium quality outdoor set, weatherproof', 'Furniture', 'Outdoor', 'Palm Jumeirah', 'Omar Mohammed', 'Yousef Hassan', '2024-02-06 13:15:00'),
(122, 1, 'Complete disaster, wrong color and size', 'Furniture', 'Bedroom', 'Sharjah', 'Hassan Khalid', 'Ali Rashid', '2024-02-07 09:30:00'),
(123, 4, 'Satisfied with the modular kitchen units', 'Furniture', 'Kitchen', 'Dubai', 'Ibrahim Ali', 'Saeed Mohammed', '2024-02-08 15:00:00');

-- Create index for better query performance
CREATE INDEX idx_nps_product_id ON public.nps_feedback(product_id);
CREATE INDEX idx_nps_region ON public.nps_feedback(region);
CREATE INDEX idx_nps_rating ON public.nps_feedback(rating);
CREATE INDEX idx_nps_created_at ON public.nps_feedback(created_at);
