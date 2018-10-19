
'''
imports for web app
'''

import os #required to save uploaded files
from flask import Flask, render_template, session, redirect, url_for, flash,request
import sqlite3

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    conn=sqlite3.connect('GS.db')
    curs=conn.cursor()
    curs.execute("SELECT * FROM image_classifications ORDER BY id desc")
    results = curs.fetchall()
    conn.close()

    return render_template('results.html', results=results)

@app.route('/remove', methods=['GET', 'POST'])
def remove():
    id = request.args.get('id')
    conn=sqlite3.connect('GS.db')
    curs=conn.cursor()
    curs.execute("delete FROM image_classifications where ID ="+id)
    conn.commit()
    conn.close()

    return redirect(url_for("index"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080,debug=True)
