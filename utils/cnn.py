import mysql.connector


def conectar():
    return mysql.connector.connect(
        host="172.16.78.103",
        port=3306,
        user="marcus",
        password="marcus123",
        database="db_techvarejo"
    )