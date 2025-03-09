from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from app import db
from app.models import Field, Crop, CultivationPlan, Schedule, CropStage
import json
from datetime import datetime, timedelta

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    # 直近の予定されている作業を取得
    today = datetime.now().date()
    upcoming_schedules = Schedule.query.filter(
        Schedule.scheduled_date >= today,
        Schedule.completion_status.in_(['scheduled', 'in_progress'])
    ).order_by(Schedule.scheduled_date).limit(5).all()
    
    # 圃場を取得
    fields = Field.query.all()
    
    # 作物の数を取得
    crop_count = Crop.query.count()
    
    # 作付け計画の数を取得
    plan_count = CultivationPlan.query.count()
    
    return render_template(
        "index.html", 
        upcoming_tasks=upcoming_schedules,  # テンプレートの互換性のため、変数名はそのまま
        fields=fields,
        crop_count=crop_count,
        plan_count=plan_count
    )


# フィールド（圃場）管理ルート
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


# 作物管理関連のルート
@bp.route("/crops")
def list_crops():
    crops = Crop.query.all()
    return render_template("crops/list.html", crops=crops)


@bp.route("/crops/create", methods=["GET", "POST"])
def create_crop():
    if request.method == "POST":
        crop_name = request.form.get("crop_name")
        description = request.form.get("description")
        
        crop = Crop(
            crop_name=crop_name,
            description=description
        )
        db.session.add(crop)
        db.session.commit()
        
        # ステージ情報の処理
        stage_data = {}
        for key, value in request.form.items():
            if key.startswith('stages['):
                # キー例: stages[0][stage_name]
                # インデックスとプロパティを抽出
                parts = key.split('][')  # ['stages[0', 'stage_name]']
                index = int(parts[0].split('[')[1])  # '0'
                prop = parts[1].rstrip(']')  # 'stage_name'
                
                if index not in stage_data:
                    stage_data[index] = {}
                stage_data[index][prop] = value
        
        # ステージを保存
        for index, stage_info in stage_data.items():
            if 'stage_name' in stage_info and 'days_from_start' in stage_info:
                stage = CropStage(
                    crop_id=crop.id,
                    stage_name=stage_info['stage_name'],
                    days_from_start=int(stage_info['days_from_start']),
                    description=stage_info.get('description', ''),
                    order=int(stage_info.get('order', index))
                )
                db.session.add(stage)
        
        db.session.commit()
        
        flash("作物情報が正常に登録されました。")
        return redirect(url_for("main.list_crops"))
    
    return render_template("crops/create.html")


@bp.route("/crops/<int:crop_id>/edit", methods=["GET", "POST"])
def edit_crop(crop_id):
    crop = Crop.query.get_or_404(crop_id)
    
    if request.method == "POST":
        crop.crop_name = request.form.get("crop_name")
        crop.description = request.form.get("description")
        
        # ステージ情報の処理
        stage_data = {}
        for key, value in request.form.items():
            if key.startswith('stages['):
                parts = key.split('][')  # ['stages[0', 'stage_name]']
                index = int(parts[0].split('[')[1])  # '0'
                prop = parts[1].rstrip(']')  # 'stage_name'
                
                if index not in stage_data:
                    stage_data[index] = {}
                stage_data[index][prop] = value
        
        # 既存のステージIDを取得
        stage_ids = []
        for index, stage_info in stage_data.items():
            if 'id' in stage_info and stage_info['id']:
                stage_ids.append(int(stage_info['id']))
        
        # 既存のステージで、送信されてこなかったものを削除
        for stage in crop.stages:
            if stage.id not in stage_ids:
                db.session.delete(stage)
        
        # ステージを更新または新規追加
        for index, stage_info in stage_data.items():
            if 'stage_name' in stage_info and 'days_from_start' in stage_info:
                if 'id' in stage_info and stage_info['id']:
                    # 既存ステージの更新
                    stage = CropStage.query.get(int(stage_info['id']))
                    if stage and stage.crop_id == crop.id:
                        stage.stage_name = stage_info['stage_name']
                        stage.days_from_start = int(stage_info['days_from_start'])
                        stage.description = stage_info.get('description', '')
                        stage.order = int(stage_info.get('order', index))
                else:
                    # 新規ステージの追加
                    stage = CropStage(
                        crop_id=crop.id,
                        stage_name=stage_info['stage_name'],
                        days_from_start=int(stage_info['days_from_start']),
                        description=stage_info.get('description', ''),
                        order=int(stage_info.get('order', index))
                    )
                    db.session.add(stage)
        
        db.session.commit()
        flash("作物情報が更新されました。")
        return redirect(url_for("main.list_crops"))
    
    return render_template("crops/edit.html", crop=crop)


