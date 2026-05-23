import streamlit as st
import pyodbc
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Sales Management System", layout="centered")


if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None

def get_connection():
    conn = pyodbc.connect(
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=DESKTOP-NOVH4NN\\SQLEXPRESS;"
        "Database=Sales_Management_System;"
        "Trusted_Connection=yes;"
    )
    return conn

def login_user(username, password):
    conn = get_connection()
    query = """
    SELECT u.user_id, u.username, u.role, u.branch_id, b.branch_name FROM users u
    LEFT JOIN branches b ON u.branch_id = b.branch_id
    WHERE u.username =? AND u.password =?
    """
    df = pd.read_sql(query, conn,params=(username, password))
    conn.close()
    if not df.empty:
        return df.iloc[0].to_dict()
    return None

def get_sales_data(branch_id=None):
    conn = get_connection()
    if branch_id:
        query = """
            SELECT cs.*, b.branch_name FROM customer_sales cs JOIN branches b ON cs.branch_id = b.branch_id
            WHERE cs.branch_id =?
            ORDER BY cs.sale_id DESC
        """
        df = pd.read_sql(query, conn, params=(branch_id,))
    else:
        query = """
            SELECT cs.*, b.branch_name FROM customer_sales cs JOIN branches b ON cs.branch_id = b.branch_id
            ORDER BY cs.sale_id DESC
        """
        df = pd.read_sql(query, conn)
    conn.close()
    df.rename(columns={'sale_date': 'date'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    return df

def get_branches():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM branches", conn)
    conn.close()
    return df 

def add_sale(data):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ISNULL(MAX(sale_id),0) + 1 FROM customer_sales"
        )
        next_sale_id = cursor.fetchone()[0]
        query = """
        INSERT INTO customer_sales 
        (
            sale_id,
            branch_id, 
            [date], 
            name, 
            mobile_number, 
            product_name, 
            gross_sales, 
            received_amount, 
            status
        )
        VALUES (?,?,?,?,?,?,?,?)
        """
        values = (
            next_sale_id,
            *data
        )
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
            st.error(f"Database Error: {e}")
            return False

def add_payment(sale_id, amount_paid, payment_method):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        payment_date = datetime.now().date()
        cursor.execute("""
            INSERT INTO payment_splits
            (sale_id, payment_date, amount_paid, payment_method)
            VALUES (?,?,?,?)
            """,
            (sale_id, payment_date, amount_paid, payment_method))
        cursor.execute("""
            UPDATE customer_sales
            SET received_amount = x.total_paid,
                status = CASE
                    WHEN x.total_paid >= gross_sales THEN 'Close'
                    ELSE 'Open'
                END
            FROM customer_sales cs
            CROSS APPLY (
                SELECT ISNULL(SUM(amount_paid),0) AS total_paid
                FROM payment_splits ps
                WHERE ps.sale_id = cs.sale_id
            ) x
            WHERE cs.sale_id = ?
        """, (sale_id,))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
        st.title("Sales Management System")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user_data = login_user(username, password)
            if user_data:
                st.session_state.logged_in = True
                st.session_state.user = user_data
                st.rerun()
            else:
                st.error("Invalid Username or Password")
else:
    if st. session_state.user is None:
        st.session_state.logged_in = False
        st.rerun()

    user = st.session_state.user
    st.sidebar.title(f"Welcome, {user['username']}")
    st.sidebar.write(f"Role: {user['role']}")
    if user.get('branch_id') and user.get('branch_name'):
        st.sidebar.write(f"Branch: {user['branch_name']}")
    
    menu = ["Dashboard", "View Sales", "Add Sale", "Add Payment", "Branch Management", "SQL Reports"]
    choice = st.sidebar.selectbox("Menu", menu)

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
        
    if choice == "Dashboard":
        st.title("Sales Dashboard - Insights & Reporting")

        if user['role'] == 'Super Admin':
            df = get_sales_data(None)
        else:
            df = get_sales_data(user['branch_id'])

        st.markdown("##### Filters ")
        f1, f2, f3, f4 = st.columns(4)

        with f1:
            start_date = st.date_input("Start_Date", datetime.now() - timedelta(days=30), key="f1")
        
        with f2:
            End_date = st.date_input("End_Date", datetime.now(), key="f2")

        with f3:
            if user['role'] == 'Super Admin':
                b_df = get_branches()
                b_opt = ['All branches'] + b_df['branch_name'].tolist() 
                s_branch = st.selectbox("Branch", b_opt, key="f3")
                
                s_id = None
                if s_branch == 'All Branches':               
                    matched = b_df[b_df['branch_name'] == s_branch]
                    if len(matched_rows) >0:
                        s_id = matched_rows['branch_id'].iloc[0]
            else:
                s_id = user['branch_id']
                st.selectbox("Branch", [user.get('branch_name')], disabled=True, key="f3_user")
        
        with f4:
            p_list = ['All Products'] + df['product_name'].unique().tolist()
            s_prod = st.selectbox("Product Name", p_list,key="f4")

            st.divider()

        df.rename(columns={'sale_date': 'date'}, inplace=True)
        df['date'] = pd.to_datetime(df['date'])
        df = df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= End_date)]
        if user['role'] == 'Super Admin' and s_id is not None:
            df = df[df['branch_id'] == s_id]
        if s_prod!= 'All Products':
            df = df[df['product_name'] == s_prod]

        if df.empty:
            st.info("No sales data found. Add a sale first.")
        else:
            st.subheader("Financial KPI Summary")
            total_sales = df['gross_sales'].sum()
            total_received = df['received_amount'].sum()
            total_pending = df['pending_amount'].sum()
            collection_percent = (total_received / total_sales * 100) if total_sales > 0 else 0

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.write("**Overall Revenue**")
                st.write(f"**RS. {total_sales:,.0f}**")
                
            with col2:    
                st.write("Total Received")
                st.write(f"**Rs. {total_received:,.0f}**")
                
            with col3:
                st.write("Total Pending")
                st.write(f"**Rs. {total_pending:,.0f}**")
                
            with col4:
                st.write("Collection Percent")
                st.write(f"**{collection_percent:,.1f}**")
            
            st.divider()

            if user['role'] == 'Super Admin':
                st.subheader("Branch Wise Sales Comparsion")
                branch_sales = df.groupby('branch_name')['gross_sales'].sum().reset_index()
                st.bar_chart(branch_sales.set_index('branch_name'))
                st.divider()

            st.subheader("Product-Wise Sales")
            product_sales = df.groupby('product_name')['gross_sales'].sum().reset_index()

            st.bar_chart(product_sales.set_index('product_name'))
            st.divider()

            st.subheader("All Sales Data")
            st.dataframe(df[['sale_id', 'branch_name', 'date', 'name', 'product_name', 'gross_sales', 'received_amount', 'pending_amount', 'status']], use_container_width=True)

    elif choice == "View Sales":
        st.title("All Sales")
        df = get_sales_data(user['branch_id'])
        st.dataframe(df, use_container_width=True)

    elif choice == "Add Sale":
        st.title("Add New Sale")
        branches = get_branches()
        
        with st.form("add_sale_form", clear_on_submit=True):
            if user['role'] == 'Super Admin':
                branch_id = st.selectbox("Branch", branches['branch_id'], format_func=lambda x: branches[branches['branch_id']==x]['branch_name'].values[0])
            else:
                branch_id = user['branch_id']
                st.info(f"Branch: {user.get('branch_name', 'N/A')}")

            customer_name = st.text_input("Customer Name")
            mobile_number = st.text_input("Mobile number")
            product_name = st.text_input("Course Name", placeholder="AI, ML, SQL, DS, DA, BA, FSD, BI")
            gross_sales = st.number_input("Gross_Sales / Course Fee", min_value=0.0)
            sale_date = st.date_input("Sale Date", datetime.now())

            submitted = st.form_submit_button("Add Sale")
            if submitted:
                if not customer_name:
                    st.error("Customer Name required")
                elif not product_name:
                    st.error("Course Name required")
                else:
                    data = (branch_id, sale_date, customer_name, mobile_number, product_name, gross_sales, received_amount, 'Open'
                    )
                    if add_sale(data):
                        st.success("Sale Added Successfully.Trigger will auto-update pending amount.")
                        st.rerun()

    elif choice == "Add Payment":
        st.title("Add Payment")
        df = get_sales_data(user['branch_id'])
        df['status'] = df['status'].astype(str)
        open_sales = df[df['status'].str.lower() == 'open']
        if open_sales.empty:
            st.warning("No Open Bills Found")
        else:
            sale_id = st.selectbox("Select Sale", open_sales['sale_id'], format_func=lambda x: f"{open_sales[open_sales['sale_id']==x]['name'].values[0]} - Pending: Rs. {open_sales[open_sales['sale_id']==x]['pending_amount'].values[0]}")
            max_amount = float(open_sales[open_sales['sale_id']==sale_id]['pending_amount'].values[0])
            amount_paid = st.number_input("Amount Paid", min_value=0.0, max_value=max_amount, value=0.0)
            payment_method = st.selectbox("payment_method", ["Cash", "UPI", "Card"])
            if st.button("Add Payment"):
                if amount_paid <= 0:
                    st.error("Amount should be greater than 0")
                else:
                   if add_payment(sale_id, amount_paid, payment_method):
                    st.success("Payment Added Successfully")
                    st.rerun()

    elif choice == "Branch Management":
        st.title("Branch Management")
        branches = get_branches()
        st.dataframe(branches, use_container_width=True)

    elif choice ==  "SQL Reports":
        st.title("SQL Query Reports")
        conn = get_connection()
        sql_questions = {

            "1. Retrieve all records from customer_sales":
            """
            SELECT * FROM customer_sales
            """,

            "2. Retrieve all records from branches":
            """
            SELECT * FROM branches
            """,

            "3. Retrieve all records from payment_splits":
            """
            SELECT * FROM payment_splits
            """,

            "4. Display all sales with status = 'Open'":
            """
            SELECT * FROM customer_sales
            WHERE status = 'Open'
            """,

            "5. Retrieve all sales belonging to the Chennai branch":
            """
            SELECT cs.*
            FROM customer_sales cs
            JOIN branches b
            ON cs.branch_id = b.branch_id
            WHERE b.branch_name = 'Chennai'
            """,

            "6. Calculate the total gross sales across all branches":
            """
            SELECT SUM(gross_sales) AS total_gross_sales
            FROM customer_sales
            """,

            "7. Calculate the total received amount across all sales":
            """
            SELECT SUM(received_amount) AS total_received_amount
            FROM customer_sales
            """,

            "8. Calculate the total pending amount across all sales":
            """
            SELECT SUM(pending_amount) AS total_pending_amount
            FROM customer_sales
            """,

            "9. Count the total number of sales per branch":
            """
            SELECT b.branch_name,
            COUNT(cs.sale_id) AS total_sales
            FROM customer_sales cs
            JOIN branches b
            ON cs.branch_id = b.branch_id
            GROUP BY b.branch_name
            """,

            "10. Find the average gross sales amount":
            """
            SELECT AVG(gross_sales) AS average_gross_sales
            FROM customer_sales
            """,

            "11. Retrieve sales details along with the branch name":
            """
            SELECT cs.sale_id,
            cs.name,
            cs.product_name,
            cs.gross_sales,
            b.branch_name
            FROM customer_sales cs
            JOIN branches b
            ON cs.branch_id = b.branch_id
            """,

            "12. Retrieve sales details along with total payment received":
            """
            SELECT cs.sale_id,
            cs.name,
            SUM(ps.amount_paid) AS total_payment
            FROM customer_sales cs
            JOIN payment_splits ps
            ON cs.sale_id = ps.sale_id
            GROUP BY cs.sale_id, cs.name
            """,

            "13. Show branch-wise total gross sales":
            """
            SELECT b.branch_name,
            SUM(cs.gross_sales) AS total_gross_sales
            FROM customer_sales cs
            JOIN branches b
            ON cs.branch_id = b.branch_id
            GROUP BY b.branch_name
            """,

            "14. Display sales along with payment method used":
            """
            SELECT cs.sale_id,
            cs.name,
            ps.payment_method
            FROM customer_sales cs
            JOIN payment_splits ps
            ON cs.sale_id = ps.sale_id
            """,

            "15. Retrieve sales along with branch admin name":
            """
            SELECT cs.sale_id,
            cs.name,
            b.branch_admin_name
            FROM customer_sales cs
            JOIN branches b
            ON cs.branch_id = b.branch_id
            """,

            "16. Find sales where pending amount is greater than 5000":
            """
            SELECT *
            FROM customer_sales
            WHERE pending_amount > 5000
            """,

            "17. Retrieve top 3 highest gross sales":
            """
            SELECT TOP 3 *
            FROM customer_sales
            ORDER BY gross_sales DESC
            """,

            "18. Find the branch with highest total gross sales":
            """
            SELECT TOP 1 b.branch_name,
            SUM(cs.gross_sales) AS total_sales
            FROM customer_sales cs
            JOIN branches b
            ON cs.branch_id = b.branch_id
            GROUP BY b.branch_name
            ORDER BY total_sales DESC
            """,

            "19. Retrieve monthly sales summary":
            """
            SELECT YEAR([date]) AS year,
            MONTH([date]) AS month,
            SUM(gross_sales) AS total_sales
            FROM customer_sales
            GROUP BY YEAR([date]), MONTH([date])
            ORDER BY year, month
            """,

            "20. Calculate payment method-wise total collection":
            """
            SELECT payment_method,
            SUM(amount_paid) AS total_collection
            FROM payment_splits
            GROUP BY payment_method
            """
        }

        question = st.selectbox(
            "Choose Question",
            list(sql_questions.keys())
        )
        query = sql_questions[question]
        st.code(query, language="sql")
        df = pd.read_sql(query, conn)
        st.dataframe(df)
        conn.close()

        



        
        
        
