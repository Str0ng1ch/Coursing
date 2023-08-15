from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/rating')
def rating():
    conn = mysql.connector.connect(user='root', password='My$QLP@ssw0rd', host='127.0.0.1', database='dog_ratings')
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT sex, NicknameEN, score FROM dogs ORDER BY score DESC ")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('rating.html', data=data)


if __name__ == '__main__':
    app.run(debug=True)
