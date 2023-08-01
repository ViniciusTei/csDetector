from datetime import datetime
from .entity import Entity

class ReleaseEntity(Entity):
    def __init__(self, name: str, createdAt: datetime, author: str) -> None:
        super().__init__()
        self._name = name
        self._createAt = createdAt
        self._author = author

    def toDict(self):
        release = {
            "name": self._name,
            "createdAt": self._createAt,
            "author": self._author
        }
        return release