@bp.route("/crops/<int:crop_id>/delete", methods=["POST"])
def delete_crop(crop_id):
    crop = Crop.query.get_or_404(crop_id)
    db.session.delete(crop)
    db.session.commit()
    flash("作物情報が削除されました。")
    return redirect(url_for("main.list_crops"))


# 作付け計画管理関連のルート
@bp.route("/plans")
def list_plans():
    plans = CultivationPlan.query.order_by(CultivationPlan.year.desc(), CultivationPlan.planned_start_date).all()
    return render_template("plans/list.html", plans=plans)


@bp.route("/plans/create", methods=["GET", "POST"])
def create_plan():
    if request.method == "POST":
        crop_id = request.form.get("crop_id")
        field_id = request.form.get("field_id")
        cultivation_number = request.form.get("cultivation_number")
        year = request.form.get("year")
        planned_start_date = datetime.strptime(request.form.get("planned_start_date"), "%Y-%m-%d").date()
        
        # 終了日の処理
        planned_end_date = None
        if request.form.get("planned_end_date"):
            planned_end_date = datetime.strptime(request.form.get("planned_end_date"), "%Y-%m-%d").date()
        else:
            # 作物の栽培ステージから終了日を計算
            crop = Crop.query.get(crop_id)
            if crop and crop.stages:
                # 収穫ステージを探すか、それがなければ最後のステージを使用
                harvest_stage = None
                sorted_stages = sorted(crop.stages, key=lambda s: s.days_from_start)
                
                for stage in sorted_stages:
                    if stage.stage_name == "収穫":
                        harvest_stage = stage
                        break
                
                if harvest_stage:
                    # 収穫ステージがあれば、その日数を使用
                    planned_end_date = planned_start_date + timedelta(days=harvest_stage.days_from_start)
                elif sorted_stages:
                    # 収穫ステージがなければ、最後のステージの日数を使用
                    last_stage = sorted_stages[-1]
                    planned_end_date = planned_start_date + timedelta(days=last_stage.days_from_start + 7)  # 最後のステージからさらに1週間
        
        plan = CultivationPlan(
            crop_id=crop_id,
            field_id=field_id,
            cultivation_number=cultivation_number,
            year=year,
            planned_start_date=planned_start_date,
            planned_end_date=planned_end_date,
            status='planned'
        )
        db.session.add(plan)
        db.session.commit()
        
        # 作物の栽培ステージに基づいて作業予定を自動生成
        crop = Crop.query.get(crop_id)
        if crop and crop.stages:
            # 栽培ステージをdaysの昇順でソート
            sorted_stages = sorted(crop.stages, key=lambda s: s.days_from_start)
            
            # 各ステージに対して作業予定を作成
            for stage in sorted_stages:
                # ステージの開始日を計算（開始日 + ステージの日数）
                stage_date = planned_start_date + timedelta(days=stage.days_from_start)
                
                # ステージ名をタスク名として設定
                task_name = f"{stage.stage_name}"
                
                # 作業予定を作成して保存
                schedule = Schedule(
                    plan_id=plan.id,
                    task_name=task_name,
                    task_type=stage.stage_name,  # タスクタイプにもステージ名を使用
                    scheduled_date=stage_date,
                    notes=stage.description or f"{crop.crop_name}の{stage.stage_name}作業",
                    completion_status='scheduled'
                )
                db.session.add(schedule)
            
            db.session.commit()
            flash(f"作付け計画と{len(sorted_stages)}件の作業予定が正常に作成されました。")
        else:
            flash("作付け計画が正常に作成されました。栽培ステージが登録されていないため、作業予定は自動生成されませんでした。")
            
        return redirect(url_for("main.list_plans"))
    
    crops = Crop.query.all()
    fields = Field.query.all()
    current_year = datetime.now().year
    years = range(current_year - 1, current_year + 3)  # 前年から2年後まで
    
    return render_template("plans/create.html", crops=crops, fields=fields, years=years)


