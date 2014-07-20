# -*- coding: utf-8 -*-

import os, datetime, psycopg2, markdown
from contextlib import closing
from flask import render_template, abort, request, url_for, redirect, session, g, Flask
from passlib.hash import pbkdf2_sha256
from TwitterAPI import TwitterAPI
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
import credentials


twitter_api = TwitterAPI('ijzWFhaG2UtO92A6tVskUy9Qt', 'hSrMEpYCBwIm1QTflr2kTAEh2z7h6vNMqNLKTMWtxWp0YTwUDo', '2579503044-xER6bBw95UstPV88QWGxsL9JlOoUxEE1sIKx5vv', 'W4vdT8c0Fwn8dF07CoxdcrL4SDbvgnHRcudT0m6nZ0nM2')


DB_SCHEMA = """
DROP TABLE IF EXISTS entries;
CREATE TABLE entries (
    id serial PRIMARY KEY,
    title VARCHAR (127) NOT NULL,
    text TEXT NOT NULL,
    created TIMESTAMP NOT NULL
)
"""

DB_ENTRY_INSERT = """
INSERT INTO entries (title, text, created) VALUES (%s, %s, %s)
"""

DB_ENTRIES_LIST = """
SELECT id, title, text, created FROM entries ORDER BY created DESC
"""

DB_ENTRY_LIST = """
SELECT id, title, text, created FROM entries WHERE entries.id = %s
"""

DB_DELETE_ENTRY_LIST = """
DELETE FROM entries WHERE entries.id = %s
"""

app = Flask(__name__)


def get_entry(id):
    """return a single entry based on id"""
    con = get_database_connection()
    cur = con.cursor()
    cur.execute(DB_ENTRY_LIST, [id])
    keys = ('id', 'title', 'text', 'created')
    row = cur.fetchone()
    cur.execute(DB_DELETE_ENTRY_LIST, [id])
    return dict(zip(keys, row))    # we use fetchone instead of fetch all


def delete_entry_db(id):
    """deletes a single entry based on id"""
    con = get_database_connection()
    cur = con.cursor()
    cur.execute(DB_DELETE_ENTRY_LIST, [id])


def get_all_entries():
    """return a list of all entries as dicts"""
    con = get_database_connection()
    cur = con.cursor()
    cur.execute(DB_ENTRIES_LIST)
    keys = ('id', 'title', 'text', 'created')
    return [dict(zip(keys, row)) for row in cur.fetchall()]

def write_entry(title, text):
    """writes an entry(title, text) to db."""
    if not title or not text:
        raise ValueError("Title and text required for writing an entry")
    con = get_database_connection()
    cur = con.cursor()
    now = datetime.datetime.utcnow()
    cur.execute(DB_ENTRY_INSERT, [title, text, now])


@app.route('/edit/<id>', methods=['GET', 'POST'])
def edit_entry(id):
    """return a single entry from the db, using id"""
    if session['logged_in']:
        entry = get_entry(id)
        return render_template('edit_form.html', entry=entry)
    else:
        abort(500)

@app.route('/delete/<id>', methods=['GET', 'POST'])
def delete_entry(id):
    """calls delete_entry_db, to delete an entry from the db."""
    if session['logged_in']:
        delete_entry_db(id)
        return ''
    else:
        abort(500)


@app.route('/show_add_entry')
def show_add_entry():
    """returns a form for adding an entry"""
    return render_template('add_entry.html')

@app.route('/')
def show_entries():
    """shows all entries in the db."""
    entries = get_all_entries()
    if len(entries) > 0:
        for entry in entries:
            entry['title'] = markdown.markdown(entry['title'])
            text = markdown.markdown(entry['text'], extensions=['codehilite(linenums=False)'])
            entry['text'] = text

    print entries

    return render_template('list_entries.html', entries=entries) # we can itteratively entry['text'] = markdown.markdonw(entry['text'],

@app.route('/add', methods=['POST'])
def add_entry():
    """calls write_entry to write a single entry to the db."""
    try:
        write_entry(request.form['title'], request.form['text'])
    	twitter_tweet = twitter_api.request('statuses/update', {'status': request.form['title']})
    except psycopg2.Error:
        # this will catch any errors generated by the database
        abort(500)
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """performs login check."""
    error = None
    if request.method == 'POST':
        try:
            do_login(request.form['username'].encode('utf-8'),
                     request.form['password'].encode('utf-8'))
        except ValueError:
            error = "Login Failed"
        else:
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """logs out a logged in user."""
    session.pop('logged_in', None)
    return redirect(url_for('show_entries'))


app.config['DATABASE'] = os.environ.get(
    'DATABASE_URL', 'dbname=learning_journal'
)
app.config['ADMIN_USERNAME'] = os.environ.get(
    'ADMIN_USERNAME', 'admin'
)

app.config['ADMIN_PASSWORD'] = os.environ.get(
    'ADMIN_PASSWORD', pbkdf2_sha256.encrypt('admin')
)

app.config['SECRET_KEY'] = os.environ.get(
    'FLASK_SECRET_KEY', 'sooperseekritvaluenooneshouldknow'
)

def connect_db():
    """Return a connection to the configured database"""
    return psycopg2.connect(app.config['DATABASE'])

def init_db():
    """Initialize the database using DB_SCHEMA

    WARNING: executing this function will drop existing tables.
    """
    with closing(connect_db()) as db:
        db.cursor().execute(DB_SCHEMA)
        db.commit()

def get_database_connection():
    """creates a db connection."""
    db = getattr(g, 'db', None)
    if db is None:
        g.db = db = connect_db()
    return db

@app.teardown_request
def teardown_request(exception):
    """uses flask g object to close an open db connection."""
    db = getattr(g, 'db', None)
    if db is not None:
        if exception and isinstance(exception, psycopg2.Error):
            db.rollback()
        else:
            db.commit()
        db.close()
        g.db = None # get rid of db from the g namespace

def do_login(username='', passwd=''):
    """performs user login authentication"""
    if username != app.config['ADMIN_USERNAME']:
        raise ValueError
    if not pbkdf2_sha256.verify(passwd, app.config['ADMIN_PASSWORD']):
        raise ValueError
    session['logged_in'] = True


if __name__ == '__main__':
    app.run(debug=True, port=5002)