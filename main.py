
from flask import Flask, render_template, redirect, url_for, g
from scraper import getImages
from time import sleep
from datetime import datetime
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
db_initialized = False

db_config = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'database': os.environ.get('DB_NAME')
}

def init_db():
    connection = get_db_connection()
    cursor = connection.cursor()
    with open("schema.sql") as f:
        sql_commands = f.read().split(';')  # split by semicolon
        
        for command in sql_commands:
            command = command.strip()
            if command:
                cursor.execute(command)
    connection.commit()
    cursor.close()
    connection.close()


def get_db_connection():
    max_retries = 5
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            return mysql.connector.connect(**db_config)
        except mysql.connector.Error as err:
            if attempt < max_retries - 1:
                print(f'Database connection failed (attempt {attempt + 1}/{max_retries}): {err}')
                sleep(retry_delay)
            else:
                raise

# Run once before the first request
@app.before_request
def initialize():
    if not hasattr(g, 'db_initialized'):
        init_db()
        db_initialized = True

# Home page - showing all the memes
@app.route("/")
def index():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM memes ORDER BY created_at DESC")
    memes = cursor.fetchall()
    connection.close()

    return render_template("index.html", memes=memes)

@app.route("/add")
def add_meme():
    memes = getImages()
    if memes:
        url = memes[0][0]
        name = memes[0][1] # Filename
        created_at = datetime.now()

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO memes (name, url, created_at) VALUES (%s, %s, %s)", (name, url, created_at))
        connection.commit()
        connection.close()

    return redirect(url_for('index'))

@app.route('/delete/<int:meme_id>', methods = ['POST'])
def delete_meme(meme_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM memes WHERE id = %s", (meme_id,))
    connection.commit()
    connection.close()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)



