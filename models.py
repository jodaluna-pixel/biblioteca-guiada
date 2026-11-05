from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
 
db = SQLAlchemy()
 
class Busqueda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    criterio = db.Column(db.String(20), nullable=False)
    termino = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc))


class LibroGuardado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(250), nullable=False)
    autor = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    anio = db.Column(db.Integer, nullable=True)
