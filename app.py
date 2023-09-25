from flask import (
    Flask,
    url_for,
    redirect,
    session,
    render_template,
    request,
    flash,
    send_file,
    abort,
)
from flask_socketio import SocketIO

from oauth_config import oauth
from models import db, User, File
from config import Config

from utils import login_required, allowed_ext
from werkzeug.utils import secure_filename

import os
import time

app = Flask(__name__)
socketio = SocketIO(app)

app.config.from_object(Config)
db.init_app(app)
oauth.init_app(app)


@app.route("/delete/<filename>", methods=["POST"])
@login_required
def delete(filename):
    file = File.query.filter(
        File.file_name == filename, File.user_id == session["id"]
    ).first()
    if not file:
        abort(404)
    try:
        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], session["id"], filename))
        db.session.delete(file)
        db.session.commit()
        flash("File deleted successfully")
    except Exception:
        abort(500)
    return redirect("/")


@app.route("/download/<filename>", methods=["GET"])
@login_required
def download(filename):
    path = os.path.join(app.config["UPLOAD_FOLDER"], session["id"], filename)
    file_exists = os.path.isfile(path)
    db_file = File.query.filter(
        File.file_name == filename, File.user_id == session["id"]
    ).first()
    try:
        if db_file and file_exists:
            return send_file(path, as_attachment=True)
        elif file_exists:
            abort(401)
        else:
            abort(404)
    except KeyError:
        abort(500)


@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        try:
            file = request.files["file"]
        except KeyError:
            flash("No file part")
            socketio.emit("upload-fail")
            return redirect(url_for("home"), 303)

        if not allowed_ext(file.filename):
            flash("Disallowed file extension")
            socketio.emit("upload-fail")
            return redirect(url_for("home"), 303)

        if file.filename == "":
            flash("No selected file")
            socketio.emit("upload-fail")
            return redirect(url_for("home"), 303)

        if file and allowed_ext(file.filename):
            filename = secure_filename(file.filename)
            if len(filename) > 120:
                flash("File name too long")
                socketio.emit("upload-fail")
                return redirect(url_for("home"), 303)
            if File.in_database(filename, session["id"]):
                new_name = filename
                while File.in_database(new_name, session["id"]):
                    split_fname = new_name.split(".")
                    new_name = split_fname[0] + "(copy)." + split_fname[1]
                if len(filename) > 120:
                    flash("File name too long")
                    socketio.emit("upload-fail")
                    return redirect(url_for("home"), 303)
                filename = new_name
            chunk_size = 1024
            total_size = int(request.headers["Content-Length"])
            uploaded_size = 0
            path = os.path.join(app.config["UPLOAD_FOLDER"], session["id"], filename)
            last_update_time = time.time()
            with open(path, "wb") as f:
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    uploaded_size += len(chunk)
                    current_time = time.time()
                    if current_time - last_update_time >= 0.25:
                        socketio.emit(
                            "upload-progress",
                            {"uploaded": uploaded_size, "total": total_size},
                        )
                        last_update_time = current_time
                    f.write(chunk)
            socketio.emit(
                "upload-progress", {"uploaded": total_size, "total": total_size}
            )
            socketio.emit("upload-done")

            if not os.path.isfile(path):
                flash("Error uploading the file")
                return redirect(url_for("home"), 303)
            file_record = File(filename, session["id"])
            db.session.add(file_record)
            db.session.commit()
            flash("File uploaded successfully")
            return redirect(url_for("home"), 303)

    data = File.query.filter(File.user_id == session["id"]).all()
    f_list = [d.file_name for d in data]
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
    if not os.path.isdir(os.path.join(app.config["UPLOAD_FOLDER"], user_info["id"])):
        os.mkdir(os.path.join(app.config["UPLOAD_FOLDER"], user_info["id"]))
    return redirect("/")


@login_required
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    if not os.path.isdir(app.config["UPLOAD_FOLDER"]):
        os.mkdir(app.config["UPLOAD_FOLDER"])
    with app.app_context():
        db.create_all()
    app.run(debug=True)