@bp.route("/plans/<int:plan_id>/edit", methods=["GET", "POST"])
def edit_plan(plan_id):
    plan = CultivationPlan.query.get_or_404(plan_id)
    
    if request.method == "POST":
        old_start_date = plan.planned_start_date
        old_crop_id = plan.crop_id
        
        plan.crop_id = request.form.get("crop_id")
        plan.field_id = request.form.get("field_id")
        plan.cultivation_number = request.form.get("cultivation_number")
        plan.year = request.form.get("year")
        plan.planned_start_date = datetime.strptime(request.form.get("planned_start_date"), "%Y-%m-%d").date()
        
        if request.form.get("planned_end_date"):
            plan.planned_end_date = datetime.strptime(request.form.get("planned_end_date"), "%Y-%m-%d").date()
        
        plan.status = request.form.get("status")
        
        # 作付け計画を保存
        db.session.commit()
        
        # 作物が変更された、または開始日が変更された場合、作業予定を再生成する
        if int(plan.crop_id) != old_crop_id or plan.planned_start_date != old_start_date:
            regenerate_schedules = request.form.get("regenerate_schedules") == "on"
            
            if regenerate_schedules:
                # 既存の作業予定を削除
                Schedule.query.filter_by(plan_id=plan.id).delete()
                
                # 作物の栽培ステージに基づいて作業予定を再生成
                crop = Crop.query.get(plan.crop_id)
                if crop and crop.stages:
                    # 栽培ステージをdaysの昇順でソート
                    sorted_stages = sorted(crop.stages, key=lambda s: s.days_from_start)
                    
                    # 各ステージに対して作業予定を作成
                    for stage in sorted_stages:
                        # ステージの開始日を計算（開始日 + ステージの日数）
                        stage_date = plan.planned_start_date + timedelta(days=stage.days_from_start)
                        
                        # ステージ名をタスク名として設定
                        task_name = f"{stage.stage_name}"
                        
                        # 作業予定を作成して保存
                        schedule = Schedule(
                            plan_id=plan.id,
                            task_name=task_name,
                            task_type=stage.stage_name,
                            scheduled_date=stage_date,
                            notes=stage.description or f"{crop.crop_name}の{stage.stage_name}作業",
                            completion_status='scheduled'
                        )
                        db.session.add(schedule)
                    
                    db.session.commit()
                    flash(f"作付け計画が更新され、{len(sorted_stages)}件の作業予定が再生成されました。")
                else:
                    flash("作付け計画が更新されました。栽培ステージが登録されていないため、作業予定は自動生成されませんでした。")
            else:
                flash("作付け計画が更新されました。")
        else:
            flash("作付け計画が更新されました。")
            
        return redirect(url_for("main.list_plans"))
    
    crops = Crop.query.all()
    fields = Field.query.all()
    current_year = datetime.now().year
    years = range(current_year - 1, current_year + 3)
    
    return render_template("plans/edit.html", plan=plan, crops=crops, fields=fields, years=years)


@bp.route("/plans/<int:plan_id>/delete", methods=["POST"])
def delete_plan(plan_id):
    plan = CultivationPlan.query.get_or_404(plan_id)
    db.session.delete(plan)
    db.session.commit()
    flash("作付け計画が削除されました。")
    return redirect(url_for("main.list_plans"))


