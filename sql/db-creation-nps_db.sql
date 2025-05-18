CREATE TABLE nps_db.public.HYB_NPS_DTL (
    NPS_DATE DATE,
    ORDER_DATE DATE,
    PK VARCHAR(100),
    P_ORDERNO VARCHAR(100),
    P_SITEID VARCHAR(13),
    P_ORDERSOURCE VARCHAR(9),
    P_EMAILID VARCHAR(48),
    P_COMMENT TEXT, -- Feedback or comment from the user
    P_NAME VARCHAR(1500), -- Name of the user providing feedback
    P_MOBILENUMBER VARCHAR(44), -- Mobile number of the user
    P_CATEGORY VARCHAR(100), -- Category of the order
    P_SUBCATEGORY VARCHAR(100), -- Subcategory of the order
    P_RATING VARCHAR(8), -- Rating given by the user
    NPS_TYPE VARCHAR(13), -- Type of Net Promoter Score
    CODE VARCHAR(14), -- Code associated with the feedback
    FEEDBACK_ID VARCHAR(50), -- Unique identifier for the feedback
    CMMT_DTTM TIMESTAMP, -- Date and time of the comment
    JOB_ID BIGINT -- Job identifier
);

COMMENT ON COLUMN HYB_NPS_DTL.NPS_DATE IS 'Date of the NPS entry';
COMMENT ON COLUMN HYB_NPS_DTL.ORDER_DATE IS 'Date of the order';
COMMENT ON COLUMN HYB_NPS_DTL.PK IS 'Primary Key';
COMMENT ON COLUMN HYB_NPS_DTL.P_ORDERNO IS 'Order number';
COMMENT ON COLUMN HYB_NPS_DTL.P_SITEID IS 'Site ID where the order was made';
COMMENT ON COLUMN HYB_NPS_DTL.P_ORDERSOURCE IS 'Source from where the order was placed';
COMMENT ON COLUMN HYB_NPS_DTL.P_EMAILID IS 'Email ID of the user';
COMMENT ON COLUMN HYB_NPS_DTL.P_COMMENT IS 'Feedback or comment from the user';
COMMENT ON COLUMN HYB_NPS_DTL.P_NAME IS 'Name of the user providing feedback';
COMMENT ON COLUMN HYB_NPS_DTL.P_MOBILENUMBER IS 'Mobile number of the user';
COMMENT ON COLUMN HYB_NPS_DTL.P_CATEGORY IS 'Category of the order';
COMMENT ON COLUMN HYB_NPS_DTL.P_SUBCATEGORY IS 'Subcategory of the order';
COMMENT ON COLUMN HYB_NPS_DTL.P_RATING IS 'Rating given by the user';
COMMENT ON COLUMN HYB_NPS_DTL.NPS_TYPE IS 'Type of Net Promoter Score';
COMMENT ON COLUMN HYB_NPS_DTL.CODE IS 'Code associated with the feedback';
COMMENT ON COLUMN HYB_NPS_DTL.FEEDBACK_ID IS 'Unique identifier for the feedback';
COMMENT ON COLUMN HYB_NPS_DTL.CMMT_DTTM IS 'Date and time of the comment';
COMMENT ON COLUMN HYB_NPS_DTL.JOB_ID IS 'Job identifier';

