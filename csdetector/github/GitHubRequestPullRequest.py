from csdetector import Configuration
from csdetector.github.GitHubRequestStrategy import GitHubRequestStrategy

class GitHubRequestPullRequest(GitHubRequestStrategy):
    @staticmethod
    def urlNumberOfPages(config: Configuration) -> str:
        return "https://api.github.com/repos/{}/{}/pulls?state=all&per_page=100&page=1".format(
            config.repositoryOwner, config.repositoryName
        )

    @staticmethod
    def urlRequestPerPage(config: Configuration, page: int) -> str:
        return "https://api.github.com/repos/{}/{}/pulls?state=all&per_page=100&page={}".format(
            config.repositoryOwner, config.repositoryName, page
        )

    @staticmethod
    def urlRequestComments(config: Configuration, number: int) -> str:
        return "https://api.github.com/repos/{}/{}/pulls/{}/comments?per_page=100&page=1".format(
            config.repositoryOwner, config.repositoryName, number
        )
