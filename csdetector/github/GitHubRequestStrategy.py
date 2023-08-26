from abc import ABC, abstractmethod

from csdetector import Configuration

class GitHubRequestStrategy(ABC):

    @staticmethod
    @abstractmethod
    def urlNumberOfPages(config: Configuration) -> str:
        pass

    @staticmethod
    @abstractmethod
    def urlRequestPerPage(config: Configuration, page: int) -> str:
        pass

