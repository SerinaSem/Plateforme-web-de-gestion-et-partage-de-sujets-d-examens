import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
import math


DBFILENAME = 'subjects.sqlite'

# Utility functions
def db_fetch(query, args=(), all=False, db_name=DBFILENAME):
  with sqlite3.connect(db_name) as conn:
    # to allow access to columns by name in res
    conn.row_factory = sqlite3.Row 
    cur = conn.execute(query, args)
    # convert to a python dictionary for convenience
    if all:
      res = cur.fetchall()
      if res:
        res = [dict(e) for e in res]
      else:
        res = []
    else:
      res = cur.fetchone()
      if res:
        res = dict(res)
  return res

def db_insert(query, args=(), db_name=DBFILENAME):
  with sqlite3.connect(db_name) as conn:
    cur = conn.execute(query, args)
    conn.commit()
    return cur.lastrowid


def db_run(query, args=(), db_name=DBFILENAME):
  with sqlite3.connect(db_name) as conn:
    cur = conn.execute(query, args)
    conn.commit()


def db_update(query, args=(), db_name=DBFILENAME):
  with sqlite3.connect(db_name) as conn:
    cur = conn.execute(query, args)
    conn.commit()
    return cur.rowcount
  


def login(identifier, password):
    user = db_fetch(
        "SELECT id, password_hash FROM user WHERE name = ? OR email = ?",
        (identifier, identifier)
    )
    if user and check_password_hash(user['password_hash'], password):
        return user['id']
    return -1



def new_user(name, password, email):
    existing_user = db_fetch("SELECT id FROM user WHERE name = ?", (name,))
    if existing_user:
        return -1
    password_hash = generate_password_hash(password)
    return db_insert("INSERT INTO user (name, password_hash, email) VALUES (?, ?, ?)",
                     (name, password_hash, email))

def get_user_by_id(user_id):
    return db_fetch("SELECT id, name, email FROM user WHERE id = ?", (user_id,))


def create_formation(name, description):
    return db_insert("INSERT INTO formation (name, description) VALUES (?, ?)", (name, description))

def get_all_formations():
    return db_fetch("SELECT * FROM formation", all=True)

def delete_formation(id):
    db_run("DELETE FROM formation WHERE id = ?", (id,))

def get_formation(id):
    return db_fetch("SELECT * FROM formation WHERE id = ?", (id,))

def create_subject(title, description, year, course, file_path, formation_id):
    return db_insert('''INSERT INTO subject (title, description, year, course, file_path, formation_id)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     (title, description, year, course, file_path, formation_id))

def update_subject(id, subject):
    return db_update('''UPDATE subject SET title = :title, description = :description, year = :year,
                        course = :course, file_path = :file_path, formation_id = :formation_id
                        WHERE id = :id''',
                     {**subject, 'id': id})

def delete_subject(id):
    db_run("DELETE FROM subject WHERE id = ?", (id,))

def get_subject(id):
    return db_fetch("SELECT * FROM subject WHERE id = ?", (id,))

def search_subjects(query="", page=1):
    num_per_page = 20
    total = db_fetch("SELECT count(*) FROM subject WHERE title LIKE ?", ('%' + query + '%',))
    num_found = total['count(*)']

    results = db_fetch(
        "SELECT id as entry, title, year, course FROM subject WHERE title LIKE ? ORDER BY year DESC LIMIT ? OFFSET ?",
        ('%' + query + '%', num_per_page, (page - 1) * num_per_page),
        all=True
    )

    return {
        'results': results,
        'num_found': num_found,
        'query': query,
        'next_page': page + 1 if (page * num_per_page) < num_found else None,
        'page': page,
        'num_pages': math.ceil(num_found / num_per_page)
    }

def get_subjects_by_formation(formation_id):
    return db_fetch(
        "SELECT * FROM subject WHERE formation_id = ? ORDER BY year DESC",
        (formation_id,),
        all=True
    )
