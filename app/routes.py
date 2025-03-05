from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from app import db
from app.models import Field, Task
import json
from datetime import datetime, timedelta

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    # 直近の予定されているタスクを取得
    today = datetime.now().date()
    upcoming_tasks = Task.query.filter(
        Task.scheduled_date >= today,
        Task.status.in_(['scheduled', 'in_progress'])
    ).order_by(Task.scheduled_date).limit(5).all()
    
    # 圃場を取得
    fields = Field.query.all()
    
    return render_template("index.html", upcoming_tasks=upcoming_tasks, fields=fields)


@bp.route("/register", methods=["GET", "POST"])
def register_field():
    if request.method == "POST":
        name = request.form.get("name")
        coordinates = request.form.get("coordinates")  # JSON形式の文字列
        area = request.form.get("area")  # JSで計算された面積（ha単位）
        if not name or not coordinates or not area:
            flash("全てのフィールドを入力してください。")
            return redirect(url_for("main.register_field"))

        field = Field(name=name, coordinates=coordinates, area=float(area))
        db.session.add(field)
        db.session.commit()
        flash("農地情報が保存されました。")
        return redirect(url_for("main.index"))

    return render_template("field_register.html")


@bp.route("/edit/<int:field_id>", methods=["GET", "POST"])
def edit_field(field_id):
    field = Field.query.get_or_404(field_id)
    if request.method == "POST":
        field.name = request.form.get("name")
        field.coordinates = request.form.get("coordinates")
        field.area = float(request.form.get("area"))
        db.session.commit()
        flash("農地情報が更新されました。")
        return redirect(url_for("main.index"))
    return render_template("field_edit.html", field=field)


@bp.route("/delete/<int:field_id>", methods=["POST"])
def delete_field(field_id):
    field = Field.query.get_or_404(field_id)
    db.session.delete(field)
    db.session.commit()
    flash("農地情報が削除されました。")
    return redirect(url_for("main.index"))


# オプション：農地データのエクスポート API（CSV/GeoJSON形式への変換は別途実装可）
@bp.route("/export", methods=["GET"])
def export_fields():
    fields = Field.query.all()
    fields_data = []
    for field in fields:
        fields_data.append(
            {
                "id": field.id,
                "name": field.name,
                "coordinates": json.loads(field.coordinates),
                "area": field.area,
            }
        )
    return jsonify(fields_data)


# 圃場一覧ページ
@bp.route("/fields")
def field_list():
    fields = Field.query.all()
    return render_template("field_list.html", fields=fields)


# タスク管理関連のルート
@bp.route("/tasks")
def list_tasks():
    tasks = Task.query.order_by(Task.scheduled_date).all()
    fields = Field.query.all()
    return render_template("tasks/list.html", tasks=tasks, fields=fields)


@bp.route("/tasks/create", methods=["GET", "POST"])
def create_task():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        field_id = request.form.get("field_id")
        scheduled_date = datetime.strptime(request.form.get("scheduled_date"), "%Y-%m-%d").date()
        
        # 時間フィールドの処理（なければNone）
        start_time = None
        if request.form.get("start_time"):
            start_time = datetime.strptime(request.form.get("start_time"), "%H:%M").time()
        
        end_time = None
        if request.form.get("end_time"):
            end_time = datetime.strptime(request.form.get("end_time"), "%H:%M").time()
        
        task = Task(
            title=title,
            description=description,
            field_id=field_id,
            scheduled_date=scheduled_date,
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(task)
        db.session.commit()
        
        flash("タスクが正常に作成されました。")
        return redirect(url_for("main.list_tasks"))
    
    fields = Field.query.all()
    return render_template("tasks/create.html", fields=fields)


@bp.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    if request.method == "POST":
        task.title = request.form.get("title")
        task.description = request.form.get("description")
        task.field_id = request.form.get("field_id")
        task.scheduled_date = datetime.strptime(request.form.get("scheduled_date"), "%Y-%m-%d").date()
        
        # 時間フィールドの処理
        if request.form.get("start_time"):
            task.start_time = datetime.strptime(request.form.get("start_time"), "%H:%M").time()
        else:
            task.start_time = None
            
        if request.form.get("end_time"):
            task.end_time = datetime.strptime(request.form.get("end_time"), "%H:%M").time()
        else:
            task.end_time = None
            
        task.status = request.form.get("status")
        
        db.session.commit()
        flash("タスクが更新されました。")
        return redirect(url_for("main.list_tasks"))
    
    fields = Field.query.all()
    return render_template("tasks/edit.html", task=task, fields=fields)


@bp.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash("タスクが削除されました。")
    return redirect(url_for("main.list_tasks"))


# カレンダー表示のルート
@bp.route("/calendar")
def calendar():
    return render_template("calendar/view.html")


@bp.route("/api/tasks")
def get_tasks():
    """タスクをJSON形式で返すAPIエンドポイント - カレンダー表示用"""
    tasks = Task.query.all()
    events = []
    
    for task in tasks:
        # 開始/終了時間の処理
        start = task.scheduled_date.isoformat()
        end = task.scheduled_date.isoformat()
        
        if task.start_time:
            start = f"{task.scheduled_date.isoformat()}T{task.start_time.isoformat()}"
        if task.end_time:
            end = f"{task.scheduled_date.isoformat()}T{task.end_time.isoformat()}"
        elif task.start_time:  # 終了時間がなく開始時間がある場合は1時間後を終了時間とする
            end = f"{task.scheduled_date.isoformat()}T{task.start_time.isoformat()}"
        else:  # 開始時間も終了時間もない場合は終日イベント
            end = (task.scheduled_date + timedelta(days=1)).isoformat()
        
        # ステータスに応じた色設定
        color = ""
        if task.status == "completed":
            color = "#28a745"  # 完了：緑
        elif task.status == "in_progress":
            color = "#ffc107"  # 進行中：黄色
        else:
            color = "#007bff"  # 予定：青
        
        events.append({
            "id": task.id,
            "title": f"{task.title} - {task.field.name}",
            "start": start,
            "end": end,
            "url": url_for("main.edit_task", task_id=task.id),
            "backgroundColor": color,
            "borderColor": color,
            "textColor": "#fff"
        })
    
    return jsonify(events)
