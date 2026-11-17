"""Cache borné par processus, sans données personnelles."""

from collections import OrderedDict
from copy import deepcopy
from threading import Lock


class ExerciseStore:
    def __init__(self, capacity: int = 1000):
        if capacity < 1:
            raise ValueError("La capacité doit être positive.")
        self.capacity = capacity
        self._items: OrderedDict[str, dict] = OrderedDict()
        self._lock = Lock()

    def add(self, exercise: dict) -> None:
        with self._lock:
            self._items[exercise["identifiant"]] = deepcopy(exercise)
            while len(self._items) > self.capacity:
                self._items.popitem(last=False)

    def get(self, identifier: str) -> dict | None:
        with self._lock:
            return deepcopy(self._items.get(identifier))
