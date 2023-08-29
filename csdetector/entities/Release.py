class Release:
    def __init__(self, name, createdAt, author):
        self._name = name
        self._createdAt = createdAt
        self._author = author

    @property
    def name(self):
        return self._name

    @property
    def createdAt(self):
        return self._createdAt

    @property
    def author(self):
        return self._author


