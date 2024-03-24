import pandas as pd
import mysql.connector

# Функция для создания подключения к MySQL
def create_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="My$QLP@ssw0rd",
        database="coursing"
    )
    return connection

# Функция для создания таблицы в MySQL
def create_table(connection):
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS racing (
            ID int AUTO_INCREMENT PRIMARY KEY,
            Date date,
            Location varchar(100),
            Distance int,
            Type varchar(25),
            Sex varchar(10),
            Nickname varchar(200),
            title varchar(64),
            time_1 varchar(25),
            time_2 varchar(25),
            time_3 varchar(25),
            link varchar(250),
            breedarchive_link varchar(200),
            ignored varchar(25),
            Breed varchar(40)
        )
    """)
    connection.commit()

# Функция для вставки данных в MySQL
def insert_data(connection, data):
    cursor = connection.cursor()
    for index, row in data.iterrows():
        row = row.where(pd.notnull(row), '')
        # print(row)
        cursor.execute("""
            INSERT INTO racing (Date, Location, Distance, Type, Sex, Nickname, title, time_1, time_2, time_3, link, breedarchive_link, ignored, Breed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row['Дата'],
            row['Место'],
            row['Дистанция (м)'],
            row['Класс'],
            row['Пол'],
            row['Кличка'],
            row['Место/Титул'],
            row['Время 1'],
            row['Время 2'],
            row['Время 3'],
            row['Ссылка на источник'],
            row['Ссылка на Breed Archive'],
            row['Игнорированные ошибки'],
            row['Порода']
        ))
    connection.commit()

# Чтение данных из Excel файла
excel_file = 'results.xlsx'
data = pd.read_excel(excel_file)

# Подключение к MySQL
connection = create_connection()

create_table(connection)

# Вставка данных в MySQL
insert_data(connection, data)

# Закрытие соединения с базой данных
connection.close()
