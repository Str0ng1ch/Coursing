from flask import Flask, render_template, request, jsonify
from flask_mysqldb import MySQL

app = Flask(__name__)

# Конфигурация MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'My$QLP@ssw0rd'
app.config['MYSQL_DB'] = 'dog_ratings'

mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('rating2.html')


@app.route('/get-data', methods=['POST'])
def get_data():
    selected_sex = request.json['selectedSex']
    name_search = request.json['nameSearch']
    selected_rating = request.json['selectedRating']  # новый параметр
    all_rows = request.json.get('allRows', False)

    cur = mysql.connection.cursor()
    base_query = "SELECT * FROM dogs"
    conditions = []
    params = []

    if selected_sex != "all":
        conditions.append("Sex=%s")
        params.append(selected_sex)
    if name_search:
        conditions.append("NicknameRU LIKE %s")
        params.append("%" + name_search + "%")
    if selected_rating != "all":
        rating_range = selected_rating.split('-')
        conditions.append("score BETWEEN %s AND %s")
        params.extend([rating_range[0], rating_range[1]])

    if conditions:
        query = base_query + " WHERE " + " AND ".join(conditions)
    else:
        query = base_query

    query += " ORDER BY score DESC, NicknameRU ASC"
    if not all_rows:
        query += " LIMIT 10"

    cur.execute(query, params)
    rows = cur.fetchall()
    data = [{"id": row[0], "name": row[3], "sex": row[5], "rating": row[8]} for row in rows]  # добавлено row[6] для рейтинга, индекс может отличаться в зависимости от структуры вашей таблицы

    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)
