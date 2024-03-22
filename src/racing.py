from urllib.request import urlopen

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


def make_rating():
    page = urlopen("http://procoursing.ru/Complete_Results_2023-09-02_V_R.html")
    soup = BeautifulSoup(page, features="html.parser")

    all_rows = soup.find_all('tr', align="center", bgcolor="#ffffff")
    for i, row in enumerate(all_rows):
        cols = row.find_all('td')
        if cols[2].get_text() == 'Уиппет':
            print(cols[2].get_text(), cols[3].get_text(), cols[4].get_text(),
                  cols[5].get_text(), cols[6].get_text(), cols[9].get_text(), cols[12].get_text(),
                  cols[15].get_text(), cols[17].get_text())


make_rating()
