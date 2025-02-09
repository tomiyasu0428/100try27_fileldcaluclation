from app import db

class Field(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    # 座標は JSON 形式の文字列として保存（例：[{ "lat": 35.6895, "lng": 139.6917 }, ...]）
    coordinates = db.Column(db.Text, nullable=False)
    area = db.Column(db.Float)  # 単位: ヘクタール

    def __repr__(self):
        return f"<Field {self.name}>"
