import mysql.connector
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import configparser
import pandas as pd

config = configparser.ConfigParser()
config.read('settings.ini')

DATABASE, TABLE = config['DATABASE']['DATABASE'], config['DATABASE']['TABLE']
app = Flask(__name__)
app.config['MYSQL_HOST'] = config['DATABASE']['HOST']
app.config['MYSQL_USER'] = config['DATABASE']['USER']
app.config['MYSQL_PASSWORD'] = config['DATABASE']['PASSWORD']
app.config['MYSQL_DB'] = DATABASE

mysql = MySQL(app)
app.secret_key = 'your_secret_key'

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/rating')
def rating():
    return render_template('rating.html')


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


@app.route('/add-data', methods=['GET', 'POST'])
def add_data():
    message = session.pop('message', None)
    if request.method == 'POST':
        if 'excel_file' in request.files:
            file = request.files['excel_file']
            cursor = mysql.connection.cursor()

            try:
                df = pd.read_excel(file)

                values_list = df.apply(lambda row: (
                    row['Date'], row['Position'], row['Type'], row['Sex'], row['Nickname'],
                    row['Points'], row['Max_position'], row['Score']
                ), axis=1).tolist()

                query = "INSERT INTO coursing.results (Date, Position, Type, Sex, Nickname, Points, max_position, Score) " \
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

                cursor.executemany(query, values_list)
                mysql.connection.commit()
                message = "Данные успешно внесены из Excel файла!"
            except Exception:
                mysql.connection.rollback()
                message = "Ошибка при занесении данных из Excel файла!"
            finally:
                cursor.close()

        else:
            date = request.form['date']
            position = request.form['position']
            type = request.form['type']
            sex = request.form['sex']
            nickname = request.form['nickname']
            points = request.form['points']
            max_position = request.form['max_position']
            score = request.form['score']

            cur = mysql.connection.cursor()
            try:
                cur.execute(
                    "INSERT INTO results (Date, Position, Type, Sex, Nickname, Points, max_position, Score) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (date, position, type, sex, nickname, points, max_position, score))
                mysql.connection.commit()
                message = "Данные успешно внесены из формы!"
            except Exception:
                mysql.connection.rollback()
                message = "Ошибка при занесении данных из формы!"
            finally:
                cur.close()
        session['message'] = message
        return redirect(url_for('add_data'))

    return render_template('add_data.html', message=message)


if __name__ == '__main__':
    app.run(debug=True)
