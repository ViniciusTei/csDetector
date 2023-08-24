from abc import ABC, abstractmethod

from csdetector import Configuration

class GitHubRequestStrategy(ABC):

    @staticmethod
    @abstractmethod
    def requestUrl(config: Configuration, sha: str):
        pass
