
ALTER TABLE customer_sales
ADD pending_amount AS
(gross_sales - received_amount);


-- CHECK CONSTRAINT
-- Prevent negative payment entries

ALTER TABLE payment_splits
ADD CONSTRAINT chk_amount_paid
CHECK (amount_paid > 0);


-- CHECK CONSTRAINT
-- Prevent received_amount greater than gross_sales

ALTER TABLE customer_sales
ADD CONSTRAINT chk_received_amount
CHECK (received_amount <= gross_sales);


-- TRIGGER 1 : AFTER INSERT
-- Automatically updates received_amount and status

CREATE TRIGGER trg_after_insert_payment
ON payment_splits
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE cs
    SET
        cs.received_amount = ISNULL(ps.total_paid, 0),

        cs.status =
            CASE
                WHEN (cs.gross_sales - ISNULL(ps.total_paid, 0)) <= 0
                    THEN 'Close'
                ELSE 'Open'
            END

    FROM customer_sales cs

    INNER JOIN
    (
        SELECT
            sale_id,
            SUM(amount_paid) AS total_paid
        FROM payment_splits
        GROUP BY sale_id
    ) ps
        ON cs.sale_id = ps.sale_id

    INNER JOIN inserted i
        ON cs.sale_id = i.sale_id;

END;


-- TRIGGER 2 : AFTER UPDATE
-- Recalculates values when payment is modified

CREATE TRIGGER trg_after_update_payment
ON payment_splits
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE cs
    SET
        cs.received_amount = ISNULL(ps.total_paid, 0),

        cs.status =
            CASE
                WHEN (cs.gross_sales - ISNULL(ps.total_paid, 0)) <= 0
                    THEN 'Close'
                ELSE 'Open'
            END

    FROM customer_sales cs

    INNER JOIN
    (
        SELECT
            sale_id,
            SUM(amount_paid) AS total_paid
        FROM payment_splits
        GROUP BY sale_id
    ) ps
        ON cs.sale_id = ps.sale_id

    INNER JOIN inserted i
        ON cs.sale_id = i.sale_id;

END;

-- TRIGGER 3 : AFTER DELETE
-- Recalculates values when payment is deleted

CREATE TRIGGER trg_after_delete_payment
ON payment_splits
AFTER DELETE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE cs
    SET
        cs.received_amount = ISNULL(ps.total_paid, 0),

        cs.status =
            CASE
                WHEN (cs.gross_sales - ISNULL(ps.total_paid, 0)) <= 0
                    THEN 'Close'
                ELSE 'Open'
            END

    FROM customer_sales cs

    LEFT JOIN
    (
        SELECT
            sale_id,
            SUM(amount_paid) AS total_paid
        FROM payment_splits
        GROUP BY sale_id
    ) ps
        ON cs.sale_id = ps.sale_id

    INNER JOIN deleted d
        ON cs.sale_id = d.sale_id;

END;


-- TRIGGER 4: AUTO UPDATE PENDING AMOUNT & STATUS
-- Automatically recalculates pending amount
-- and updates customer payment status


CREATE TRIGGER trg_pending_amount
ON customer_sales
AFTER INSERT
AS
BEGIN

    SET NOCOUNT ON;

    UPDATE cs
    SET
        status =
            CASE
                WHEN (cs.gross_sales - cs.received_amount) <= 0
                THEN 'Close'
                ELSE 'Open'
            END

    FROM customer_sales cs
    INNER JOIN inserted i
        ON cs.sale_id = i.sale_id;

END;



