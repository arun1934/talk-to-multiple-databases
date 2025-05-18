CREATE TABLE nps_db.public. HYB_PRODUCT_DATA (
    P_LOCATION VARCHAR(30), -- Location of the product
    BASE_PRODUCT VARCHAR(255), -- Base product identifier
    COLOR_VARIANT VARCHAR(255), -- Color variant of the product
    SIZE_VARIANT VARCHAR(255), -- Size variant of the product
    STYLE_NUMBER VARCHAR(255), -- Style number assigned
    SKU_ID VARCHAR(255), -- Stock Keeping Unit identifier
    PRODUCT_NAME TEXT, -- Name of the product
    COLOR VARCHAR(255), -- Color of the product
    SIZE VARCHAR(255), -- Size of the product
    BRAND VARCHAR(255), -- Brand of the product
    CATEGORY1 VARCHAR(255), -- First category of the product
    CATEGORY2 VARCHAR(255), -- Second category of the product
    CATEGORY3 VARCHAR(255), -- Third category of the product
    CONCEPT VARCHAR(255), -- Concept associated with the product
    ORIGINAL_CONCEPT VARCHAR(255), -- Original concept of the product
    TIER VARCHAR(255), -- Tier level of the product
    BADGE TEXT, -- Badge information or promotional tags
    PRICE_PER_UNIT VARCHAR(255), -- Price per unit
    PRICE_START_TIME VARCHAR(255), -- Price start time
    PRICE_END_TIME VARCHAR(255), -- Price end time
    UPLOADED_DATE TIMESTAMP, -- Date when the product was uploaded
    MODIFIED_DATE TIMESTAMP, -- Date when the product data was last modified
    PRODUCT_STATUS VARCHAR(255), -- Current status of the product
    COLOR_VARIANT_STATUS VARCHAR(255), -- Status of the color variant
    SIZE_VARIANT_STATUS VARCHAR(255), -- Status of the size variant
    AVAILABLE_STOCK VARCHAR(255), -- Available stock quantity
    GENDER VARCHAR(255), -- Gender association of the product
    CATEGORY4 VARCHAR(255), -- Fourth category of the product
    CATEGORY5 VARCHAR(255), -- Fifth category of the product
    PROMOTION_TYPE VARCHAR(255), -- Type of promotion
    PROMOTION_PRICE VARCHAR(255), -- Promotion price
    CONCEPT_CLASS VARCHAR(255), -- Class of the concept
    PROMOTION_START_DATE VARCHAR(255), -- Starting date of the promotion
    PROMOTION_END_DATE VARCHAR(255), -- Ending date of the promotion
    CONCEPT_GROUP VARCHAR(255), -- Group for the concept
    CONCEPT_DEPARTMENT VARCHAR(255), -- Department for the concept
    CONCEPT_SUB_CLASS VARCHAR(255), -- Subclass of the concept
    SEASON VARCHAR(255), -- Season related to the product
    EAN VARCHAR(255), -- European Article Number
    SUPERCATEGORY2 VARCHAR(255), -- Super category 2
    SUPERCATEGORY3 VARCHAR(255), -- Super category 3
    SUPERCATEGORY4 VARCHAR(255), -- Super category 4
    SUPERCATEGORY5 VARCHAR(255), -- Super category 5
    SUPERCATEGORY6 VARCHAR(255), -- Super category 6
    TAG TEXT, -- Tags associated with the product
    DISCONTINUED VARCHAR(10), -- Indicator if the product is discontinued
    DISCONTINUED_DATE TIMESTAMP, -- Date when the product was discontinued
    DISCONTINUED_REASON VARCHAR(255), -- Reason for discontinuation
    STYLE VARCHAR(255), -- Style description
    ROOM_TYPE VARCHAR(255), -- Room type related to the product
    ITEM_STATUS VARCHAR(255), -- Status of the item
    EVENT VARCHAR(255), -- Event related to the product
    COO VARCHAR(255), -- Country of origin
    UNIT_PACK_LENGTH VARCHAR(255), -- Length of the packing unit
    UNIT_PACK_WIDTH VARCHAR(255), -- Width of the packing unit
    UNIT_PACK_HEIGHT VARCHAR(255), -- Height of the packing unit
    UNIT_PACK_TYPE VARCHAR(255), -- Type of packing unit
    UNIT_PACK_WEIGHT VARCHAR(255), -- Weight of the packing unit
    VPN VARCHAR(255), -- Vendor product number
    RANKING VARCHAR(255), -- Ranking of the product
    CV VARCHAR(255), -- Country version
    BASE_PRICE_PER_UNIT NUMERIC(22, 4), -- Base price per unit with 4 decimal precision
    COLOR_VARIANT_PRICE_PER_UNIT NUMERIC(22, 4), -- Price per unit for color variant
    SIZE_VARIANT_PRICE_PER_UNIT NUMERIC(22, 4), -- Price per unit for size variant
    MODEL_NAME VARCHAR(255), -- Model name of the product
    CONCEPT_DELIVERY INTEGER, -- Concept delivery identifier
    CMMT_DTTM TIMESTAMP, -- Timestamp for comments
    JOB_ID INTEGER -- Job identifier
);


