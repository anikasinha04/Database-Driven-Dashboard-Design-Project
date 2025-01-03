import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector
import pgeocode

# wide view
st.set_page_config(layout="wide")

# apply a dark theme
base = "dark"

# title and photo
st.title("LargeCo Dashboard designed by Alexa Garcia and Anika Sinha")
st.image("https://i.ibb.co/2kdqCDm/logo.jpg", use_container_width=False)
st.caption("Thanks to ChatGPT for the image")

# create tabs
tab_customers, tab_products, tab_employees = st.tabs(["Customers", "Products", "Employees"])

# connect to sql server
def connect_mysql():
    try:
        mydb = mysql.connector.connect(
            host="itpmysql.usc.edu",
            port=3306,
            user="anikasin",
            password="5691082656",
            database="largeco",
        )
        return mydb
    except mysql.connector.Error as err:
        raise Exception(f"Error connecting to the database: {err}")

# Call the connection function and create the cursor
try:
    mydb = connect_mysql()
    mycursor = mydb.cursor()
except Exception as e:
    st.error(f"Failed to connect to the database: {e}")

# get revenue data
query = """
select cust_code, concat(cust_fname, ' ', cust_lname) as CustomerName, sum(inv_total) as Revenue
from lgcustomer natural join lginvoice 
group by cust_code
order by revenue desc
limit 10;
"""
mycursor.execute(query)
myresult = mycursor.fetchall()

# convert data to dataframe
data = pd.DataFrame(myresult, columns=["CUST_CODE", "NAME", "REVENUE"])

# get customer data
query_balance = """
select *
from lgcustomer
"""
mycursor.execute(query_balance)
myresult_balance = mycursor.fetchall()
data_balance = pd.DataFrame(myresult_balance, columns=["CUST_CODE", "CUST_FNAME", "CUST_LNAME", "CUST_STREET", "CUST_CITY", "CUST_STATE", "CUST_ZIP", "CUST_BALANCE"])
data_balance["CUST_BALANCE"] = pd.to_numeric(data_balance["CUST_BALANCE"], errors="coerce")

# convert to lat and long
nomi = pgeocode.Nominatim("us")
data_balance["LATITUDE"] = data_balance["CUST_ZIP"].apply(lambda x: nomi.query_postal_code(x).latitude)
data_balance["LONGITUDE"] = data_balance["CUST_ZIP"].apply(lambda x: nomi.query_postal_code(x).longitude)

data_balance = data_balance.dropna(subset=["LATITUDE", "LONGITUDE"])

# customer tab
with tab_customers:
    st.header("Customers")
    col1, col2 = st.columns(2)

    # column 1 in customer tab
    with col1:
        st.subheader("Most Valuable Customers")
        fig = px.bar(
            data,
            x="NAME",
            y="REVENUE",
        )
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("View Raw Data"):
            st.write(data)

    # column 2 in customer tab
    with col2:
        st.subheader("Customer Balance Map")
        st.map(data_balance, latitude = "LATITUDE", longitude = "LONGITUDE", size = "CUST_BALANCE")
        with st.expander("Customer Balance Data"):
            st.write(data_balance[["CUST_CODE", "CUST_FNAME", "CUST_LNAME", "CUST_STREET", "CUST_CITY", "CUST_STATE", "CUST_ZIP", "CUST_BALANCE"]])

# get brand data
query_products = """
select brand_name, count(*) as ProductCount
from lgproduct join lgbrand on lgproduct.brand_id = lgbrand.brand_id
group by brand_name
order by brand_name;
"""
mycursor.execute(query_products)
myresult_products = mycursor.fetchall()
data_products = pd.DataFrame(myresult_products, columns=["BRAND_NAME", "NUMPRODUCTS"])

# get inventory data
query_inventory = """
select prod_description, prod_category, prod_price, prod_qoh
from lgproduct
"""
mycursor.execute(query_inventory)
myresult_inventory = mycursor.fetchall()
data_inventory = pd.DataFrame(myresult_inventory, columns=["PROD_DESCRIPTION", "PROD_CATEGORY", "PROD_PRICE", "PROD_QOH"])

data_inventory["PROD_PRICE"] = pd.to_numeric(data_inventory["PROD_PRICE"], errors="coerce")
data_inventory["PROD_QOH"] = pd.to_numeric(data_inventory["PROD_QOH"], errors="coerce")
data_inventory["INVENTORY_VALUE"] = data_inventory["PROD_PRICE"] * data_inventory["PROD_QOH"]

# products tab
with tab_products:
    st.header("Products")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Products by Brand")
        fig_products = px.pie(
            data_products,
            names="BRAND_NAME",
            values="NUMPRODUCTS",
        )
        st.plotly_chart(fig_products, use_container_width=True)
        with st.expander("Brand Data"):
            st.write(data_products)
    with col2:
        st.subheader("Inventory Value")
        fig_inventory = px.scatter(
            data_inventory,
            x="PROD_QOH",
            y="PROD_PRICE",
            size="INVENTORY_VALUE",
            color="PROD_CATEGORY",
            hover_name="PROD_DESCRIPTION",
        )
        st.plotly_chart(fig_inventory, use_container_width=True)
        with st.expander("Inventory Data"):
            st.write(data_inventory[["PROD_DESCRIPTION", "PROD_CATEGORY", "PROD_PRICE", "PROD_QOH"]])

query_employees = """
select concat(a.emp_fname, ' ', a.emp_lnamel) as MANAGERNAME, a.dept_name, concat(e.emp_fname, ' ', e.emp_lnamel) as EMPLOYEENAME
from (select emp_num, emp_fname, emp_lnamel, dept_num, dept_name
from lgdepartment natural join lgemployee) a join lgemployee e on a.dept_num = e.dept_num
where a.dept_name = "ACCOUNTING" or a.dept_name = "SALES" or a.dept_name = "PURCHASING"
"""
mycursor.execute(query_employees)
myresult_employees = mycursor.fetchall()
data_employees = pd.DataFrame(myresult_employees, columns=["MANAGERNAME", "DEPT_NAME", "EMPLOYEENAME"])

query_top = """
select concat(emp_fname, " ", emp_lnamel) as EMPLOYEENAME, sum(inv_total) as Total_Revenue, employee_id
from lgemployee e join lginvoice i on e.emp_num = i.employee_id
group by e.emp_num, emp_fname, emp_lnamel
order by Total_Revenue desc
limit 20;
"""
mycursor.execute(query_top)
myresult_top = mycursor.fetchall()
data_top =  pd.DataFrame(myresult_top, columns=["EMPLOYEENAME", "Revenue", "Employee_ID"])

# employees tab
with tab_employees:
    st.header("Employees")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Departments, Managers, Employees")
        fig_employees = px.sunburst(
            data_employees,
            path=["DEPT_NAME", "MANAGERNAME", "EMPLOYEENAME"],color="DEPT_NAME",
            color_discrete_map={"ACCOUNTING": "green", "SALES": "red", "PURCHASING": "blue"},
        )
        st.plotly_chart(fig_employees, use_container_width=True)
        with st.expander("Manager Data"):
            st.write(data_employees)
    with col2:
        st.subheader("Top N Employees")
        n_employees = st.slider(
            "How many top employees?",
            min_value=1,
            max_value=len(data_top),
            value=20
        )
        filtered_df = data_top.head(n_employees)
        fig_employees = px.bar(
            filtered_df, x="EMPLOYEENAME", y="Revenue", color="Revenue"
        )
        st.plotly_chart(fig_employees, use_container_width=True)
        with st.expander("Employee Data"):
            st.write(filtered_df)
