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
    def init(cls, strategy: GitHubRequestStrategy):
        cls._strategy = strategy

    @classmethod
    def numberOfPages(cls, config: Configuration) -> int:
        url = cls._strategy.urlNumberOfPages(config)
        response = cls._request.request(url)

        if response is None:
            return 1
        
        if response.links.keys():
            return int(response.links['last']['url'].partition("&page=")[-1])
        else:
            return 1

    @classmethod
    def requestPerPage(cls, config: Configuration, page: int):
        url = cls._strategy.urlRequestPerPage(config, page)
        return cls._request.request(url)
