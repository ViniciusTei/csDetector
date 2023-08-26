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
