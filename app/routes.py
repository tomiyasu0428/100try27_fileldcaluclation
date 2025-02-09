from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from app import db
from app.models import Field
import json

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    fields = Field.query.all()
    return render_template("index.html", fields=fields)


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
