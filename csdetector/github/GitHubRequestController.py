from typing import List
from csdetector import Configuration
from csdetector.github.GitHubRequestHelper import GitHubRequestHelper
from csdetector.github.GitHubRequestStrategy import GitHubRequestStrategy

class GitHubRequestController:
    _request: GitHubRequestHelper
    _strategy: GitHubRequestStrategy

    @classmethod
    def __init__(cls, config: Configuration) -> None:
        cls._request = GitHubRequestHelper()
        cls._request.init_tokens(config)
        pass

    @property
    def request(self):
        return self._request

    @classmethod
    def setStrategy(cls, strategy):
        cls._strategy = strategy
        pass

    @classmethod
    def requestComments(cls, urlComments: str) -> List[str]:
        comments = []
        responseComments = cls._request.request(urlComments)
        if responseComments is not None:
            for comment in responseComments.json():
                comments.append(comment["body"])

        return comments

    @classmethod
    def requestTotalCommits(cls, urlCommits: str) -> int:
        responseCommits = cls._request.request(urlCommits)
        if responseCommits is not None:
            return len(responseCommits.json())

        return 0

    @classmethod
    def requestParticipants(cls, config: Configuration, number: int) -> List[str]:
        url = "https://api.github.com/repos/{}/{}/issues/{}/events".format(
            config.repositoryOwner, config.repositoryName, number
        )
        participants = []
        responseParticipants = cls._request.request(url)
        if responseParticipants is not None:
            for participant in responseParticipants.json():
                if participant is None or participant["actor"] is None or participant["actor"]["login"] is None:
                    login = None
                else:
                    login = participant["actor"]["login"]

                if login is not None and login not in participants:
                    participants.append(login)

        return participants

    @classmethod
    def numberOfPages(cls, config: Configuration) -> int:
        url = cls._strategy.urlNumberOfPages(config)
        response = cls._request.request(url)

        if response is None:
            return 1

        try:
            if response.links.keys():
                return int(response.links['last']['url'].partition("&page=")[-1])
            else:
                return 1
        except ValueError:
            return 1

    @classmethod
    def requestPerPage(cls, config: Configuration, page: int):
        url = cls._strategy.urlRequestPerPage(config, page)
        return cls._request.request(url)
