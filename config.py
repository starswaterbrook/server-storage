from datetime import timedelta
from dotenv import load_dotenv
import os
UPLOAD_DIR = "./files/"
load_dotenv("secret.env")

class Config:
    SECRET_KEY = os.getenv("APP_SECRET")
    SESSION_COOKIE_NAME = "google-login-session"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)
    SQLALCHEMY_DATABASE_URI = "sqlite:///user.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = UPLOAD_DIR