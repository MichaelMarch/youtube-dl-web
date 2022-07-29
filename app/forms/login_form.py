from wtforms import Form, StringField, PasswordField
from wtforms.validators import DataRequired, Length
from flask_babel import lazy_gettext as _l


class LoginForm(Form):
    username = StringField(
        _l("Username"), [DataRequired(), Length(min=4, max=25)], id="username", name="username")

    password = PasswordField(
        _l("Password"), [DataRequired()], id="password", name="password")
