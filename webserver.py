from flask import Flask, url_for, redirect, session, render_template, request, send_from_directory, flash, send_file
from authlib.integrations.flask_client import OAuth

from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from utils import login_required, allowed_ext
from cryptography.fernet import Fernet
from datetime import timedelta

import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './files/'

app = Flask(__name__)
load_dotenv('secret.env')
fernet = Fernet(os.getenv("SAFE_KEY"))
app.secret_key = os.getenv("APP_SECRET")
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///user.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


db = SQLAlchemy(app)

#--------------------------------------------------------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    google_id = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(512), unique=True, nullable=False)
    files = db.relationship('File', backref='user', lazy=True)
    def __init__(self, google_id, name, email):
        self.google_id = google_id
        self.name = name
        self.email = email
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
    def in_database(cls, n):
        f = File.query.filter_by(file_name=n).first()
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
    client_kwargs={'scope': 'openid email profile'},
    jwks_uri= "https://www.googleapis.com/oauth2/v3/certs"
)

@app.route('/delete/<filename>', methods=['POST'])
@login_required
def delete(filename):
    file = File.query.filter(File.file_name == filename).first()
    try:
        if file.user_id == session["id"]:
            db.session.delete(file)
            os.remove(f"./files/{filename}")
            db.session.commit()
        else:
            return "Can't access that file"
    except KeyError:
        return "An error occured, try again later"
    return redirect("/")
    
@app.route('/download/<filename>')
@login_required
def download(filename):
    path = app.config["UPLOAD_FOLDER"] + filename
    try:
        if File.query.filter(File.file_name == filename).first().user_id == session["id"]:
            return send_file(path, as_attachment=True)
        else:
            return "Not authorize to download"
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
            if not File.in_database(f"{session['id']}_{filename}"):
                if len(f"{session['id']}_{filename}") > 120:
                    flash("File name too long")
                    return redirect(request.url)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{session['id']}_{filename}"))
                file_record = File(f"{session['id']}_{filename}", session["id"])
                db.session.add(file_record)
                db.session.commit()
            else:
                flash("Same name file present, delete before uploading")
                return redirect(request.url)
            return redirect(url_for('home'))
        elif file:
            flash('Unallowed file extension')
            return redirect(request.url)
    
    return render_template("index.html", username=session["name"], files = f_list)

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
    #print(fernet.encrypt(user_info["id"].encode()).decode())
    #print(fernet.encrypt(user_info["email"].encode()).decode())
    if not User.in_database(user_info["id"]):
        user = User(user_info["id"], user_info["given_name"], user_info["email"])
        db.session.add(user)
        db.session.commit()
    return redirect("/")

@app.route("/logout")
def logout():
    try:
        _ = session["id"]
        for key in list(session.keys()):
            session.pop(key)
    except KeyError:
        return "Not logged in!"
    return redirect('/')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
