from wtforms import Form, StringField, PasswordField, validators
from flask_babel import lazy_gettext as _l

class LoginForm(Form):
    username: StringField = StringField(
        _l("Username"), [validators.DataRequired(), validators.Length(min=4, max=25)], id="username", name="username")
    password: PasswordField = PasswordField(
        _l("Password"), [validators.DataRequired()], id="password", name="password")
