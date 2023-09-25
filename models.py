from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    google_id = db.Column(db.String(80), primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    files = db.relationship("File", backref="user", lazy=True)

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
    user_id = db.Column(db.String(80), db.ForeignKey("user.google_id"), nullable=False)

    def __init__(self, file_name, user_id):
        self.file_name = file_name
        self.user_id = user_id

    @classmethod
    def in_database(cls, n, id):
        f = File.query.filter_by(user_id=id, file_name=n).first()
        return f is not None