CREATE TABLE nps_db.public.HYB_ORDER_DETAIL (
    P_DATE VARCHAR(25), -- Order date
    P_ORDERNO VARCHAR(100), -- Order number
    P_LANGUAGE VARCHAR(25), -- Language of the order
    P_DATE2 VARCHAR(100), -- Additional date field
    P_TIME VARCHAR(100), -- Time of the order
    P_LOCATION VARCHAR(100), -- Location of the order
    P_REGISTEREDUSER VARCHAR(100), -- Registered user identifier
    P_CUSTOMERPK VARCHAR(100), -- Primary key for customer
    P_SALETYPE VARCHAR(100), -- Type of sale
    P_ORDERSTATUS VARCHAR(100), -- Status of the order
    P_ORDERSTATUSDISPLAY VARCHAR(100), -- Display status of the order
    P_STATUS BYTEA, -- Binary status data
    P_STATUSDISPLAY BYTEA, -- Binary display status data
    P_PAYMENTMODE VARCHAR(100), -- Mode of payment
    P_ORDERCONFIRMATIONTIME TIMESTAMP, -- Confirmation time of the order
    P_MODIFICATIONDATE TIMESTAMP, -- Date of last modification
    P_PAYMENTTYPEID VARCHAR(100), -- Payment type identifier
    P_DELIVERYCOST NUMERIC(22, 2), -- Cost of delivery
    P_WALLETREDEEMEDAMOUNT NUMERIC(22, 2), -- Amount redeemed from wallet
    P_PRODUCTCODE VARCHAR(100), -- Code of the product
    P_CONCEPTCODE VARCHAR(100), -- Code for concept
    P_STYLENO VARCHAR(100), -- Style number of the product
    P_VPN VARCHAR(100), -- Vendor product number
    P_CV VARCHAR(100), -- Country of origin code
    P_SEASON VARCHAR(100), -- Season of the product
    P_CONCEPTGROUP VARCHAR(100), -- Group associated with concept
    P_CONCEPTCLASS VARCHAR(100), -- Class of the concept
    P_CONCEPTSUBCLASS VARCHAR(100), -- Subclass of the concept
    P_CONCEPTDEPARTMENT VARCHAR(100), -- Department for the concept
    P_COLORVARIANTCODE VARCHAR(100), -- Color variant code
    P_QUANTITY NUMERIC(22, 2), -- Quantity ordered
    P_PRODUCTAMOUNT NUMERIC(22, 2), -- Amount for the product
    P_DISCOUNTAMOUNT NUMERIC(22, 2), -- Amount of discount
    P_NETAMOUNT NUMERIC(22, 2), -- Net amount after discounts
    P_PROMOTIONCODE VARCHAR(100), -- Code for the promotion
    P_PROMOTIONSTARTDATE TIMESTAMP, -- Start date of the promotion
    P_PROMOTIONENDDATE TIMESTAMP, -- End date of the promotion
    P_RETURNREQUESTCODE VARCHAR(100), -- Code for return request
    P_REASONCODE VARCHAR(100), -- Reason code for return
    P_RETURNSTATUS VARCHAR(100), -- Status of the return
    P_NOTES TEXT, -- Notes regarding the order
    P_REQUESTNO VARCHAR(100), -- Request number for order
    PGREFUNDAMOUNT NUMERIC(22, 2), -- Refund amount for PG
    REFUNDVOUCHERAMOUNT NUMERIC(22, 2), -- Voucher refund amount
    CODNONREFUNDAMOUNT NUMERIC(22, 2), -- Non-refundable COD amount
    CASHREFUNDAMOUNT NUMERIC(22, 2), -- Cash refund amount
    P_CITYCODE VARCHAR(100), -- Code for city
    P_CITYSHORTCODE VARCHAR(100), -- Shortcode for city
    P_AREANAME TEXT, -- Name of the area
    P_CITYPK VARCHAR(100), -- Primary key for city
    P_EPO_NUMBER VARCHAR(100), -- EPO number
    P_VENDOR VARCHAR(100), -- Vendor associated with the order
    P_ITEM_TYPE_FLAG VARCHAR(100), -- Type flag for the item
    P_STORE_CODE VARCHAR(100), -- Store code for order
    P_LOYALTY_POINTS_REDEEMED NUMERIC(22, 2), -- Loyalty points redeemed
    P_LOYALTY_REDEEMED_AMOUNT NUMERIC(22, 2), -- Loyalty amount redeemed
    P_LOYALTY_RETURNED_POINTS NUMERIC(22, 2), -- Points returned to user
    P_ORDER_THRESHOLD_VOUCHER_AMOUNT NUMERIC(22, 2), -- Threshold voucher amount
    P_SOURCE_SITE VARCHAR(100), -- Source site for the order
    P_DELIVERY_TYPE VARCHAR(100), -- Type of delivery
    P_RETURN_STORE_CODE VARCHAR(100), -- Store code for return
    P_REFUND_MODE VARCHAR(100), -- Mode of refund
    P_NPS VARCHAR(100), -- Net Promoter Score associated with the order
    P_ORDER_SOURCE VARCHAR(100), -- Source of the order
    P_RETURN_SOURCE VARCHAR(100), -- Source of return
    P_DELIVERY_PARTNER VARCHAR(100), -- Delivery partner for the order
    P_ORDER_TYPE VARCHAR(100), -- Type of order
    P_SHIPPING_CHARGES NUMERIC(22, 2), -- Charges for shipping
    P_CHOSEN_DELIVERY_DATE VARCHAR(100), -- Chosen delivery date
    P_NETAMOUNTUSD NUMERIC(22, 2), -- Net amount in USD
    P_SHUKRAN_ID VARCHAR(100), -- Shukran ID for reward program
    P_PROMO_VOUCHER_CODE VARCHAR(400), -- Promotion voucher code
    P_PROMO_VOUCHER_TYPE VARCHAR(100), -- Type of promotion voucher
    P_PROMO_APPLIED_DISCOUNT NUMERIC(22, 2), -- Discount applied from promo
    P_PROMO_VOUCHER_AMOUNT NUMERIC(22, 2), -- Amount from promo voucher
    P_GIFTCARD_REDEEMED_AMOUNT NUMERIC(22, 2), -- Gift card redeemed amount
    P_CARD_PROMO_AMOUNT NUMERIC(22, 2), -- Promo amount from card
    P_SITE_ADDED VARCHAR(100), -- Site where the order was added
    P_CANCEL_REASON VARCHAR(100), -- Reason for cancellation
    P_CANCELLATION_SOURCE VARCHAR(100), -- Source of cancellation
    P_ORDER_ENTRY_GIFTCARD_DISCOUNT NUMERIC(22, 2), -- Gift card discount on entry
    AWB_NUMBER VARCHAR(150), -- AWB number for tracking
    GROSSREFUNDAMOUNT NUMERIC(22, 2), -- Total gross refund amount
    ECOMDISCOUNTAMOUNT NUMERIC(22, 2), -- E-commerce discount amount
    CONCEPTDISCOUNTAMOUNT NUMERIC(22, 2), -- Discount amount for concept
    P_KEY VARCHAR(400), -- Unique key for order details
    DELIVERY_ESTIMATE_DATE TIMESTAMP, -- Estimated delivery date
    KIOSKVOUCHER VARCHAR(150), -- Kiosk voucher code
    CMMT_DTTM TIMESTAMP, -- Timestamp for comments
    JOB_ID BIGINT -- Job identifier
);

