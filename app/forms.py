from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired


class FieldForm(FlaskForm):
    name = StringField("農地名", validators=[DataRequired()])
    coordinates = TextAreaField("境界情報 (JSON形式)", validators=[DataRequired()])
    submit = SubmitField("保存")
