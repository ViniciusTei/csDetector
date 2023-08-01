from datetime import datetime, timezone
from dateutil.parser import isoparse
from lib.extraction.github.githubRequestHelper import GithubRequestHelper
from lib.extraction.github.entitys.pullRequestEntity import PullRequestEntity

class PullRequestsExctractor(GithubRequestHelper):
    def __init__(self, pat) -> None:
        super().__init__()
        super().setToken(pat)

    def requestPR(self, repoName: str, repoOwner: str):
        responseList = self.requests(f'https://api.github.com/repos/{repoOwner}/{repoName}/pulls?state=all')
        if responseList:
            listOfPRs = []

            for resDict in responseList:
                data = resDict.json()
                for res in data:
                    createdAt = isoparse(res["created_at"])
                    closedAt = (
                        datetime.now(timezone.utc)
                        if res["closed_at"] is None
                        else isoparse(res["closed_at"])
                    )
                    pr = PullRequestEntity(
                            int(res['number']), 
                            createdAt, 
                            closedAt, 
                            self._getPRComments(res['comments_url']), 
                            self._getTotalCommitsCount(res['commits_url']), 
                            list()
                        )

                    listOfPRs.append(pr)

            return listOfPRs
        else:
           raise Exception('Could not fetch pull requests from repository!')

    def _getPRComments(self, commentsUrl) -> list[str]:
        comments = []
        commentsRes = self.requests(commentsUrl)

        if commentsRes == None:
            return comments

        for com in commentsRes:
            resList = com.json()
            for resDict in resList:
                comments.append(resDict['body'])
        
        return comments

    def _getTotalCommitsCount(self, commitsUrl) -> int:
        total = 0

        commitRes = self.requests(commitsUrl)

        if commitRes == None:
            return total

        for com in commitRes:
            resList = com.json()
            total += len(resList)

        return total

