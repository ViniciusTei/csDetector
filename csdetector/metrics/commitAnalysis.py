from datetime import datetime
from typing import List
from dateutil.relativedelta import relativedelta
from git import Commit
from pandas.core.dtypes.dtypes import pytz
from sentistrength import PySentiStr
import statistics 
import csv
import os

from csdetector import Configuration
from csdetector.github.GitHubRequestHelper import GitHubRequestHelper

def outputStatistics(idx: int, data, metric: str, outputDir: str):

    # validate
    if len(data) < 1:
        return

    # calculate and output
    stats = calculateStats(data)

    # output
    with open(os.path.join(outputDir, f"results_{idx}.csv"), "a", newline="") as f:
        w = csv.writer(f, delimiter=",")

        for key in stats:
            outputValue(w, metric, key, stats)

def calculateStats(data):

    stats = dict(
        count=len(data),
        mean=statistics.mean(data),
        stdev=statistics.stdev(data) if len(data) > 1 else None
    )

    return stats


def outputValue(w, metric: str, name: str, dict: dict):
    value = dict[name]
    name = "{0}_{1}".format(metric, name)
    w.writerow([name, value])
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
            batchAuthorInfoDict, batchDaysActive = self._analysis(idx)

            authorInfoDict.update(batchAuthorInfoDict)
            daysActive.append(batchDaysActive)

            
        return batchDates, authorInfoDict, daysActive

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

        if len(commitMessages) > 0:
            sentimentScores = self._senti.getSentiment(commitMessages)
            commitMessagesSentimentsPositive = list(
                result for result in filter(lambda value: value >=1, sentimentScores)
            )

            commitMessagesSentimentsNegative = list(
                result for result in filter(lambda v: v <= -1, sentimentScores)
            )

        sponsoredAuthorCount = 0
        for login, author in authorInfoDict.items():

            # check if sponsored
            commitCount = int(author["commitCount"])
            sponsoredCommitCount = int(author["sponsoredCommitCount"])
            diff = sponsoredCommitCount / commitCount
            if diff >= 0.95:
                author["sponsored"] = True
                sponsoredAuthorCount += 1

            # calculate active days
            earliestDate = author["earliestCommitDate"]
            latestDate = author["latestCommitDate"]
            activeDays = (latestDate - earliestDate).days + 1
            author["activeDays"] = activeDays

            # check if experienced
            if activeDays >= experienceDays:
                author["experienced"] = True

        # calculate percentage sponsored authors
        percentageSponsoredAuthors = sponsoredAuthorCount / len([*authorInfoDict])

        # calculate active project days
        firstCommitDate = None
        lastCommitDate = None
        if firstDate is not None:
            firstCommitDate = datetime.fromtimestamp(firstDate)
        if lastDate is not None:
            lastCommitDate = datetime.fromtimestamp(lastDate)
        daysActive = 0
        if lastCommitDate is not None:
            daysActive = (lastCommitDate - firstCommitDate).days

        # TODO: store csv statisct in memory
        # TODO: create helper classes to do it
        with open(
            os.path.join(self._config.metricsPath, f"authorDaysOnProject_{idx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["Author", "# of Days"])
            for login, author in authorInfoDict.items():
                w.writerow([login, author["activeDays"]])

        # output commits per author
        with open(
            os.path.join(self._config.metricsPath, f"commitsPerAuthor_{idx}.csv"), "a", newline=""
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["Author", "Commit Count"])
            for login, author in authorInfoDict.items():
                w.writerow([login, author["commitCount"]])

        # output timezones
        with open(
            os.path.join(self._config.metricsPath, f"timezones_{idx}.csv"), "a", newline=""
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["Timezone Offset", "Author Count", "Commit Count"])
            for key, timezone in timezoneInfoDict.items():
                w.writerow([key, len(timezone["authors"]), timezone["commitCount"]])

        # output results
        with open(
            os.path.join(self._config.resultsPath, f"results_{idx}.csv"), "a", newline=""
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["CommitCount", realCommitCount])
            w.writerow(["DaysActive", daysActive])
            w.writerow(["FirstCommitDate", "{:%Y-%m-%d}".format(firstCommitDate)])
            w.writerow(["LastCommitDate", "{:%Y-%m-%d}".format(lastCommitDate)])
            w.writerow(["AuthorCount", len([*authorInfoDict])])
            w.writerow(["SponsoredAuthorCount", sponsoredAuthorCount])
            w.writerow(["PercentageSponsoredAuthors", percentageSponsoredAuthors])
            w.writerow(["TimezoneCount", len([*timezoneInfoDict])])

        outputStatistics(
            idx,
            [author["activeDays"] for login, author in authorInfoDict.items()],
            "AuthorActiveDays",
            self._config.resultsPath,
        )

        outputStatistics(
            idx,
            [author["commitCount"] for login, author in authorInfoDict.items()],
            "AuthorCommitCount",
            self._config.resultsPath,
        )

        outputStatistics(
            idx,
            [len(timezone["authors"]) for key, timezone in timezoneInfoDict.items()],
            "TimezoneAuthorCount",
            self._config.resultsPath,
        )

        outputStatistics(
            idx,
            [timezone["commitCount"] for key, timezone in timezoneInfoDict.items()],
            "TimezoneCommitCount",
            self._config.resultsPath,
        )

        outputStatistics(
            idx,
            sentimentScores,
            "CommitMessageSentiment",
            self._config.resultsPath,
        )

        outputStatistics(
            idx,
            commitMessagesSentimentsPositive,
            "CommitMessageSentimentsPositive",
            self._config.resultsPath,
        )

        outputStatistics(
            idx,
            commitMessagesSentimentsNegative,
            "CommitMessageSentimentsNegative",
            self._config.resultsPath,
        )

        return authorInfoDict, daysActive
        
