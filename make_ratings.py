import urllib.error
from urllib.request import urlopen
import mysql.connector
import re
import random
try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup
from sys import argv

config = {
  'user': 'root',
  'password': 'My$QLP@ssw0rd',
  'host': 'localhost',
  'database': 'dog_ratings',
}

# path, url = argv
url = "http://procoursing.ru/Complete_Results_2023-07-01.html"
page = urlopen(url)
soup = BeautifulSoup(page, features="html.parser")

date_pattern = r"\d{4}-\d{2}-\d{2}"
date = re.search(date_pattern, url).group()


def parse_data():
    all_dogs = []
    all_rows = soup.find_all('tr', align="center", bgcolor="#ffffff")
    for i, row in enumerate(all_rows):
        if i % 2 == 0:
            all_cols = row.find_all('td')
            dog = []
            try:
                for j, col in enumerate(all_cols):
                    if j == 0 or j == 20:
                        dog.append(int(col.get_text()))
                    if j == 3 or j == 4:
                        dog.append(col.get_text())
                    if j == 5:
                        names = col.get_text().split('/')
                        if len(names) == 1:
                            if ord(names[0].strip()[0]) < 200:
                                dog.append(names[0].strip() + "/")
                            else:
                                dog.append("/" + names[0].strip())
                        else:
                            if ord(names[0].strip()[0]) < 200:
                                dog.append(names[0].strip() + "/" + names[1].strip())
                            else:
                                dog.append(names[1].strip() + "/" + names[0].strip())

                all_dogs.append(dog)
            except ValueError:
                pass
    return all_dogs


def find_max_position(dog_type, sex, dogs):
    max_position = 0
    for dog in dogs:
        if dog[1] == dog_type and dog[2] == sex:
            max_position = max(max_position, dog[0])
    return max_position


def insert_max_position(dog_type, sex, dogs):
    max_position = find_max_position(dog_type, sex, dogs)
    for dog in dogs:
        if dog[1] == dog_type and dog[2] == sex:
            dog.append(max_position)
            dog.append(max_position - dog[0] + 1)
    return dogs


def insert_all_max_positions(all_dogs):
    arr = [('Стандартный', 'Кобель'), ('Стандартный', 'Сука'), ('Стандартный-спринтеры', 'Кобель'),
           ('Стандартный-спринтеры', 'Сука'), ('Юниоры', 'Кобель'), ('Юниоры', 'Сука')]
    for pair in arr:
        all_dogs = insert_max_position(pair[0], pair[1], all_dogs)
    return all_dogs


def insert_into_database(all_dogs):
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    insert_query = "INSERT INTO `dog_ratings`.all_results (Date, Position, Type, Sex, Nickname, Points, max_position, score) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    for row in all_dogs:
        if len(row) == 7:
            cursor.execute(insert_query, [date] + row)

    connection.commit()
    cursor.close()
    connection.close()


def main():
    all_dogs = parse_data()
    all_dogs = insert_all_max_positions(all_dogs)
    for dog in all_dogs:
        print(dog)
    insert_into_database(all_dogs)


if __name__ == "__main__":
    main()