COMMENT ON COLUMN HYB_ORDER_DETAIL.P_DATE IS 'Order date';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_ORDERNO IS 'Order number';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_LANGUAGE IS 'Language of the order';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_DATE2 IS 'Additional date field';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_TIME IS 'Time of the order';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_LOCATION IS 'Location of the order';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_REGISTEREDUSER IS 'Registered user identifier';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_CUSTOMERPK IS 'Primary key for customer';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_SALETYPE IS 'Type of sale';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_ORDERSTATUS IS 'Status of the order';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_ORDERSTATUSDISPLAY IS 'Display status of the order';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_STATUS IS 'Binary status data';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_STATUSDISPLAY IS 'Binary display status data';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_PAYMENTMODE IS 'Mode of payment';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_ORDERCONFIRMATIONTIME IS 'Confirmation time of the order';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_MODIFICATIONDATE IS 'Date of last modification';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_PAYMENTTYPEID IS 'Payment type identifier';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_DELIVERYCOST IS 'Cost of delivery';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_WALLETREDEEMEDAMOUNT IS 'Amount redeemed from wallet';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_PRODUCTCODE IS 'Code of the product';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_CONCEPTCODE IS 'Code for concept';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_STYLENO IS 'Style number of the product';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_VPN IS 'Vendor product number';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_CV IS 'Country of origin code';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_SEASON IS 'Season of the product';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_CONCEPTGROUP IS 'Group associated with concept';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_CONCEPTCLASS IS 'Class of the concept';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_CONCEPTSUBCLASS IS 'Subclass of the concept';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_CONCEPTDEPARTMENT IS 'Department for the concept';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_COLORVARIANTCODE IS 'Color variant code';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_QUANTITY IS 'Quantity ordered';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_PRODUCTAMOUNT IS 'Amount for the product';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_DISCOUNTAMOUNT IS 'Amount of discount';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_NETAMOUNT IS 'Net amount after discounts';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_PROMOTIONCODE IS 'Code for the promotion';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_PROMOTIONSTARTDATE IS 'Start date of the promotion';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_PROMOTIONENDDATE IS 'End date of the promotion';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_RETURNREQUESTCODE IS 'Code for return request';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_REASONCODE IS 'Reason code for return';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_RETURNSTATUS IS 'Status of the return';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_NOTES IS 'Notes regarding the order';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_REQUESTNO IS 'Request number for order';
COMMENT ON COLUMN HYB_ORDER_DETAIL.PGREFUNDAMOUNT IS 'Refund amount for PG';
COMMENT ON COLUMN HYB_ORDER_DETAIL.REFUNDVOUCHERAMOUNT IS 'Voucher refund amount';
COMMENT ON COLUMN HYB_ORDER_DETAIL.CODNONREFUNDAMOUNT IS 'Non-refundable COD amount';
COMMENT ON COLUMN HYB_ORDER_DETAIL.CASHREFUNDAMOUNT IS 'Cash refund amount';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_CITYCODE IS 'Code for city';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_CITYSHORTCODE IS 'Shortcode for city';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_AREANAME IS 'Name of the area';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_CITYPK IS 'Primary key for city';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_EPO_NUMBER IS 'EPO number';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_VENDOR IS 'Vendor associated with the order';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_ITEM_TYPE_FLAG IS 'Type flag for the item';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_STORE_CODE IS 'Store code for order';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_LOYALTY_POINTS_REDEEMED IS 'Loyalty points redeemed';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_LOYALTY_REDEEMED_AMOUNT IS 'Loyalty amount redeemed';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_LOYALTY_RETURNED_POINTS IS 'Points returned to user';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_ORDER_THRESHOLD_VOUCHER_AMOUNT IS 'Threshold voucher amount';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_SOURCE_SITE IS 'Source site for the order';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_DELIVERY_TYPE IS 'Type of delivery';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_RETURN_STORE_CODE IS 'Store code for return';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_REFUND_MODE IS 'Mode of refund';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_NPS IS 'Net Promoter Score associated with the order';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_ORDER_SOURCE IS 'Source of the order';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_RETURN_SOURCE IS 'Source of return';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_DELIVERY_PARTNER IS 'Delivery partner for the order';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_ORDER_TYPE IS 'Type of order';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_SHIPPING_CHARGES IS 'Charges for shipping';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_CHOSEN_DELIVERY_DATE IS 'Chosen delivery date';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_NETAMOUNTUSD IS 'Net amount in USD';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_SHUKRAN_ID IS 'Shukran ID for reward program';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_PROMO_VOUCHER_CODE IS 'Promotion voucher code';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_PROMO_VOUCHER_TYPE IS 'Type of promotion voucher';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_PROMO_APPLIED_DISCOUNT IS 'Discount applied from promo';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_PROMO_VOUCHER_AMOUNT IS 'Amount from promo voucher';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_GIFTCARD_REDEEMED_AMOUNT IS 'Gift card redeemed amount';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_CARD_PROMO_AMOUNT IS 'Promo amount from card';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_SITE_ADDED IS 'Site where the order was added';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_CANCEL_REASON IS 'Reason for cancellation';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_CANCELLATION_SOURCE IS 'Source of cancellation';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_ORDER_ENTRY_GIFTCARD_DISCOUNT IS 'Gift card discount on entry';
COMMENT ON COLUMN HYB_ORDER_DETAIL.AWB_NUMBER IS 'AWB number for tracking';
COMMENT ON COLUMN HYB_ORDER_DETAIL.GROSSREFUNDAMOUNT IS 'Total gross refund amount';
COMMENT ON COLUMN HYB_ORDER_DETAIL.ECOMDISCOUNTAMOUNT IS 'E-commerce discount amount';
COMMENT ON COLUMN HYB_ORDER_DETAIL.CONCEPTDISCOUNTAMOUNT IS 'Discount amount for concept';
COMMENT ON COLUMN HYB_ORDER_DETAIL.P_KEY IS 'Unique key for order details';
COMMENT ON COLUMN HYB_ORDER_DETAIL.DELIVERY_ESTIMATE_DATE IS 'Estimated delivery date';
COMMENT ON COLUMN HYB_ORDER_DETAIL.KIOSKVOUCHER IS 'Kiosk voucher code';
COMMENT ON COLUMN HYB_ORDER_DETAIL.CMMT_DTTM IS 'Timestamp for comments';
COMMENT ON COLUMN HYB_ORDER_DETAIL.JOB_ID IS 'Job identifier';

