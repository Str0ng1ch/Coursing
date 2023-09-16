import configparser
import io
import subprocess
from datetime import datetime
from functools import wraps

import Levenshtein
import pandas as pd
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, session
from flask_mysqldb import MySQL
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

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
    selected_id = request.json['selectedID']
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
    if selected_id != '':
        conditions.append("ID LIKE %s")
        params.append("%" + selected_id + "%")

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
                 f" VALUES (%s, %s, %s, %s, UPPER(%s), %s, %s, %s, %s)")

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


def autofill_data():
    message = None
    cur = mysql.connection.cursor()
    try:
        mysql.connection.commit()
        message = f"Данные успешно заполнены"
    except Exception as e:
        mysql.connection.rollback()
        message = f"Ошибка при заполнении данных. \nОшибка: {e}"
    finally:
        cur.close()
        return message


def reset_ignored():
    message = None
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(f"UPDATE {DATABASE}.{TABLE} SET ignored = 0")
        mysql.connection.commit()
        message = "Ошибки успешно сброшены"
    except Exception as e:
        mysql.connection.rollback()
        message = f"Ошибка при сбросе ошибок. \nОшибка: {e}"
    finally:
        cursor.close()
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
            "VALUES (%s, %s, %s, %s, UPPER(%s), %s, %s, %s, %s)",
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
    sheet = wb.active

    sheet.append(column_names)
    if full:
        for row in result:
            sheet.append(row)

    for column in sheet.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            if isinstance(cell.value, datetime):
                max_length = max(max_length, len(cell.value.strftime("%Y-%m-%d")))
            else:
                max_length = max(max_length, len(str(cell.value)))
        adjusted_width = (max_length + 2)
        sheet.column_dimensions[column_letter].width = adjusted_width

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
        elif 'reset_ignored' in request.form:
            message = reset_ignored()
        elif 'autofill_data' in request.form:
            message = autofill_data()
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
              Nickname = UPPER(%s),
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


def find_similar_pairs_with_distance(values_list, min_distance, max_distance):
    similar_pairs = []
    for i in range(len(values_list)):
        for j in range(i + 1, len(values_list)):
            distance = Levenshtein.distance(values_list[i], values_list[j])
            if min_distance <= distance <= max_distance:
                similar_pairs.append((values_list[i], values_list[j], distance))

    return similar_pairs


@app.route("/ignore-data", methods=["POST"])
def ignore_data():
    errors = {
        "Неправильно указан пол": 1,
        'Неправильно указан класс': 2,
        'Неправильно посчитаны очки': 3,
        'Недействительная ссылка на результаты соревнований': 4,
        'Недействительная ссылка на BreedArchive': 5,
        'Недействительная дата': 6,
        'Позиция больше количества участников': 7,
        'Количество очков меньше 0': 8
    }
    row_id = request.json['id']
    error = request.json['error']
    cursor = mysql.connection.cursor()

    try:
        query = f"UPDATE {DATABASE}.{TABLE} SET ignored = {errors.get(error)} WHERE ID = {row_id}"
        cursor.execute(query)
        mysql.connection.commit()
        return jsonify()
    except Exception:
        mysql.connection.rollback()
        return jsonify(), 500
    finally:
        cursor.close()


@app.route("/check-database", methods=["POST"])
def check_database():
    cursor = mysql.connection.cursor()
    cursor.execute(f"SELECT * FROM {DATABASE}.{TABLE}")

    ids, errors = [], []
    column_names = [desc[0] for desc in cursor.description]
    dataset = pd.DataFrame(cursor.fetchall(), columns=column_names)

    mask = (~dataset['Sex'].isin(['Кобель', 'Сука'])) & (dataset['ignored'] != 1)
    result = dataset[mask]
    ids.extend(result['ID'].to_list())
    errors.extend(['Неправильно указан пол'] * len(result['ID'].to_list()))

    mask = (~dataset['Type'].isin(['Стандартный', 'Стандартный-спринтеры', 'Юниоры'])) & (dataset['ignored'] != 2)
    result = dataset[mask]
    ids.extend(result['ID'].to_list())
    errors.extend(['Неправильно указан класс'] * len(result['ID'].to_list()))

    mask = (dataset['Score'] != dataset['Max_position'] - dataset['Position'] + 1) & (dataset['ignored'] != 3)
    result = dataset[mask]
    ids.extend(result['ID'].to_list())
    errors.extend(['Неправильно посчитаны очки'] * len(result['ID'].to_list()))

    unique_links = dataset['link'].unique()
    link_status_dict = {link: check_url_status(link) for link in unique_links}
    dataset['Link_status'] = dataset['link'].map(link_status_dict)
    dataset['breedarchive_link_status'] = dataset['breedarchive_link'].apply(check_url_status)

    result = dataset[(dataset['Link_status'] != 200) & (dataset['ignored'] != 4)]
    ids.extend(result['ID'].to_list())
    errors.extend(['Недействительная ссылка на результаты соревнований'] * len(result['ID'].to_list()))

    result = dataset[(dataset['breedarchive_link_status'] != 200) & (dataset['ignored'] != 5)]
    ids.extend(result['ID'].to_list())
    errors.extend(['Недействительная ссылка на BreedArchive'] * len(result['ID'].to_list()))

    # dataset[['Part1', 'Part2']] = dataset['Nickname'].str.split('/', n=1, expand=True)
    # print(find_similar_pairs_with_distance(dataset['Part1'], 1, 4))
    # print(find_similar_pairs_with_distance(dataset['Part2'], 1, 4))
    #
    # dataset1 = dataset[dataset['Part1'] != '']
    # duplicates = dataset1[dataset1.duplicated(subset='Part1', keep=False)]
    # print(duplicates)
    #
    # result = pd.merge(duplicates, dataset1, on='Part1', how='left')
    # print(result)

    today = datetime.now().date()
    mask = (dataset['Date'] <= today)
    result = dataset.loc[(~mask) & (dataset['ignored'] != 6)]
    ids.extend(result['ID'].to_list())
    errors.extend(['Недействительная дата'] * len(result['ID'].to_list()))

    mask = (dataset['Position'] > dataset['Max_position']) & (dataset['ignored'] != 7)
    result = dataset[mask]
    ids.extend(result['ID'].to_list())
    errors.extend(['Позиция больше количества участников'] * len(result['ID'].to_list()))

    mask = (dataset['Score'] < 0) & (dataset['ignored'] != 8)
    result = dataset[mask]
    ids.extend(result['ID'].to_list())
    errors.extend(['Количество очков меньше 0'] * len(result['ID'].to_list()))

    return jsonify([{"id": row[0], "error": row[1]} for row in zip(ids, errors)])
    # TODO одна часть ника совпадает вторая нет


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
