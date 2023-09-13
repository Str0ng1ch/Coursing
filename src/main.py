import configparser
import io
import subprocess
from functools import wraps

import pandas as pd
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, session
from flask_mysqldb import MySQL
from openpyxl import Workbook
import requests

config = configparser.ConfigParser()
config.read('settings.ini')

DATABASE, TABLE = config['DATABASE']['DATABASE'], config['DATABASE']['TABLE']
ADMIN_USERNAME, ADMIN_PASSWORD = config['SECURITY']['ADMIN_USERNAME'], config['SECURITY']['ADMIN_PASSWORD']
SECRET_KEY = config['SECURITY']['SECRET_KEY']

app = Flask(__name__)
app.config['MYSQL_HOST'] = config['DATABASE']['HOST']
app.config['MYSQL_USER'] = config['DATABASE']['USER']
app.config['MYSQL_PASSWORD'] = config['DATABASE']['PASSWORD']
app.config['MYSQL_DB'] = DATABASE

mysql = MySQL(app)
app.secret_key = SECRET_KEY


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/rating')
def rating():
    return render_template('rating.html')


def handle_bad_request(error):
    return render_template('errors/error400.html'), 400


def handle_unauthorized(error):
    return render_template('errors/error401.html'), 401


def handle_forbidden(error):
    return render_template('errors/error403.html'), 403


def handle_not_found(error):
    return render_template('errors/error404.html'), 404


def handle_not_allowed(error):
    return render_template('errors/error405.html'), 405


def handle_too_many_request(error):
    return render_template('errors/error429.html'), 429


def handle_internal_server(error):
    return render_template('errors/error500.html'), 500


def handle_service_unavailable(error):
    return render_template('errors/error503.html'), 503


def handle_gateway_timeout(error):
    return render_template('errors/error504.html'), 504


@app.route('/get-score-details', methods=['POST'])
def get_score_details():
    data = request.json
    name, dog_type = data['score'].split(', ')
    name = name.replace('<br>', '/')

    cursor = mysql.connection.cursor()
    query = f"SELECT date, position, max_position, score, link FROM {DATABASE}.{TABLE} WHERE Nickname = '{name}' AND Type = '{dog_type}' ORDER BY date"
    cursor.execute(query)
    score_details = cursor.fetchall()

    cursor.close()

    return jsonify(score_details)


@app.route('/get-data', methods=['POST'])
def get_data():
    selected_rating = request.json['selectedRating']
    selected_sex = request.json['selectedSex']
    name_search = request.json['nameSearch']
    selected_score = request.json['selectedScore']
    selected_type = request.json['selectedType']
    all_rows = request.json.get('allRows', False)

    cur = mysql.connection.cursor()
    base_query = f"""SELECT * FROM (SELECT Type, Sex, Nickname, breedarchive_link, SUM(Score) AS TotalScore
                                    FROM {DATABASE}.{TABLE} 
                                    WHERE Date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
                                    GROUP BY Type, Sex, Nickname, breedarchive_link
                                    ) AS sub"""
    conditions = []
    params = []

    if selected_type != "all":
        conditions.append("Type=%s")
        params.append(selected_type)
    if selected_sex != "all":
        conditions.append("Sex=%s")
        params.append(selected_sex)
    if name_search:
        conditions.append("Nickname LIKE %s")
        params.append("%" + name_search + "%")
    if selected_score != "all":
        score_range = selected_score.split('-')
        conditions.append("TotalScore BETWEEN %s AND %s")
        params.extend([score_range[0], score_range[1]])

    if conditions:
        query = base_query + " WHERE " + " AND ".join(conditions)
    else:
        query = base_query

    query += " ORDER BY TotalScore DESC, Nickname ASC"
    if not all_rows:
        query += " LIMIT 9"
    cur.execute(query, params)
    rows = cur.fetchall()
    data = [{"type": row[0], "sex": row[1], "name": row[2], "TotalScore": row[4], "breedLink": row[3]} for row in
            rows]

    return jsonify(data)


@app.route('/get-all-data', methods=['POST'])
def get_all_data():
    selected_date = request.json['selectedDate']
    selected_sex = request.json['selectedSex']
    name_search = request.json['nameSearch']
    selected_rating = request.json['selectedRating']
    selected_type = request.json['selectedType']
    all_rows = request.json.get('allRows', False)

    cur = mysql.connection.cursor()
    base_query = f"""SELECT * FROM {DATABASE}.{TABLE}"""
    conditions = []
    params = []

    if selected_type != "all":
        conditions.append("Type=%s")
        params.append(selected_type)
    if selected_sex != "all":
        conditions.append("Sex=%s")
        params.append(selected_sex)
    if name_search:
        conditions.append("Nickname LIKE %s")
        params.append("%" + name_search + "%")
    if selected_rating != "all":
        rating_range = selected_rating.split('-')
        conditions.append("Score BETWEEN %s AND %s")
        params.extend([rating_range[0], rating_range[1]])
    if selected_date != "":
        conditions.append("Date=%s")
        params.append(selected_date)

    if conditions:
        query = base_query + " WHERE " + " AND ".join(conditions)
    else:
        query = base_query

    query += " ORDER BY Date DESC, Nickname ASC"
    if not all_rows:
        query += " LIMIT 9"

    cur.execute(query, params)
    rows = cur.fetchall()
    data = [{"id": row[0], "date": row[1], "position": row[2], "type": row[3], "sex": row[4], "Nickname": row[5],
             "max_position": row[6], "score": row[7], "link": row[8], "breedLink": row[9]} for row in rows]

    return jsonify(data)


