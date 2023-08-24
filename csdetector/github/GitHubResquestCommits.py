from csdetector import Configuration
from csdetector.github.GitHubRequestStrategy import GitHubRequestStrategy

class GitHubRequestCommits(GitHubRequestStrategy):
    @staticmethod
    def requestUrl(config: Configuration, sha) -> str:
        if sha is not None:
            return "https://api.github.com/repos/{}/{}/commits/{}".format(config.repositoryOwner, config.repositoryName, sha)
        else:
            return "https://api.github.com/repos/{}/{}/commits".format(config.repositoryOwner, config.repositoryName)
