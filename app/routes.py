from flask import Response, redirect, render_template, stream_with_context, url_for, session, request
from flask_babel import _ as translate
from typing import Generator
from os import path
from app import app

from app.utils import authenticate
from app.forms.login_form import LoginForm
from app.models.user import User


_users: dict[str, User] = {}


@app.before_request
def is_user_authenticated() -> Response | None:
    if "username" in session:
        username: str = session["username"]
        if username not in _users:
            _users[username] = User(
                username,
                save_dir=path.join(app.config["YT_SAVE_PATH"], username)
            )

        return None

    if request.endpoint == "login":
        return None

    return redirect(url_for("login"))


@app.route("/")
def home() -> str:
    return render_template("home.html.jinja")


@app.route("/login/", methods=["GET", "POST"])
def login() -> str | Response:
    form = LoginForm(request.form)

    if request.method == "GET" or not form.validate():
        if "username" not in session:
            return render_template("login.html.jinja", form=form)

        return redirect(url_for("home"))

    # POST
    username = request.form.get("username") or ""
    password = request.form.get("password") or ""

    if authenticate(username, password):
        session["username"] = username
        session.permanent = True
        return redirect(url_for("home"))

    return render_template("login.html.jinja", errors=[("warning", translate("Wrong username or password!"))], form=form)


@app.route("/progress/")
def progress() -> Response:

    @stream_with_context
    def get_progress() -> Generator[str, None, None]:
        username: str = session["username"]

        return _users[username].get_progress()

    return Response(get_progress(), mimetype="text/event-stream")


# @app.route("/downloaded/")
# def downloaded() -> Response:

#     @stream_with_context
#     def get_downloaded() -> Generator[str, None, None]:
#         username: str = session["username"]

#         return _users[username].get_downloaded()

#     return Response(get_downloaded(), mimetype='text/event-stream')


@app.route("/download/", methods=["POST"])
def download() -> str:
    url: str | None = request.form.get("url")
    if url:
        username: str = session["username"]
        _users[username].enqueue_download(url)
    else:
        # some error popup
        ...

    return redirect(url_for("home"))


@app.route("/logout/")
def logout() -> Response:
    session.permanent = False
    session.pop("username", None)
    return redirect(url_for("home"))