@app.route('/get-nicknames', methods=['POST'])
def get_nicknames():
    name_search = request.json['nameSearch']
    all_rows = request.json.get('allRows', False)

    cur = mysql.connection.cursor()
    base_query = f"""SELECT DISTINCT(Nickname), breedarchive_link FROM {DATABASE}.{TABLE}"""

    conditions = []
    params = []

    if name_search:
        conditions.append("Nickname LIKE %s")
        params.append("%" + name_search + "%")

    if conditions:
        query = base_query + " WHERE " + " AND ".join(conditions)
    else:
        query = base_query

    query += " ORDER BY Nickname ASC"
    if not all_rows:
        query += " LIMIT 9"
    cur.execute(query, params)
    rows = cur.fetchall()
    data = [{"nickname": row[0], "breedLink": row[1]} for row in rows]

    return jsonify(data)


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization

        if auth and auth.username == ADMIN_USERNAME and auth.password == ADMIN_PASSWORD:
            return f(*args, **kwargs)

        return Response(
            'Could not verify your access level for that URL.\n'
            'You have to login with proper credentials.', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'})

    return decorated


def delete_from_table():
    message = None
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {DATABASE}.{TABLE}_copy; "
                       f"CREATE TABLE {DATABASE}.{TABLE}_copy AS SELECT * FROM {DATABASE}.{TABLE};")
        cursor.execute(f"DELETE FROM {DATABASE}.{TABLE};")
        cursor.execute(f"ALTER TABLE {DATABASE}.{TABLE} AUTO_INCREMENT = 1;")
        mysql.connection.commit()
        message = "Все данные успешно удалены!"
    except Exception as e:
        mysql.connection.rollback()
        message = f"Ошибка при удалении данных! \nОшибка: {e}"
    finally:
        cursor.close()
        return message


def add_data_from_excel():
    file = request.files['excel_file']
    cursor = mysql.connection.cursor()
    message = None

    try:
        df = pd.read_excel(file)

        values_list = df.apply(lambda row: (
            row['Дата'], row['Место'], row['Класс'], row['Пол'], row['Кличка'], row['Всего мест'],
            row['Очки'], row['Ссылка на источник'], row['Ссылка на Breed Archive']
        ), axis=1)
        values_list = values_list.apply(lambda tpl: tuple('' if pd.isna(val) else val for val in tpl)).tolist()

        query = (f"INSERT INTO {DATABASE}.{TABLE} "
                 f"(Date, Position, Type, Sex, Nickname, max_position, Score, link, breedarchive_link)"
                 f" VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)")

        cursor.executemany(query, values_list)
        mysql.connection.commit()
        message = "Данные успешно внесены из Excel файла!"
    except Exception as e:
        mysql.connection.rollback()
        message = f"Ошибка при занесении данных из Excel файла! \nОшибка: {e}"
    finally:
        cursor.close()
        return message


def run_script():
    link = request.form.get('link', '')
    message = None
    try:
        subprocess.run(['python', 'src/make_ratings.py', link], check=True)
        message = f"Данные успешно внесены из {link}"
    except Exception as e:
        message = f"Ошибка при занесении данных из {link}. \nОшибка: {e}"
    finally:
        return message


def add_data_from_form():
    message = None
    date = request.form['date']
    position = request.form['position']
    dog_type = request.form['type']
    sex = request.form['sex']
    nickname = request.form['nickname']
    max_position = request.form['max_position']
    score = request.form['score']
    link = request.form['link']
    breed_link = request.form['breed_link']

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            f"INSERT INTO {DATABASE}.{TABLE} "
            f"(Date, Position, Type, Sex, Nickname, max_position, Score, link, breedarchive_link) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (date, position, dog_type, sex, nickname, max_position, score, link, breed_link))
        mysql.connection.commit()
        message = "Данные успешно внесены из формы!"
    except Exception as e:
        mysql.connection.rollback()
        message = f"Ошибка при занесении данных из формы! \nОшибка: {e}"
    finally:
        cur.close()
        return message


def download_excel(cursor, full=True):
    query = f"SELECT * FROM {DATABASE}.{TABLE}"
    cursor.execute(query)
    result = cursor.fetchall()

    column_names = ['ID', 'Дата', 'Место', 'Класс', 'Пол', 'Кличка',
                    'Всего мест', 'Очки', 'Ссылка на источник', 'Ссылка на Breed Archive']

    wb = Workbook()
    ws = wb.active

    ws.append(column_names)
    if full:
        for row in result:
            ws.append(row)

    excel_data = io.BytesIO()
    wb.save(excel_data)
    excel_data.seek(0)

    return excel_data