CREATE TABLE IF NOT EXISTS nps_db.public.dm_empmast
(
    concept_code character varying(100) COLLATE pg_catalog."default",
    country_code character varying(100) COLLATE pg_catalog."default",
    terr_id character varying(6) COLLATE pg_catalog."default",
    emp_no character varying(20) COLLATE pg_catalog."default",
    emp_idcardname character varying(75) COLLATE pg_catalog."default",
    emp_desig character varying(20) COLLATE pg_catalog."default",
    emp_grade character varying(3) COLLATE pg_catalog."default",
    emp_location character varying(25) COLLATE pg_catalog."default",
    emp_mobileno character varying(10) COLLATE pg_catalog."default",
    basic_salary bigint,
    total_salary bigint,
    emp_skill bigint,
    emp_remarks character varying(50) COLLATE pg_catalog."default",
    stage_bin_num character varying(20) COLLATE pg_catalog."default",
    emp_type character varying(1) COLLATE pg_catalog."default",
    emp_isonvacation character varying(2) COLLATE pg_catalog."default" DEFAULT '0'::character varying,
    emp_designedto character varying(100) COLLATE pg_catalog."default",
    emp_supervisor character varying(20) COLLATE pg_catalog."default",
    emp_ctd_flg bigint DEFAULT 0,
    status character varying(1) COLLATE pg_catalog."default" DEFAULT '1'::character varying,
    created_on timestamp without time zone,
    created_by character varying(20) COLLATE pg_catalog."default",
    last_updated_on timestamp without time zone,
    last_updated_by character varying(20) COLLATE pg_catalog."default",
    employee_organization character varying(20) COLLATE pg_catalog."default",
    religion character varying(20) COLLATE pg_catalog."default",
    start_time character varying(8) COLLATE pg_catalog."default",
    end_time character varying(100) COLLATE pg_catalog."default",
    nationality character varying(50) COLLATE pg_catalog."default",
    emp_track_flg character varying(10) COLLATE pg_catalog."default",
    op_type character varying(10) COLLATE pg_catalog."default",
    cmmt_dttm timestamp without time zone,
    src_cmmt_dttm character varying(100) COLLATE pg_catalog."default",
    dbuser character varying(50) COLLATE pg_catalog."default"
)


