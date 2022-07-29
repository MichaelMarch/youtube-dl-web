from os import listdir, makedirs, path
from copy import deepcopy, copy
from typing import Generator
from threading import Thread
from yt_dlp import YoutubeDL
from queue import Queue
from time import sleep

from app.utils import create_sse_message, split_filename
from app.concurrent import ConcurrentDict

# TODO: file based config, JSON preferably
_base_yt_config: dict[str, ] = {
    "format": "bestaudio/best",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192"
    }],
    "quiet": True,
    "noprogress": True,
    "ffmpeg_location": r"D:\ffmpeg\bin"
}


class User:
    def __init__(self, username: str, save_dir: str) -> None:
        self.progress = ConcurrentDict[str, Queue[str]]()
        self.pending_downloads = ConcurrentDict[str, str]()
        self.thread = Thread()

        self.save_dir = save_dir
        self.username = username

        self._init()

    def _init(self) -> None:
        # TODO: test if copy is enough or is it ever needed
        self.yt_config: dict[str, ] = deepcopy(_base_yt_config)

        self.yt_config.update(
            outtmpl=path.join(self.save_dir, "%(id)s %(title)s.%(ext)s"),
            progress_hooks=[self._download_progress_hook],
            postprocessor_hooks=[self._extract_progress_hook],
            ratelimit=100_000
        )

    def enqueue_download(self, url: str) -> None:
        if len(url) == 1:
            print(self.progress)
            print(self.pending_downloads)
            return

        def _download_audio() -> None:
            # user might delete the save directory so it needs to be created before each download call
            # TODO: catch exceptions
            makedirs(self.save_dir, exist_ok=True)

            while self.pending_downloads:
                ids: list[str] = []

                for id in self.pending_downloads.keys():
                    self.progress[id] = Queue()
                    ids.append(id)

                with YoutubeDL(self.yt_config) as ydl:
                    ydl.download(ids)

                for id in ids:
                    del self.pending_downloads[id]

        self.pending_downloads.update(self._extract_info(url))

        if not self.thread.is_alive():
            self.thread = Thread(target=_download_audio)
            self.thread.start()

    def _extract_info(self, url: str) -> dict[str, str]:
        with YoutubeDL({"quiet": True, "noprogress": True, "verbose": False, "prefer_insecure": True}) as ydl:
            info = ydl.extract_info(url, download=False, process=False)

        return {info["id"]: info["title"]}

    def _download_progress_hook(self, data: dict[str, ]) -> None:
        # TODO: maybe front-end should check do the check instead
        if "speed" not in data or "eta" not in data:
            return
        # TODO: maybe front-end should check do the check instead
        if not data["speed"] or not data["eta"]:
            return

        info = data["info_dict"]
        id: str = info["id"]

        step = create_sse_message("downloading", {
            "id": id,
            "title": info["title"],
            "percent": data["_percent_str"].strip(),
            "speed": data["speed"],
            "eta": data["eta"]
        })

        self.progress[id].put(step)

    def _extract_progress_hook(self, data) -> None:
        id: str = data["info_dict"]["id"]

        status: str = data["status"]
        postprocessor: str = data["postprocessor"]

        if status == "started" and postprocessor == "ExtractAudio":
            step: str = create_sse_message("extracting", {
                "id": id,
                "status": 0
            })
            self.progress[id].put(step)

        if status == "finished" and postprocessor == "MoveFiles":
            step: str = create_sse_message("extracting", {
                "id": id,
                "title": f"{data['info_dict']['title']}.{data['info_dict']['ext']}",
                "status": 1
            })
            self.progress[id].put(step)
            self.progress[id].put("done")

    def get_progress(self) -> Generator[str, None, None]:
        if path.isdir(self.save_dir):
            for filename in listdir(self.save_dir):
                id, real_filename, extenstion = split_filename(filename)

                # Don't list files that are currently being processed
                if id in self.progress:
                    continue

                if extenstion in ("mp3"):
                    print(filename)
                    yield create_sse_message("downloaded", {
                        "id": id,
                        "title": real_filename
                    })
                sleep(0.1)

        if self.pending_downloads:
            yield create_sse_message("queued", self.pending_downloads)

        while self.progress or self.pending_downloads:
            for id in copy(self.progress):
                steps: Queue[str] = self.progress[id]

                while not steps.empty():
                    step = steps.get()

                    if step:
                        yield step
                        steps.task_done()
                    else:
                        del self.progress[id]
            sleep(0.1)

        yield create_sse_message("no_data", {})

    # def get_downloaded(self) -> Generator[str, None, None]:
    #     if path.isdir(self.save_dir):
    #         for filename in listdir(self.save_dir):
    #             id, real_filename, extenstion = split_filename(filename)

    #             # Don't list files that are currently being processed
    #             if id in self.progress:
    #                 continue

    #             if extenstion in ("mp3"):
    #                 yield create_sse_message("downloaded", {
    #                     "id": id,
    #                     "title": real_filename
    #                 })
    #             sleep(0.1)

    #     yield create_sse_message("no_data", {})
