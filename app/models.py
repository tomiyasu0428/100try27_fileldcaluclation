from app import db
from datetime import datetime

class Field(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    # 座標は JSON 形式の文字列として保存（例：[{ "lat": 35.6895, "lng": 139.6917 }, ...]）
    coordinates = db.Column(db.Text, nullable=False)
    area = db.Column(db.Float)  # 単位: ヘクタール

    def __repr__(self):
        return f"<Field {self.name}>"


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    field_id = db.Column(db.Integer, db.ForeignKey('field.id'), nullable=False)
    scheduled_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # リレーションシップ
    field = db.relationship('Field', backref=db.backref('tasks', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Task {self.title}>'
