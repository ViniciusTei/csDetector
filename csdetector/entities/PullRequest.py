from datetime import datetime
from typing import List

class PullRequest:
    def __init__(self, number: int, createdAt: datetime, closedAt: datetime, comments: List[str], commitCount: int, participants: List[str]) -> None:
        self._number = number
        self._createdAt = createdAt
        self._closedAt = closedAt
        self._comments = comments
        self._commitCount = commitCount
        self._participants = participants
        pass

    @property
    def number(self) -> int:
        return self._number

    @property
    def createdAt(self) -> datetime:
        return self._createdAt

    @property
    def closedAt(self) -> datetime:
        return self._closedAt

    @property
    def comments(self) -> List[str]:
        return self._comments

    @property
    def commitCount(self) -> int:
        return self._commitCount

    @property
    def participants(self) -> List[str]:
        return self._participants
