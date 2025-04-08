from flask import Flask, session, Response, request, redirect, url_for, render_template, jsonify, send_from_directory
import data_model as model
from functools import wraps
import os
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'png', 'jpg'}  # selon ce que tu acceptes

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Generate your own secret key, e.g. by running :
#    python -c 'import secrets; print(secrets.token_hex())'
app.secret_key = b'bece2d81e66a6cdc1a3bde191dfb3d3bf12127730d9366664141843b5e48bd5b'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))  # Redirige vers la page de connexion
        return f(*args, **kwargs)
    return decorated_function

########################################
# Routes des pages principales du site #
########################################

@app.get('/')
def home():
  return render_template('index.html')

@app.get('/login')
def login_page():
  return render_template('login.html')

@app.post('/login')
def login_post():
    identifier = request.form['identifier']
    password = request.form['password']

    user_id = model.login(identifier, password)

    if user_id != -1:
        user = model.get_user_by_id(user_id) 
        session.clear()
        session['user_id'] = user_id
        session['name'] = user['name']
        session['email'] = user['email']
        return redirect(url_for('home'))
    else:
        return render_template('login.html', error="Identifiants incorrects")



@app.get('/new_user')
def new_user_page():
  return render_template('new_user.html')

@app.post('/new_user')
def new_user_post():
    name = request.form['name']
    password = request.form['password']
    email = request.form['email']
    error = None

    user_id = model.new_user(name, password, email)

    if user_id == -1:
        error = "Nom d'utilisateur déjà pris. Veuillez en choisir un autre."
    
    if error is None:
        session.clear()
        session['user_id'] = user_id
        session['name'] = name
        session['email'] = email
        return redirect(url_for('home'))
    else:
        return render_template("new_user.html", error=error)



@app.get('/formations')
def formations_list():
    formations = model.get_all_formations()
    return render_template('formations.html', formations=formations)

@app.get('/sujets/<int:formation_id>')
def sujets_par_formation(formation_id):
    subjects = model.get_subjects_by_formation(formation_id)
    formation = model.get_formation(formation_id)
    if not formation:
        return "Formation non trouvée", 404
    return render_template('subjects_by_formation.html', subjects=subjects, formation=formation)

@app.get('/subject/<int:id>')
def subject_detail(id):
    subject = model.get_subject(id)
    if not subject:
        return "Sujet non trouvé", 404
    return render_template('subject_detail.html', subject=subject)

@app.get('/subject/new')
@login_required
def new_subject_form():
    formations = model.get_all_formations()
    return render_template('new_subject.html', formations=formations)

@app.post('/subject')
@login_required
def create_subject_post():
    if 'file' not in request.files:
        return "Aucun fichier reçu", 400

    file = request.files['file']
    
    if file.filename == '':
        return "Fichier non sélectionné", 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Création du sujet en base
        data = {
            'title': request.form['title'],
            'description': request.form['description'],
            'year': int(request.form['year']),
            'course': request.form['course'],
            'file_path': filename,  # on ne stocke que le nom du fichier
            'formation_id': int(request.form['formation_id'])
        }
        subject_id = model.create_subject(**data)

        # 🔽 Ajouter aussi dans le fichier JSON
        subject_entry = {
            "id": subject_id,
            "title": data['title'],
            "description": data['description'],
            "year": data['year'],
            "course": data['course'],
            "file_path": data['file_path'],
            "formation_id": data['formation_id']
        }

        json_file = 'subjects.json'
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                subjects = json.load(f)
        except FileNotFoundError:
            subjects = []

        subjects.append(subject_entry)

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(subjects, f, ensure_ascii=False, indent=2)

        return redirect(url_for('sujets_par_formation', formation_id=data['formation_id']))

    return "Fichier invalide", 400


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
  session.clear()  # Supprime toutes les informations de session
  return redirect(url_for('home'))

@app.get('/subject/<id>/delete')
@login_required
def delete_form(id):
    entry = model.get_subject(int(id))
    if not entry:
        return "Sujet non trouvé", 404
    return render_template('delete.html', id=id, title=entry['title'])

@app.post('/subject/<int:id>/delete')
@login_required
def delete_subject_post(id):
    model.delete_subject(id)
    return redirect(url_for('formations_list'))  # ou /subjects, selon ce que tu veux

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
