from flask import Response, redirect, render_template, stream_with_context, url_for, session, request
from flask_babel import _ as translate
from os import listdir, path
from typing import Generator
from queue import Queue
from time import sleep
from app import app

from app.utils import create_sse_message, authenticate, split_filename, clear_queue
from app.yt_dl_utils import download_audio, _progress, _threads
from app.forms.login_form import LoginForm


@app.before_request
def is_user_authenticated() -> Response | None:
    if request.endpoint == "login" or "username" in session:
        return

    return redirect(url_for("login"))


@app.route("/")
def home() -> str:
    return render_template("home.html.jinja")


@app.route("/login/", methods=["GET", "POST"])
def login() -> str | Response:
    form: LoginForm = LoginForm(request.form)

    # TODO: check with postman if this logic is correct. Test both GET and POST with correct and wrong credentials
    if request.method == "GET" and not form.validate():
        if "username" not in session:
            return render_template("login.html.jinja", form=form)

        return redirect(url_for("home"))

    # POST
    username: str = request.form.get("username") or ""
    password: str = request.form.get("password") or ""

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

        while True:
            if username in _progress:
                for id in _progress[username]:
                    downloading: Queue[str] = _progress[username][id]

                    while not downloading.empty():
                        step: str = downloading.get()
                        yield step
                        downloading.task_done()
            else:
                yield create_sse_message("no_data", {})
                break
            sleep(0.1)

    return Response(get_progress(), mimetype='text/event-stream')


@app.route("/downloaded/")
def downloaded() -> Response:

    @stream_with_context
    def get_downloaded() -> Generator[str, None, None]:
        username: str = session["username"]

        dir: str = path.join(app.config["YT_SAVE_PATH"], username)
        if path.isdir(dir):
            for file in listdir(dir):
                (id, real_filename, extenstion) = split_filename(file)

                # Don't list files that are currently being processed
                if username in _progress and id in _progress[username]:
                    continue

                if extenstion in ("mp3"):
                    yield create_sse_message("downloaded", {
                        "id": id,
                        "title": real_filename
                    })
                sleep(0.1)

        yield create_sse_message("no_data", {})
    return Response(get_downloaded(), mimetype='text/event-stream')


@app.route("/finish/<id>", methods=["GET"])
def finish(id: str) -> Response:
    # variable collision (id)
    username: str = session["username"]

    if username not in _progress or id not in _progress[username]:
        return Response()

    clear_queue(_progress[username][id])

    finished: bool = True
    for id in _progress[username]:
        if not _progress[username][id].empty():
            finished = False
            break

    if finished:
        del _progress[username]
        del _threads[username]

    @stream_with_context
    def acknowledge() -> Generator[str, None, None]:
        # TODO: create_sse_message
        yield f"data: {1 if finished else 0}\n\n"

    return Response(acknowledge(), mimetype='text/event-stream')


@app.route("/download/", methods=["POST"])
def download() -> str:
    url: str | None = request.form.get("url")
    if url:
        download_audio(url)
    else:
        # some error popup
        ...

    return redirect(url_for("home"))


@app.route("/logout/")
def logout() -> Response:
    session.permanent = False
    session.pop("username", None)
    return redirect(url_for("home"))
