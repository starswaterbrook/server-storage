from flask import session, redirect
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = dict(session).get('id', None)
        if user:
            return f(*args, **kwargs)
        return redirect("/login")
    return decorated_function

def allowed_ext(filename):
    file_ext = filename.rsplit('.', 1)[1].lower()
    ALLOWED_EXTENSIONS = ["txt", "pdf", "png", "jpg", "jpeg", "gif", "mp3", "mp4"]
    return file_ext in ALLOWED_EXTENSIONS