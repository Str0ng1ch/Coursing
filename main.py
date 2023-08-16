from flask import Flask, render_template
import mysql.connector

from flask import Flask, render_template, request, jsonify
from flask_mysqldb import MySQL

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'My$QLP@ssw0rd'
app.config['MYSQL_DB'] = 'dog_ratings'

mysql = MySQL(app)


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
    selected_rating = request.json['selectedRating']  # новый параметр
    selected_type = request.json['selectedType']
    all_rows = request.json.get('allRows', False)

    cur = mysql.connection.cursor()
    base_query = """SELECT * FROM (SELECT Type, Sex, Nickname, SUM(Score) AS TotalScore 
                                    FROM all_results 
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
        query += " LIMIT 10"
    cur.execute(query, params)
    rows = cur.fetchall()
    data = [{"type": row[0], "sex": row[1], "name": row[2], "TotalScore": row[3]} for row in
            rows]

    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True)