# 作業予定管理関連のルート（旧タスク管理を置き換え）
@bp.route("/schedules")
def list_schedules():
    schedules = Schedule.query.order_by(Schedule.scheduled_date).all()
    plans = CultivationPlan.query.all()
    return render_template("schedules/list.html", schedules=schedules, plans=plans)


@bp.route("/schedules/create", methods=["GET", "POST"])
def create_schedule():
    if request.method == "POST":
        task_name = request.form.get("task_name")
        task_type = request.form.get("task_type")
        plan_id = request.form.get("plan_id") or None  # 空文字列の場合はNoneに変換
        field_id = request.form.get("field_id") or None  # 空文字列の場合はNoneに変換
        scheduled_date = datetime.strptime(request.form.get("scheduled_date"), "%Y-%m-%d").date()
        notes = request.form.get("notes")
        
        # Scheduleオブジェクトを作成
        schedule = Schedule(
            task_name=task_name,
            task_type=task_type,
            plan_id=plan_id,
            scheduled_date=scheduled_date,
            start_time=None,  # 開始時間と終了時間は使用しない
            end_time=None,    # 開始時間と終了時間は使用しない
            notes=notes,
            completion_status='scheduled'
        )
        
        # 作付け計画がなく、圃場が選択されている場合の処理
        if not plan_id and field_id:
            # field_idをScheduleモデルに直接保存する代わりに、notesに追記
            field = Field.query.get(field_id)
            if field:
                if schedule.notes:
                    schedule.notes += f"\n\n圃場: {field.name}"
                else:
                    schedule.notes = f"圃場: {field.name}"
        
        db.session.add(schedule)
        db.session.commit()
        
        flash("作業予定が正常に作成されました。")
        return redirect(url_for("main.list_schedules"))
    
    plans = CultivationPlan.query.all()
    fields = Field.query.all()  # 圃場の一覧を取得
    # 一般的な作業タイプのリスト
    task_types = ["耕起", "整地", "播種", "定植", "施肥", "灌水", "除草", "病害虫防除", "収穫", "その他"]
    
    return render_template("schedules/create.html", plans=plans, fields=fields, task_types=task_types)


