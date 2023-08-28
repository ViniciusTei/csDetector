from csdetector import Configuration
from csdetector.github.GitHubRequestStrategy import GitHubRequestStrategy

class GitHubRequestReleases(GitHubRequestStrategy):
    @staticmethod
    def urlNumberOfPages(config: Configuration):
        return "https://api.github.com/repos/{}/{}/releases".format(config.repositoryOwner, config.repositoryName)

    @staticmethod
    def urlRequestPerPage(config: Configuration, page: int) -> str:
        return "https://api.github.com/repos/{}/{}/releases?page={}&per_page=100".format(config.repositoryOwner, config.repositoryName, page)

    @staticmethod
    def urlRequestComments(config: Configuration, number: int):
        pass