COMMENT ON COLUMN HYB_PRODUCT_DATA.P_LOCATION IS 'Location of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.BASE_PRODUCT IS 'Base product identifier';
COMMENT ON COLUMN HYB_PRODUCT_DATA.COLOR_VARIANT IS 'Color variant of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.SIZE_VARIANT IS 'Size variant of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.STYLE_NUMBER IS 'Style number assigned';
COMMENT ON COLUMN HYB_PRODUCT_DATA.SKU_ID IS 'Stock Keeping Unit identifier';
COMMENT ON COLUMN HYB_PRODUCT_DATA.PRODUCT_NAME IS 'Name of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.COLOR IS 'Color of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.SIZE IS 'Size of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.BRAND IS 'Brand of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.CATEGORY1 IS 'First category of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.CATEGORY2 IS 'Second category of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.CATEGORY3 IS 'Third category of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.CONCEPT IS 'Concept associated with the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.ORIGINAL_CONCEPT IS 'Original concept of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.TIER IS 'Tier level of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.BADGE IS 'Badge information or promotional tags';
COMMENT ON COLUMN HYB_PRODUCT_DATA.PRICE_PER_UNIT IS 'Price per unit';
COMMENT ON COLUMN HYB_PRODUCT_DATA.PRICE_START_TIME IS 'Price start time';
COMMENT ON COLUMN HYB_PRODUCT_DATA.PRICE_END_TIME IS 'Price end time';
COMMENT ON COLUMN HYB_PRODUCT_DATA.UPLOADED_DATE IS 'Date when the product was uploaded';
COMMENT ON COLUMN HYB_PRODUCT_DATA.MODIFIED_DATE IS 'Date when the product data was last modified';
COMMENT ON COLUMN HYB_PRODUCT_DATA.PRODUCT_STATUS IS 'Current status of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.COLOR_VARIANT_STATUS IS 'Status of the color variant';
COMMENT ON COLUMN HYB_PRODUCT_DATA.SIZE_VARIANT_STATUS IS 'Status of the size variant';
COMMENT ON COLUMN HYB_PRODUCT_DATA.AVAILABLE_STOCK IS 'Available stock quantity';
COMMENT ON COLUMN HYB_PRODUCT_DATA.GENDER IS 'Gender association of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.CATEGORY4 IS 'Fourth category of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.CATEGORY5 IS 'Fifth category of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.PROMOTION_TYPE IS 'Type of promotion';
COMMENT ON COLUMN HYB_PRODUCT_DATA.PROMOTION_PRICE IS 'Promotion price';
COMMENT ON COLUMN HYB_PRODUCT_DATA.CONCEPT_CLASS IS 'Class of the concept';
COMMENT ON COLUMN HYB_PRODUCT_DATA.PROMOTION_START_DATE IS 'Starting date of the promotion';
COMMENT ON COLUMN HYB_PRODUCT_DATA.PROMOTION_END_DATE IS 'Ending date of the promotion';
COMMENT ON COLUMN HYB_PRODUCT_DATA.CONCEPT_GROUP IS 'Group for the concept';
COMMENT ON COLUMN HYB_PRODUCT_DATA.CONCEPT_DEPARTMENT IS 'Department for the concept';
COMMENT ON COLUMN HYB_PRODUCT_DATA.CONCEPT_SUB_CLASS IS 'Subclass of the concept';
COMMENT ON COLUMN HYB_PRODUCT_DATA.SEASON IS 'Season related to the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.EAN IS 'European Article Number';
COMMENT ON COLUMN HYB_PRODUCT_DATA.SUPERCATEGORY2 IS 'Super category 2';
COMMENT ON COLUMN HYB_PRODUCT_DATA.SUPERCATEGORY3 IS 'Super category 3';
COMMENT ON COLUMN HYB_PRODUCT_DATA.SUPERCATEGORY4 IS 'Super category 4';
COMMENT ON COLUMN HYB_PRODUCT_DATA.SUPERCATEGORY5 IS 'Super category 5';
COMMENT ON COLUMN HYB_PRODUCT_DATA.SUPERCATEGORY6 IS 'Super category 6';
COMMENT ON COLUMN HYB_PRODUCT_DATA.TAG IS 'Tags associated with the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.DISCONTINUED IS 'Indicator if the product is discontinued';
COMMENT ON COLUMN HYB_PRODUCT_DATA.DISCONTINUED_DATE IS 'Date when the product was discontinued';
COMMENT ON COLUMN HYB_PRODUCT_DATA.DISCONTINUED_REASON IS 'Reason for discontinuation';
COMMENT ON COLUMN HYB_PRODUCT_DATA.STYLE IS 'Style description';
COMMENT ON COLUMN HYB_PRODUCT_DATA.ROOM_TYPE IS 'Room type related to the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.ITEM_STATUS IS 'Status of the item';
COMMENT ON COLUMN HYB_PRODUCT_DATA.EVENT IS 'Event related to the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.COO IS 'Country of origin';
COMMENT ON COLUMN HYB_PRODUCT_DATA.UNIT_PACK_LENGTH IS 'Length of the packing unit';
COMMENT ON COLUMN HYB_PRODUCT_DATA.UNIT_PACK_WIDTH IS 'Width of the packing unit';
COMMENT ON COLUMN HYB_PRODUCT_DATA.UNIT_PACK_HEIGHT IS 'Height of the packing unit';
COMMENT ON COLUMN HYB_PRODUCT_DATA.UNIT_PACK_TYPE IS 'Type of packing unit';
COMMENT ON COLUMN HYB_PRODUCT_DATA.UNIT_PACK_WEIGHT IS 'Weight of the packing unit';
COMMENT ON COLUMN HYB_PRODUCT_DATA.VPN IS 'Vendor product number';
COMMENT ON COLUMN HYB_PRODUCT_DATA.RANKING IS 'Ranking of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.CV IS 'Country version';
COMMENT ON COLUMN HYB_PRODUCT_DATA.BASE_PRICE_PER_UNIT IS 'Base price per unit with 4 decimal precision';
COMMENT ON COLUMN HYB_PRODUCT_DATA.COLOR_VARIANT_PRICE_PER_UNIT IS 'Price per unit for color variant';
COMMENT ON COLUMN HYB_PRODUCT_DATA.SIZE_VARIANT_PRICE_PER_UNIT IS 'Price per unit for size variant';
COMMENT ON COLUMN HYB_PRODUCT_DATA.MODEL_NAME IS 'Model name of the product';
COMMENT ON COLUMN HYB_PRODUCT_DATA.CONCEPT_DELIVERY IS 'Concept delivery identifier';
COMMENT ON COLUMN HYB_PRODUCT_DATA.CMMT_DTTM IS 'Timestamp for comments';
COMMENT ON COLUMN HYB_PRODUCT_DATA.JOB_ID IS 'Job identifier';