@bp.route("/schedules/<int:schedule_id>/edit", methods=["GET", "POST"])
def edit_schedule(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    
    if request.method == "POST":
        schedule.task_name = request.form.get("task_name")
        schedule.task_type = request.form.get("task_type")
        schedule.plan_id = request.form.get("plan_id")
        schedule.scheduled_date = datetime.strptime(request.form.get("scheduled_date"), "%Y-%m-%d").date()
        schedule.notes = request.form.get("notes")
        
        # 時間フィールドの処理
        if request.form.get("start_time"):
            schedule.start_time = datetime.strptime(request.form.get("start_time"), "%H:%M").time()
        else:
            schedule.start_time = None
            
        if request.form.get("end_time"):
            schedule.end_time = datetime.strptime(request.form.get("end_time"), "%H:%M").time()
        else:
            schedule.end_time = None
        
        # 実施日の処理
        if request.form.get("actual_date"):
            schedule.actual_date = datetime.strptime(request.form.get("actual_date"), "%Y-%m-%d").date()
        else:
            schedule.actual_date = None
            
        schedule.completion_status = request.form.get("completion_status")
        
        db.session.commit()
        flash("作業予定が更新されました。")
        return redirect(url_for("main.list_schedules"))
    
    plans = CultivationPlan.query.all()
    task_types = ["耕起", "整地", "播種", "定植", "施肥", "灌水", "除草", "病害虫防除", "収穫", "その他"]
    statuses = [("scheduled", "予定"), ("in_progress", "進行中"), ("completed", "完了"), ("postponed", "延期")]
    
    return render_template("schedules/edit.html", schedule=schedule, plans=plans, task_types=task_types, statuses=statuses)


@bp.route("/schedules/<int:schedule_id>/delete", methods=["POST"])
def delete_schedule(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    db.session.delete(schedule)
    db.session.commit()
    flash("作業予定が削除されました。")
    return redirect(url_for("main.list_schedules"))


# カレンダー表示のルート（互換性のために残す）
@bp.route("/calendar")
def calendar():
    return render_template("calendar/view.html")


# 新しいカレンダーAPI（作業予定の取得）
@bp.route("/api/schedules")
def get_schedules():
    """作業予定をJSON形式で返すAPIエンドポイント - カレンダー表示用"""
    schedules = Schedule.query.all()
    events = []
    
    for schedule in schedules:
        # 作付け計画情報を取得
        plan = schedule.plan
        
        # 作付け計画、作物、圃場の情報を初期化
        crop_name = "未設定"
        field_name = "未設定"
        cultivation_number = 0
        
        # 作付け計画がある場合は関連情報を取得
        if plan:
            if plan.crop:
                crop_name = plan.crop.crop_name
            if plan.field:
                field_name = plan.field.name
            cultivation_number = plan.cultivation_number
        
        # 開始/終了時間の処理
        start = schedule.scheduled_date.isoformat()
        end = schedule.scheduled_date.isoformat()
        
        if schedule.start_time:
            start = f"{schedule.scheduled_date.isoformat()}T{schedule.start_time.isoformat()}"
        if schedule.end_time:
            end = f"{schedule.scheduled_date.isoformat()}T{schedule.end_time.isoformat()}"
        elif schedule.start_time:  # 終了時間がなく開始時間がある場合は1時間後を終了時間とする
            end = f"{schedule.scheduled_date.isoformat()}T{schedule.start_time.isoformat()}"
        else:  # 開始時間も終了時間もない場合は終日イベント
            end = (schedule.scheduled_date + timedelta(days=1)).isoformat()
        
        # ステータスに応じた色設定
        color = ""
        if schedule.completion_status == "completed":
            color = "#28a745"  # 完了：緑
        elif schedule.completion_status == "in_progress":
            color = "#ffc107"  # 進行中：黄色
        elif schedule.completion_status == "postponed":
            color = "#dc3545"  # 延期：赤
        else:
            color = "#007bff"  # 予定：青
        
        # タスク種別によって色を変える（オプション）
        if schedule.task_type == "播種":
            color = "#6610f2"  # 紫
        elif schedule.task_type == "収穫":
            color = "#fd7e14"  # オレンジ
        
        # タイトルの設定
        title = schedule.task_name
        if plan:
            title = f"{schedule.task_name} - {crop_name} 第{cultivation_number}作 - {field_name}"
        
        event = {
            "id": schedule.id,
            "title": title,
            "start": start,
            "end": end,
            "url": url_for("main.edit_schedule", schedule_id=schedule.id),
            "backgroundColor": color,
            "borderColor": color,
            "textColor": "#fff"
        }
        
        # 追加情報の設定
        event["extendedProps"] = {
            "task_type": schedule.task_type
        }
        
        # 作付け計画がある場合は追加情報を拡張
        if plan:
            event["extendedProps"].update({
                "crop": crop_name,
                "field": field_name,
                "cultivation_number": cultivation_number
            })
        
        events.append(event)
    
    return jsonify(events)


# 古いTaskモデルのルートとAPIエンドポイント（互換性のために一時的に残す）
@bp.route("/tasks")
def list_tasks():
    """古いタスク一覧ルートを新しいスケジュール一覧ルートにリダイレクト"""
    return redirect(url_for("main.list_schedules"))

@bp.route("/tasks/create", methods=["GET", "POST"])
def create_task():
    """古いタスク作成ルートを新しいスケジュール作成ルートにリダイレクト"""
    return redirect(url_for("main.create_schedule"))

@bp.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id):
    """古いタスク編集ルートはサポートしない（データモデルが変わったため）"""
    flash("タスク管理が作業予定管理に移行しました。作業予定一覧から編集してください。")
    return redirect(url_for("main.list_schedules"))

@bp.route("/api/tasks")
def get_tasks():
    """古いタスクAPIをリダイレクト"""
    return get_schedules()  # 新しいAPIを呼び出す
