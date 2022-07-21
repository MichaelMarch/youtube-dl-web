from flask import copy_current_request_context, stream_with_context, session
from os import path, makedirs
from threading import Thread
from yt_dlp import YoutubeDL
from queue import Queue
from app import app

from app.utils import create_sse_message

username_t = id_t = url_t = str
steps_t = Queue[str]
progress_t = dict[id_t, steps_t]

# TODO: merge these 3 into one object called User
#       _users: dict[username_t, User] = {}
_progress: dict[username_t, progress_t] = {}
_threads: dict[username_t, Thread] = {}
_queued_urls: dict[username_t, list[url_t]] = {}


def download_audio(url: str) -> None:
    username: str = session["username"]

    @copy_current_request_context
    def _download_audio() -> None:
        dir: str = path.join(app.config["YT_SAVE_PATH"], username)
        makedirs(dir, exist_ok=True)

        # TODO: I don't like this here. I would prefer not to reconstruct the template everytime.
        # TODO: currently this is unsafe acess to YT_CONFIG. After switching to json based config with required fields this should become safe
        app.config["YT_CONFIG"]["outtmpl"] = path.join(
            dir, "%(id)s %(title)s.%(ext)s")

        while username in _queued_urls and len(_queued_urls[username]) > 0:
            with YoutubeDL(app.config["YT_CONFIG"]) as ydl:
                ydl.download(_queued_urls.pop(username))

    if username not in _progress:
        _progress[username] = {}

    if username not in _queued_urls:
        _queued_urls[username] = []

    _queued_urls[username].append(url)

    if username in _threads:
        if not _threads[username].is_alive():
            del _threads[username]

    if username not in _threads:
        thread = Thread(target=_download_audio)
        thread.start()

        _threads[username] = thread


@stream_with_context
def progress_hook(data) -> None:
    if "speed" not in data or "eta" not in data:
        return

    if not data["speed"] and not data["eta"]:
        return

    info: dict[str, ] = data["info_dict"]
    id: str = info["id"]

    # data for front-end to render
    step: str = create_sse_message("downloading", {
        "id": id,
        "title": info["title"],
        # TODO: try {downloaded_bytes / total_bytes} instead
        "percent": float(str(data["_percent_str"]).strip()[:-1]),
        "speed": data["speed"],
        "eta": data["eta"]
    })

    username: str = session["username"]
    if id not in _progress[username]:
        _progress[username][id] = Queue[str]()

    _progress[username][id].put(step)


@stream_with_context
def postprocessor_hook(data) -> None:
    id: str = data["info_dict"]["id"]
    username: str = session["username"]

    status: str = data["status"]
    postprocessor: str = data["postprocessor"]

    if status == "started" and postprocessor == "ExtractAudio":
        step: str = create_sse_message("extracting", {
            "id": id,
            "status": 0
        })
        _progress[username][id].put(step)

    if status == "finished" and postprocessor == "MoveFiles":
        step: str = create_sse_message("extracting", {
            "id": id,
            "title": f"{data['info_dict']['title']}.{data['info_dict']['ext']}",
            "status": 1
        })
        _progress[username][id].put(step)
