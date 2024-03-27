from urllib.request import urlopen

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

from openpyxl import Workbook

# Создаем новую книгу Excel и выбираем активный лист
wb = Workbook()
ws = wb.active

# Добавляем заголовки столбцов
ws.append(['Distance', 'Dog Type', 'Sex', 'Nickname', 'Title', 'Lap 1', 'Lap 2', 'Lap 3'])

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


def make_rating():
    page = urlopen("http://procoursing.ru/Complete_Results_2023-06-10.html")
    soup = BeautifulSoup(page, features="html.parser")

    all_rows = soup.find_all('tr', align="center", bgcolor="#ffffff")
    for i, row in enumerate(all_rows):
        cols = row.find_all('td')
        if cols[2].get_text() == 'Уиппет':
            breed = cols[2].get_text()
            dog_type = cols[3].get_text()
            sex = cols[4].get_text()
            nickname = cols[5].get_text()
            distance = cols[6].get_text()
            lap_1 = cols[9].get_text() if cols[9].get_text() == '' else cols[9].get_text().split()[0]
            lap_2 = cols[12].get_text() if cols[12].get_text() == '' else cols[12].get_text().split()[0]
            lap_3 = cols[15].get_text() if cols[15].get_text() == '' else cols[15].get_text().split()[0]
            title = cols[17].get_text()
            print(distance, dog_type, sex, nickname, title, lap_1, lap_2, lap_3)

            ws.append([distance, dog_type, sex, nickname, title, lap_1, lap_2, lap_3])
            wb.save('dog_data.xlsx')


make_rating()
