from urllib.request import urlopen
import mysql.connector
import re

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

DATABASE, TABLE = "coursing", "results"
# config = {
#     'user': "u2255198_artem",
#     'password': "00zEbyTI3y5avEot",
#     'host': "server25.hosting.reg.ru",
#     'database': DATABASE,
# }
config = {
    'user': "root",
    'password': "My$QLP@ssw0rd",
    'host': "localhost",
    'database': DATABASE,
}


def parse_data(soup, breed):
    all_dogs = []
    all_rows = soup.find_all('tr', align="center", bgcolor="#ffffff")
    for i, row in enumerate(all_rows):
        if i % 2 == 0:
            all_cols = row.find_all('td')
            dog = []
            try:
                if all_cols[2].get_text() in breed:
                    dog.append(int(all_cols[0].get_text()))
                    dog.append(all_cols[3].get_text())
                    dog.append(all_cols[4].get_text())
                    names = all_cols[5].get_text().split('/')
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
                    dog.append(all_cols[2].get_text())
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


def insert_into_database(all_dogs, date, url):
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    insert_query = (
        f"INSERT INTO {DATABASE}.{TABLE} (Date, Position, Type, Sex, Nickname, breed, max_position, score, location, link, breedarchive_link, ignored) VALUES (%s, %s, %s, %s, UPPER(%s), %s, %s, %s, %s, %s, %s, %s)")
    for row in all_dogs:
        if len(row) == 7:
            cursor.execute(insert_query, [date] + row + ['', url] + ['', ''])

    connection.commit()
    cursor.close()
    connection.close()


def make_rating(url, breed):
    page = urlopen(url)
    soup = BeautifulSoup(page, features="html.parser")

    date_pattern = r"\d{4}-\d{2}-\d{2}"
    date = re.search(date_pattern, url).group()

    all_dogs = parse_data(soup, breed)
    all_dogs = insert_all_max_positions(all_dogs)
    insert_into_database(all_dogs, date, url)
