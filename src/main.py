import mysql.connector
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, session
from flask_mysqldb import MySQL
import configparser
import pandas as pd
import subprocess
import io
from openpyxl import Workbook
from functools import wraps

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
    query = f"SELECT date, position, max_position, score FROM results WHERE Nickname = '{name}' AND Type = '{dog_type}' ORDER BY date"
    cursor.execute(query)
    score_details = cursor.fetchall()

    cursor.close()

    return jsonify(score_details)


@app.route('/get-data', methods=['POST'])
def get_data():
    selected_sex = request.json['selectedSex']
    name_search = request.json['nameSearch']
    selected_rating = request.json['selectedRating']
    selected_type = request.json['selectedType']
    all_rows = request.json.get('allRows', False)

    cur = mysql.connection.cursor()
    base_query = f"""SELECT * FROM (SELECT Type, Sex, Nickname, SUM(Score) AS TotalScore 
                                    FROM {DATABASE}.{TABLE} 
                                    WHERE Date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
                                    GROUP BY Type, Sex, Nickname
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
    if selected_rating != "all":
        rating_range = selected_rating.split('-')
        conditions.append("TotalScore BETWEEN %s AND %s")
        params.extend([rating_range[0], rating_range[1]])

    if conditions:
        query = base_query + " WHERE " + " AND ".join(conditions)
    else:
        query = base_query

    query += " ORDER BY TotalScore DESC, Nickname ASC"
    if not all_rows:
        query += " LIMIT 9"
    cur.execute(query, params)
    rows = cur.fetchall()
    data = [{"type": row[0], "sex": row[1], "name": row[2], "TotalScore": row[3]} for row in
            rows]

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
        cursor.execute("DROP TABLE IF EXISTS copy_results; CREATE TABLE copy_results AS SELECT * FROM results;")
        cursor.execute("DELETE FROM results;")
        cursor.execute("ALTER TABLE results AUTO_INCREMENT = 1;")
        mysql.connection.commit()
        message = "Все данные успешно удалены!"
    except Exception:
        mysql.connection.rollback()
        message = "Ошибка при удалении данных!"
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
            row['Date'], row['Position'], row['Type'], row['Sex'],
            row['Nickname'], row['Max_position'], row['Score']
        ), axis=1).tolist()

        query = "INSERT INTO coursing.results (Date, Position, Type, Sex, Nickname, max_position, Score) " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"

        cursor.executemany(query, values_list)
        mysql.connection.commit()
        message = "Данные успешно внесены из Excel файла!"
    except Exception:
        mysql.connection.rollback()
        message = "Ошибка при занесении данных из Excel файла!"
    finally:
        cursor.close()
        return message


def run_script():
    link = request.form.get('link', '')
    message = None
    try:
        subprocess.run(['python', 'src/make_ratings.py', link], check=True)
        message = f"Данные успешно внесены из {link}"
    except Exception:
        message = f"Ошибка при занесении данных из {link}"
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

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "INSERT INTO results (Date, Position, Type, Sex, Nickname, max_position, Score) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (date, position, dog_type, sex, nickname, max_position, score))
        mysql.connection.commit()
        message = "Данные успешно внесены из формы!"
    except Exception:
        mysql.connection.rollback()
        message = "Ошибка при занесении данных из формы!"
    finally:
        cur.close()
        return message


def download_excel(cursor, full=True):
    query = "SELECT * FROM results"
    cursor.execute(query)
    result = cursor.fetchall()

    column_names = [column[0] for column in cursor.description]

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
        except Exception:
            message = "Ошибка при скачивании Excel файла!"
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
        except Exception:
            message = "Ошибка при скачивании Excel файла!"
        finally:
            cursor.close()

    return render_template('add_data.html', message=message)


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
