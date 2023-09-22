from flask import Flask, url_for, redirect, session, render_template, request, flash, send_file
from authlib.integrations.flask_client import OAuth

from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from utils import login_required, allowed_ext
from datetime import timedelta

import os
from werkzeug.utils import secure_filename

from flask_socketio import SocketIO
import time

UPLOAD_DIR = './files/'

app = Flask(__name__)
socketio = SocketIO(app)

load_dotenv('secret.env')
app.secret_key = os.getenv("APP_SECRET")
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///user.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR


db = SQLAlchemy(app)

# DB Model
#--------------------------------------------------------------------------

class User(db.Model):
    google_id = db.Column(db.String(80), primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    files = db.relationship('File', backref='user', lazy=True)

    def __init__(self, google_id, name):
        self.google_id = google_id
        self.name = name

    @classmethod
    def in_database(cls, id):
        user = User.query.filter_by(google_id=id).first()
        return user is not None

class File(db.Model):
    file_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    file_name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.String(80), db.ForeignKey('user.google_id'), nullable=False)

    def __init__(self, file_name, user_id):
        self.file_name = file_name
        self.user_id = user_id

    @classmethod
    def in_database(cls, n, id):
        f = File.query.filter_by(user_id=id, file_name=n).first()
        return f is not None

#--------------------------------------------------------------------------
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid profile'},
    jwks_uri= "https://www.googleapis.com/oauth2/v3/certs"
)

@app.route('/delete/<filename>', methods=['POST'])
@login_required
def delete(filename):
    file = File.query.filter(File.file_name == filename).first()
    try:
        if file.user_id == session["id"]:
            db.session.delete(file)
            os.remove(os.path.join(UPLOAD_DIR,session["id"],filename))
            db.session.commit()
        else:
            return {"Response":"Can't access that file"}
    except KeyError:
        return {"Response":"An error occured, try again later"}
    return redirect("/")
    
@app.route('/download/<filename>', methods=['GET'])
@login_required
def download(filename):
    path = os.path.join(app.config["UPLOAD_FOLDER"], session['id'], filename)
    try:
        if File.query.filter(File.file_name == filename).first().user_id == session["id"]:
            return send_file(path, as_attachment=True)
        else:
            return "Not authorized to download"
    except KeyError:
        return "An error occured, try again later"

@app.route("/", methods=['GET', 'POST'])
@login_required
def home():
    data = File.query.filter(File.user_id == session["id"]).all()
    f_list = [d.file_name for d in data]
    if request.method == 'POST':
        try: 
            file = request.files['file']
        except KeyError:
            flash('No file part')
            return redirect(request.url)
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_ext(file.filename):
            filename = secure_filename(file.filename)
            if len(filename) > 120:
                flash("File name too long")
                return redirect(request.url)
            if File.in_database(filename,session["id"]):
                new_name = filename
                while File.in_database(new_name,session["id"]):
                    split_fname = new_name.split(".")
                    new_name = split_fname[0] + "(copy)." + split_fname[1]
                if len(filename) > 120:
                    flash("File name too long")
                    return redirect(request.url)
                filename = new_name
            chunk_size = 1024
            total_size = int(request.headers['Content-Length'])
            uploaded_size = 0
            path = os.path.join(app.config['UPLOAD_FOLDER'],session['id'], filename)
            last_update_time = time.time()
            with open(path, 'wb') as f:
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    uploaded_size += len(chunk)
                    current_time = time.time()
                    if current_time - last_update_time >= 0.25:
                        socketio.emit('upload-progress', {'uploaded':uploaded_size,'total':total_size})
                        last_update_time = current_time
                    f.write(chunk)
            socketio.emit('upload-progress', {'uploaded':total_size,'total':total_size})
            socketio.emit('upload-done')

            if not os.path.isfile(path):
                flash("Error uploading the file")
                return redirect(request.url)
            file_record = File(filename, session["id"])
            db.session.add(file_record)
            db.session.commit()
            return redirect(url_for('home'))
        elif file:
            flash('Disallowed file extension')
            return redirect(request.url)
    
    return render_template("index.html", username=session["name"], files=f_list)

@app.route("/login")
def login():
    google = oauth.create_client("google")
    redirect_uri = url_for("authorize", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/authorize")
def authorize():
    google = oauth.create_client("google")
    token = google.authorize_access_token()
    response = google.get("userinfo", token=token)
    user_info = response.json()
    session["id"] = user_info["id"]
    session["name"] = user_info["given_name"]
    if not User.in_database(user_info["id"]):
        user = User(user_info["id"], user_info["given_name"])
        db.session.add(user)
        db.session.commit()
    if not os.path.isdir(os.path.join(UPLOAD_DIR, user_info["id"])):
        os.mkdir(os.path.join(UPLOAD_DIR, user_info["id"]))
    return redirect("/")

@login_required
@app.route("/logout")
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')

if __name__ == "__main__":
    if not os.path.isdir(UPLOAD_DIR):
        os.mkdir(UPLOAD_DIR)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
