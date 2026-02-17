import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="@H.dpriyo0177@.",
        database="companydb",
    )


# def get_connection():
#     return mysql.connector.connect(
#         host="shortline.proxy.rlwy.net",   # Railway host
#         user="root",
#         password="clzLsJULDKBuhRbFRafmXPuTghdJubZx",  # NOT your local password
#         database="companydb",
#         port=48561
#     )s