import sqlite3
import json

DBFILENAME = 'subjects.sqlite'
FORMATIONS_FILE = 'formations.json'
SUBJECTS_FILE = 'subjects.json'

# Utilitaire pour exécuter une requête SQL
def db_run(query, args=(), db_name=DBFILENAME):
    with sqlite3.connect(db_name) as conn:
        cur = conn.execute(query, args)
        conn.commit()

def load():
    # Réinitialiser les tables
    db_run('DROP TABLE IF EXISTS user')
    db_run('DROP TABLE IF EXISTS subject')
    db_run('DROP TABLE IF EXISTS formation')

    # Créer les tables
    db_run('''
        CREATE TABLE user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT
        )
    ''')
    
    db_run('''
        CREATE TABLE formation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )
    ''')

    db_run('''
        CREATE TABLE subject (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            year INT,
            course TEXT,
            file_path TEXT,
            formation_id INTEGER
        )
    ''')

    # Insérer les formations
    with open(FORMATIONS_FILE, 'r', encoding='utf-8') as f:
        formations = json.load(f)
    for formation in formations:
        db_run('INSERT INTO formation VALUES (:id, :name)', formation)

    # Insérer les sujets
    with open(SUBJECTS_FILE, 'r', encoding='utf-8') as f:
        subjects = json.load(f)
    for subject in subjects:
        db_run('''
            INSERT INTO subject 
            VALUES (:id, :title, :description, :year, :course, :file_path, :formation_id)
        ''', subject)


# Exécution
load()
