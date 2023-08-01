from datetime import datetime
from .entity import Entity

class IssueEntity(Entity):
    def __init__(self, number: int, createdAt: datetime, closedAt: datetime, comments: list[str], participants: list[str]) -> None:
        super().__init__()
        self._number = number
        self._createdAt = createdAt
        self._closedAt = closedAt
        self._comments = comments
        self._participants = participants
        
    def toDict(self):
        issue = {
            "number": self._number,
            "createdAt": self._createdAt,
            "closedAt": self._closedAt,
            "comments": self._comments,
            "participants": self._participants,
        }
        return issue

