import csv
import os
from datetime import datetime
from dateutil.parser import isoparse
import logging
from typing import List
from dateutil.relativedelta import relativedelta
from git import Commit

from csdetector import Configuration
from csdetector.entities.Release import Release
from csdetector.github.GitHubRequestController import GitHubRequestController
from csdetector.github.GitHubRequestReleases import GitHubRequestReleases
from csdetector.utils.statistics import outputStatistics

class ReleaseAnalysis:
    def __init__(self, config: Configuration, request: GitHubRequestController) -> None:
        self._config = config
        self._request = request
        self._request.setStrategy(strategy=GitHubRequestReleases)
        pass

    def _releaseRequest(self, delta: relativedelta, batchDates: List[datetime]):
        pages = self._request.numberOfPages(self._config) 

        # prepare batches
        batches = []
        batch = None
        batchStartDate = None
        batchEndDate = None
        for page in range(1, pages + 1):
            logging.info("Querying page {}".format(page))
            response = self._request.requestPerPage(self._config, page) 

            if response is not None:
                requestData = response.json()

                for data in requestData:
                    createdAt = isoparse(data["created_at"])

                    if batchEndDate == None or (
                        createdAt > batchEndDate and len(batches) < len(batchDates) - 1
                    ):

                        if batch != None:
                            batches.append(batch)

                        batchStartDate = batchDates[len(batches)]
                        batchEndDate = batchStartDate + delta

                        batch = {"releaseCount": 0, "releases": []}

                    batch["releaseCount"] += 1
                    batch["releases"].append(Release(data["name"], createdAt, data["author"]["login"]))

        if batch != None:
            batches.append(batch)

        return batches

    def extract(self, allCommits: List[Commit], delta: relativedelta, batchDates: List[datetime]):
        # sort commits by ascending commit date
        allCommits.sort(key=lambda c: c.committed_datetime)

        logging.info("Querying releases")
        batches = self._releaseRequest(delta, batchDates)

        for batchIdx, batch in enumerate(batches):

            releases = batch["releases"]
            releaseAuthors = set()
            releaseCommitsCount = {}

            for i, release in enumerate(releases):
                releaseCommits = list()
                releaseDate = release.createdAt

                # try add author to set
                releaseAuthors.add(release.author)

                if i == 0:

                    # this is the first release, get all commits prior to release created date
                    for commit in allCommits:
                        if commit.committed_datetime < releaseDate:
                            releaseCommits.append(commit)
                        else:
                            break

                else:

                    # get in-between commit count
                    prevReleaseDate = releases[i - 1].createdAt
                    for commit in allCommits:
                        if (
                            commit.committed_datetime >= prevReleaseDate
                            and commit.committed_datetime < releaseDate
                        ):
                            releaseCommits.append(commit)
                        else:
                            break

                # remove all counted commits from list to improve iteration speed
                allCommits = allCommits[len(releaseCommits) :]

                # calculate authors per release
                commitAuthors = set(commit.author.email for commit in releaseCommits)

                # add results
                releaseCommitsCount[release.name] = dict(
                    date=release.createdAt,
                    authorsCount=len(commitAuthors),
                    commitsCount=len(releaseCommits),
                )

            # sort releases by date ascending
            releaseCommitsCount = {
                key: value
                for key, value in sorted(
                    releaseCommitsCount.items(), key=lambda r: r[1]["date"]
                )
            }

            logging.info("Writing results")
            with open(
                os.path.join(self._config.resultsPath, f"results_{batchIdx}.csv"), "a", newline=""
            ) as f:
                w = csv.writer(f, delimiter=",")
                w.writerow(["NumberReleases", batch["releaseCount"]])
                w.writerow(["NumberReleaseAuthors", len(releaseAuthors)])

            with open(
                os.path.join(self._config.metricsPath, f"releases_{batchIdx}.csv"),
                "a",
                newline="",
            ) as f:
                w = csv.writer(f, delimiter=",")
                w.writerow(["Release", "Date", "Author Count", "Commit Count"])
                for key, value in releaseCommitsCount.items():
                    w.writerow(
                        [
                            key,
                            value["date"].isoformat(),
                            value["authorsCount"],
                            value["commitsCount"],
                        ]
                    )

            outputStatistics(
                batchIdx,
                [value["authorsCount"] for key, value in releaseCommitsCount.items()],
                "ReleaseAuthorCount",
                self._config.resultsPath,
            )

            outputStatistics(
                batchIdx,
                [value["commitsCount"] for key, value in releaseCommitsCount.items()],
                "ReleaseCommitCount",
                self._config.resultsPath,
            )
