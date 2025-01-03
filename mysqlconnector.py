import mysql.connector

def connect_mysql():
    mydb = mysql.connector.connect(
        host="itpmysql.usc.edu",
        port=3306,
        user="anikasin",
        password="5691082656",
        database="largeco",
    )
    return mydb