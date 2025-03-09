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


class Crop(db.Model):
    """作物マスタモデル"""
    id = db.Column(db.Integer, primary_key=True)
    crop_name = db.Column(db.String(64), nullable=False)
    default_growing_days = db.Column(db.Integer, nullable=True)  # 標準栽培日数
    season_options = db.Column(db.String(255), nullable=True)  # 栽培適期（JSON形式で保存）
    description = db.Column(db.Text, nullable=True)
    
    # リレーションシップ
    stages = db.relationship('CropStage', backref='crop', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Crop {self.crop_name}>"


class CultivationPlan(db.Model):
    """作付け計画モデル"""
    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(db.Integer, db.ForeignKey('crop.id'), nullable=False)
    field_id = db.Column(db.Integer, db.ForeignKey('field.id'), nullable=False)
    cultivation_number = db.Column(db.Integer, default=1)  # 作付け回数
    year = db.Column(db.Integer, nullable=False)  # 栽培年
    planned_start_date = db.Column(db.Date, nullable=False)
    planned_end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='planned')  # planned, in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # リレーションシップ
    crop = db.relationship('Crop', backref=db.backref('cultivation_plans', lazy='dynamic'))
    field = db.relationship('Field', backref=db.backref('cultivation_plans', lazy='dynamic'))
    
    def __repr__(self):
        return f"<CultivationPlan {self.crop.crop_name} #{self.cultivation_number} ({self.year})>"


class Schedule(db.Model):
    """作業予定モデル（旧Taskモデルの拡張）"""
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('cultivation_plan.id'), nullable=True)
    task_name = db.Column(db.String(120), nullable=False)
    task_type = db.Column(db.String(50), nullable=True)  # 作業種別（例：播種、施肥、収穫など）
    scheduled_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    actual_date = db.Column(db.Date, nullable=True)  # 実際に作業を行った日付
    completion_status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed, postponed
    notes = db.Column(db.Text, nullable=True)  # 作業メモ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # リレーションシップ
    plan = db.relationship('CultivationPlan', backref=db.backref('schedules', lazy='dynamic'))
    
    def __repr__(self):
        return f"<Schedule {self.task_name} for Plan #{self.plan_id}>"


class CropStage(db.Model):
    """作物栽培ステージモデル"""
    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(db.Integer, db.ForeignKey('crop.id'), nullable=False)
    stage_name = db.Column(db.String(100), nullable=False)  # ステージ名（播種、苗管理、植え付け、収穫など）
    days_from_start = db.Column(db.Integer, nullable=False)  # 開始日からの日数
    description = db.Column(db.Text, nullable=True)  # 説明
    order = db.Column(db.Integer, default=0)  # 表示順
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CropStage {self.stage_name} for Crop #{self.crop_id}>"


# 以下のモデルは後続の開発フェーズで追加予定
"""
class Task(db.Model):
    # Taskモデルの名前を保持し、既存コードとの互換性のために一時的に残しておくことも検討
    # 完全に移行が終わったら削除する
    pass
"""
