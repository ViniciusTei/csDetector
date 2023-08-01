from .entity import Entity
import datetime

class PullRequestEntity(Entity):
    def __init__(self, number: int, createdAt: datetime.datetime, closedAt: datetime.datetime, comments: list[str], commitCount: int, participants: list[str]) -> None:
        super().__init__()
        self._number = number
        self._createdAt = createdAt
        self._closedAt = closedAt
        self._comments = comments
        self._commitCount = commitCount
        self._participants = participants

    def toDict(self):
        pr = {
            "number": self._number,
            "createdAt": self._createdAt,
            "closedAt": self._closedAt,
            "comments": self._comments,
            "commitCount": self._commitCount,
            "participants": self._participants
        }
        return pr