@app.route('/add-data', methods=['GET', 'POST'])
@requires_auth
def add_data():
    message = session.pop('message', None)
    if request.method == 'POST':
        if 'delete_button' in request.form:
            message = delete_from_table()
        elif 'excel_file' in request.files:
            message = add_data_from_excel()
        elif 'run_script' in request.form:
            message = run_script()
        else:
            message = add_data_from_form()
        session['message'] = message
        return redirect(url_for('add_data'))
    if 'download_full_excel' in request.args:
        cursor = mysql.connection.cursor()
        try:
            excel_data = download_excel(cursor, full=True)
            return Response(
                excel_data.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment;filename=database.xlsx"}
            )
        except Exception as e:
            message = f"Ошибка при скачивании Excel файла! \nОшибка: {e}"
        finally:
            cursor.close()
    elif 'download_part_excel' in request.args:
        cursor = mysql.connection.cursor()
        try:
            excel_data = download_excel(cursor, full=False)
            return Response(
                excel_data.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment;filename=template.xlsx"}
            )
        except Exception as e:
            message = f"Ошибка при скачивании Excel файла! \nОшибка: {e}"
        finally:
            cursor.close()

    return render_template('add_data.html', message=message)


@app.route("/update-data", methods=["POST"])
def update_data():
    updated_data = request.json
    row_id = updated_data['id']
    date = updated_data['date'].split('.')
    position = updated_data['position']
    dog_type = updated_data['type']
    sex = updated_data['sex']
    nickname = updated_data['nickname']
    max_position = updated_data['max_position']
    score = updated_data['score']
    link = updated_data['link']
    breed_link = updated_data['BreedLink']

    formatted_date = f"{date[2]}-{date[1]}-{date[0]}"
    cur = mysql.connection.cursor()
    try:
        update_query = f"""
            UPDATE {DATABASE}.{TABLE}
            SET
              Date = %s,
              Position = %s,
              Type = %s,
              Sex = %s,
              Nickname = %s,
              max_position = %s,
              Score = %s,
              link = %s,
              breedarchive_link = %s
            WHERE
              ID = %s
            """
        cur.execute(update_query,
                    (formatted_date, position, dog_type, sex, nickname, max_position, score, link, breed_link, row_id))

        if breed_link == '':
            query = f"""
                SELECT breedarchive_link FROM {DATABASE}.{TABLE}
                WHERE breedarchive_link != '' AND Nickname = "{nickname}"
                """
            cur.execute(query)
            breed_link = cur.fetchone()
            breed_link = '' if breed_link is None else breed_link[0]

        if breed_link != '':
            update_query = f"""
                UPDATE {DATABASE}.{TABLE}
                SET
                  breedarchive_link = %s
                WHERE
                  Nickname = %s
                """
            cur.execute(update_query, (breed_link, nickname))

        mysql.connection.commit()
        return jsonify()
    except Exception:
        mysql.connection.rollback()
        return jsonify(), 500
    finally:
        cur.close()


def check_url_status(url):
    try:
        response = requests.get(url)
        return response.status_code
    except requests.exceptions.RequestException:
        return None


def check():
    cursor = mysql.connection.cursor()
    cursor.execute(f"SELECT * FROM {DATABASE}.{TABLE}")

    column_names = [desc[0] for desc in cursor.description]
    dataset = pd.DataFrame(cursor.fetchall(), columns=column_names)

    print(column_names)
    mask = ~dataset['Sex'].isin(['Кобель', 'Сука'])
    result = dataset[mask]
    print(result['ID'].to_list())

    mask = ~dataset['Type'].isin(['Стандартный', 'Стандартный-спринтеры', 'Юниоры'])
    result = dataset[mask]
    print(result['ID'].to_list())

    mask = dataset['Score'] != dataset['Max_position'] - dataset['Position'] + 1
    result = dataset[mask]
    print(result['ID'].to_list())

    unique_links = dataset['link'].unique()
    link_status_dict = {link: check_url_status(link) for link in unique_links}
    dataset['Link_status'] = dataset['link'].map(link_status_dict)
    dataset['breedarchive_link_status'] = dataset['breedarchive_link'].apply(check_url_status)

    non_working_links = dataset[(dataset['Link_status'] != 200)]
    print(non_working_links['ID'].to_list())

    non_working_breedLinks = dataset[(dataset['breedarchive_link_status'] != 200)]
    print(non_working_breedLinks['ID'].to_list())

    dataset[['Part1', 'Part2']] = dataset['Nickname'].str.split('/', n=1, expand=True)


error_handlers = {
    400: handle_bad_request,
    401: handle_unauthorized,
    403: handle_forbidden,
    404: handle_not_found,
    405: handle_not_allowed,
    429: handle_too_many_request,
    500: handle_internal_server,
    503: handle_service_unavailable,
    504: handle_gateway_timeout
}

for error_code, handler in error_handlers.items():
    app.register_error_handler(error_code, handler)

if __name__ == '__main__':
    app.run(debug=True)
