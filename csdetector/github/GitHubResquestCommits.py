from csdetector import Configuration
from csdetector.github.GitHubRequestStrategy import GitHubRequestStrategy

class GitHubRequestCommits(GitHubRequestStrategy):
    @staticmethod
    def urlNumberOfPages(config: Configuration) -> str:
        return "https://api.github.com/repos/{}/{}/commits?page{0}&per_page=100".format(config.repositoryOwner, config.repositoryName)

    @staticmethod
    def urlRequestPerPage(config: Configuration, page: int) -> str:
        return "https://api.github.com/repos/{}/{}/commits?page={}&per_page=100".format(config.repositoryOwner, config.repositoryName, page)

    @staticmethod
    def urlCommitBySha(config: Configuration, sha: str):
        return "https://api.github.com/repos/{}/{}/commits/{}".format(config.repositoryOwner, config.repositoryName, sha)

    @staticmethod
    def urlRequestComments(config: Configuration, sha: str):
       return "" 
