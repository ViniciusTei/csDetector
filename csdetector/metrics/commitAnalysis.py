from datetime import datetime
from typing import List
from dateutil.relativedelta import relativedelta
from git import Commit
from pandas.core.dtypes.dtypes import pytz
from sentistrength import PySentiStr

from csdetector import Configuration
from csdetector.github.GitHubRequestHelper import GitHubRequestHelper

class CommitAnalysis():
    def __init__(self, senti: PySentiStr, commits: List[Commit], delta: relativedelta, config: Configuration):
        self._senti = senti
        self._commits = commits
        self._delta = delta
        self._config = config
        pass

    def extract(self):
        # split commits into batches
        batches = []
        batch = []
        startDate = None

        if self._config.startDate is not None:
            startDate = datetime.strptime(self._config.startDate, "%Y-%m-%d")
            startDate = startDate.replace(tzinfo=pytz.UTC)

        batchStartDate = None
        batchEndDate = None
        batchDates = []

        for commit in self._commits:
            if startDate is not None and commit.committed_datetime < startDate:
                continue

            if batchStartDate is None:
                batchStartDate = commit.committed_datetime
                batchEndDate = batchStartDate + self._delta

            elif commit.committed_datetime > batchEndDate:
                batches.append(batch)
                batch = []
                batchStartDate = commit.committed_datetime
                batchEndDate = batchStartDate + self._delta
                batchDates.append(batchStartDate)

            batch.append(commit)

        batches.append(batch)
        del batch

        authorInfoDict = {}
        daysActive = list()

        for idx, batch in enumerate(batches):
            batchStartDate = batchDates[idx]
            batchEndDate = batchStartDate + self._delta

            for commit in batch:
                author = commit.author.name
                if author not in authorInfoDict:
                    authorInfoDict[author] = {
                        "commits": 0,
                        "daysActive": 0,
                        "positive": 0,
                        "negative": 0,
                        "neutral": 0,
                        "total": 0,
                        "positiveRatio": 0,
                        "negativeRatio": 0,
                        "neutralRatio": 0,
                        "totalRatio": 0,
                        "social": 0,
                        "socialRatio": 0,
                        "smell": 0,
                        "smellRatio": 0
                    }

                authorInfoDict[author]["commits"] += 1
                authorInfoDict[author]["daysActive"] = (batchEndDate - batchStartDate).days

                # sentiment
                sentiment = self._senti.getSentiment(commit.message)
                authorInfoDict[author][sentiment] += 1
                authorInfoDict[author]["total"] += 1



        pass

    def _analysis(self, idx: int):
        authorInfoDict = {}
        timezoneInfoDict = {}
        experienceDays = 150

        startDate = None

        if self._config.startDate is not None:
            startDate = datetime.strptime(self._config.startDate, "%Y-%m-%d")
            startDate = startDate.replace(tzinfo=pytz.UTC)

        self._commits.sort(key=lambda x: x.committed_datetime, reverse=True)

        commitMessages = []
        lastDate = None
        firstDate = None
        realCommitCount = 0

        for commit in self._commits:
            if startDate is not None and startDate > commit.committed_datetime:
                continue

            if lastDate is None:
                lastDate = commit.committed_datetime

            firstDate = commit.committed_datetime
            realCommitCount = realCommitCount + 1

            author = GitHubRequestHelper.get_author_id(commit.author)
            timezone = commit.author_tz_offset
            time = commit.authored_datetime

            timezoneInfo = timezoneInfoDict.setdefault(timezone, dict(commitCount=0, authors=set()))
            timezoneInfo["authors"].add(author)

            if commit.message and commit.message.strip():
                commitMessages.append(commit.message)

            timezoneInfo["commitCount"] += 1

            authorInfo = authorInfoDict.setdefault(
                    author, 
                    dict(
                        commitCount=0, 
                        sponsoredCommitCount=0,
                        earliestCommitDate=time,
                        latestCommitDate=time,
                        sponsored=False,
                        activeDays=0,
                        experienced=False
                    )
                )

            authorInfo["commitCount"] += 1

            if time < authorInfo["earliestCommitDate"]:
                authorInfo["earliestCommitDate"] = time

            if not commit.author_tz_offset == 0 and time.hour >= 9 and time.hour <= 17:
                authorInfo["sponsoredCommitCount"] += 1

        # analyzing commit message sentiment
        sentimentScores = []
        commitMessagesSentimentsPositive = []
        commitMessagesSentimentsNegative = []





        pass
        
