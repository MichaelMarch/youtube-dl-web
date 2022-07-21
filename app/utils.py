from json import dumps as to_json_str
from queue import Queue
from flask import request, session
from flask_babel import Babel
from platform import system
from uuid import uuid1
from app import app


if not system() == "Windows":
    from simplepam import authenticate as pam_authenticate

babel: Babel = Babel(app)
# TODO: dict[username, Thread] assign thread to a user
threads = []


def create_sse_message(event_name: str, data: dict) -> str:
    """Creates Server-Sent event message

    Args:
        event_name (str): The name of the event. Can be anything 
        data (str): The data to be sent.

    Returns:
        str: Server-Sent event message in the following format:\n
             "id: {id}\\nevent: {event_name}\\ndata: {data}\\n\\n"
    """

    # Note: The format must stay as it is otherwise everything will break!
    return f"""id: {uuid1()}
event: {event_name}
data: {to_json_str(data)}

"""


@babel.localeselector
def get_locale() -> str:
    if "locale" not in session:
        session["locale"] = request.accept_languages.best_match(
            ("en", "pl"), "en")

    return session["locale"]


def authenticate(username: str, password: str) -> bool:
    if app.config["DEBUG"] and system() == "Windows":
        return (username == app.config["TEST_USER_NAME"] and password == app.config["TEST_USER_PASSWORD"]) or \
            (username == app.config["TEST_USER_NAME2"]
             and password == app.config["TEST_USER_PASSWORD2"])

    return pam_authenticate(username, password)


def split_filename(filename: str) -> tuple[str, str, str]:
    sep_index: int = filename.find(' ')
    return (filename[:sep_index], filename[sep_index:], filename[filename.rfind('.') + 1:].lower())


def clear_queue(queue: Queue) -> None:
    with queue.mutex:
        queue.queue.clear()
        queue.all_tasks_done.notify_all()
        queue.unfinished_tasks = 0
