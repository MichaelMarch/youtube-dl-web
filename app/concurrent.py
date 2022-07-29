from typing import TypeVar
from threading import Lock

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class ConcurrentDict(dict[_KT, _VT]):
    def __init__(self) -> None:
        self.lock = Lock()
        super().__init__()

    def __setitem__(self, __k: _KT, __v: _VT) -> None:
        with self.lock:
            return super().__setitem__(__k, __v)

    def __getitem__(self, __k: _KT) -> _VT:
        with self.lock:
            return super().__getitem__(__k)

    def __delitem__(self, __v: _KT) -> None:
        with self.lock:
            return super().__delitem__(__v)

    def __len__(self) -> int:
        with self.lock:
            return super().__len__()

    def __contains__(self, __o: object) -> bool:
        with self.lock:
            return super().__contains__(__o)

    def copy(self) -> dict[_KT, _VT]:
        with self.lock:
            return super().copy()

    def keys(self):
        with self.lock:
            return super().keys()

    def update(self, __m) -> None:
        with self.lock:
            super().update(__m)
