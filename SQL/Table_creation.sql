create database Sales_Management_System;

use Sales_Management_System;

CREATE TABLE branches (
    branch_id INT PRIMARY KEY,
    branch_name VARCHAR(100) NOT NULL,
    branch_admin_name VARCHAR(100)
    );

select * from branches;

    CREATE TABLE users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    branch_id INT,
    role VARCHAR(20)
    CHECK (role IN ('Super Admin', 'Admin')),
    FOREIGN KEY (branch_id) 
        REFERENCES branches(branch_id)
);

select * from users;

CREATE TABLE customer_sales (
    sale_id INT IDENTITY(1,1) PRIMARY KEY,
    branch_id INT NOT NULL,
    sale_date DATE NOT NULL,
    name VARCHAR(100),
    mobile_number VARCHAR(15),
    product_name VARCHAR(30),
    gross_sales DECIMAL(12,2) NOT NULL,
    received_amount DECIMAL(12,2) DEFAULT 0,
    pending_amount AS (gross_sales - received_amount) PERSISTED,
    status VARCHAR(10) DEFAULT 'Open'CHECK (status IN ('Open','Close')),
    FOREIGN KEY (branch_id) 
        REFERENCES branches(branch_id)
);

select * from customer_sales;

CREATE TABLE payment_splits (
    payment_id INT IDENTITY(1,1) PRIMARY KEY,
    sale_id INT NOT NULL,
    payment_date DATE NOT NULL,
    amount_paid DECIMAL(12,2) CHECK (amount_paid > 0),
    payment_method VARCHAR(20) NOT NULL
        CHECK (payment_method IN ('Cash','UPI','Card')),
        FOREIGN KEY (sale_id)
        REFERENCES customer_sales(sale_id)
);

select * from payment_splits;




