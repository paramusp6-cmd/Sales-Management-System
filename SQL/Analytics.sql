
-- 1. view all sales

select * from customer_sales;

-- 2. view all branches

select * from branches;

-- 3. view all payments

select * from payment_splits;

-- 4. open sales

select * from customer_sales
where status = 'Open';

-- 5. closed sales

select * from customer_sales
where status = 'Close';

-- 6. total sales

select sum (gross_sales) as total_sales
from customer_sales;

-- 7. total received

select sum (received_amount) as total_received
from customer_sales;

-- 8. total pending

select sum (pending_amount) as total_pending
from customer_sales;



-- 9. branch wise sales

select b.branch_name,sum(c.gross_sales) as total_sales
from customer_sales c
join branches b
on c.branch_id = b.branch_id
group by b.branch_name;



-- 10. top performing branch

select top 1 b.branch_name, sum(c.gross_sales) as total_sales
from customer_sales c
join branches b
on c.branch_id = b.branch_id
group by b.branch_name
order by total_sales desc;




-- 11. payment method analysis

select payment_method,sum(amount_paid) as total_amount
from payment_splits
group by payment_method;



-- 12. daily sales trend

select sale_date,sum(gross_sales) as daily_sales
from customer_sales
group by sale_date
order by sale_date;



-- 13. customer pending report

select name,gross_sales,received_amount,pending_amount,
status from customer_sales
where pending_amount > 0;



-- 14. sales count branch wise

select b.branch_name,count(c.sale_id) as total_sales_count
from customer_sales c
join branches b
on c.branch_id = b.branch_id
group by b.branch_name;




-- 15. high value sales

select * from customer_sales
where gross_sales > 10000;


