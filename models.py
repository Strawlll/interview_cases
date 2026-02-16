from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Case(db.Model):
    __tablename__ = 'cases'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=True)  # необязательное название
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)  # например, junior, middle, senior
    excalidraw_content = db.Column(db.Text, nullable=False)  # содержимое .excalidraw файла (JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Case {self.id}: {self.title or "Без названия"}>'